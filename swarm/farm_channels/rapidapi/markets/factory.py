"""Global API factory — activate markets only with verified datasets."""

from __future__ import annotations

from typing import Any

from swarm.farm_channels.rapidapi.markets.data_sources import commercial_use_ok, get_source
from swarm.farm_channels.rapidapi.markets.registry import get_market, list_markets, registry


def register_market(country_code: str) -> dict[str, Any]:
    """
    Return factory plan for a country. Does NOT invent data or flip LIVE.
    LIVE requires an attached commercial-ok source in the registry overrides.
    """
    row = get_market(country_code)
    if not row:
        return {"ok": False, "error": "unknown_country", "country": country_code}
    src_id = str(row.get("data_source") or "")
    source = get_source(src_id) if src_id else None
    live = row.get("status") == "LIVE" and commercial_use_ok(src_id) if src_id else False
    return {
        "ok": True,
        "country": row["country_code"],
        "name": row["country_name"],
        "status": row["status"],
        "live_endpoints_allowed": bool(live),
        "source": source,
        "routes": _planned_routes(row["country_code"], live=bool(live)),
        "note": (
            "LIVE endpoints serve real datasets only. "
            "PLANNED/READY markets return market_not_live — never fake cities."
        ),
    }


def _planned_routes(cc: str, *, live: bool) -> list[dict[str, Any]]:
    base = f"/v1/{cc.lower()}"
    return [
        {
            "method": "GET",
            "path": f"{base}/postal/{{postal_code}}",
            "enabled": live,
            "product": "global-postal-location",
        },
        {
            "method": "GET",
            "path": f"{base}/city/{{city}}",
            "enabled": False,
            "product": "global-city-region",
            "note": "activate when city dataset exists",
        },
    ]


def market_capabilities_matrix(*, wave_only: bool = True) -> list[dict[str, Any]]:
    rows = list_markets(wave_only=wave_only)
    out: list[dict[str, Any]] = []
    for r in rows:
        caps = r.get("capabilities") or {}
        out.append(
            {
                "country": r["country_code"],
                "name": r["country_name"],
                "postal": bool(caps.get("postal")),
                "city": bool(caps.get("city")),
                "address": bool(caps.get("address")),
                "phone": bool(caps.get("phone")),
                "vat": bool(caps.get("vat")),
                "status": r["status"],
                "commercial_wave": r.get("commercial_wave") or 0,
            }
        )
    return out


def products_catalog() -> list[dict[str, Any]]:
    """Commercial RapidAPI product shells — not claimed LIVE per country."""
    cov = registry().coverage()
    return [
        {
            "id": "global-postal-location",
            "name": "Global Postal & Location API",
            "live_countries": cov.get("live", 0),
            "status": "LIVE" if cov.get("live") else "PLANNED",
            "discovery": {
                "category": "location",
                "markets": ["Germany", "Europe", "DACH", "Global"],
                "use_case": "postal_code_lookup",
            },
        },
        {
            "id": "global-address",
            "name": "Global Address API",
            "live_countries": 0,
            "status": "PLANNED",
            "discovery": {"category": "address", "markets": ["Global"], "use_case": "parse_normalize"},
        },
        {
            "id": "global-phone",
            "name": "Global Phone Formatter API",
            "live_countries": 0,
            "status": "PLANNED",
            "note": "format/validate only — no owner lookup",
            "discovery": {"category": "phone", "markets": ["Global"], "use_case": "format_validate"},
        },
        {
            "id": "global-tax-id-format",
            "name": "Global Tax/VAT Format API",
            "live_countries": 0,
            "status": "PLANNED",
            "note": "format_valid ≠ official_verified",
            "discovery": {"category": "tax", "markets": ["EU", "Global"], "use_case": "vat_format"},
        },
        {
            "id": "global-country-data",
            "name": "Global Country Data API",
            "live_countries": cov.get("countries_total", 0),
            "status": "READY",
            "note": "metadata from ISO registry (no invented postal data)",
            "discovery": {
                "category": "country",
                "markets": ["Global", "Europe", "North America", "Asia"],
                "use_case": "country_metadata",
            },
        },
        {
            "id": "global-developer-utilities",
            "name": "Global Developer Utilities API",
            "live_countries": 0,
            "status": "PLANNED",
            "discovery": {"category": "utilities", "markets": ["Global"], "use_case": "dev_helpers"},
        },
    ]
