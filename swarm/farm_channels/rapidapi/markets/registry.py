"""GlobalMarketRegistry — ISO markets map; LIVE only with verified datasets."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from swarm.farm_channels.rapidapi.markets.iso3166_data import ISO3166_ALPHA2

MARKET_STATUS = (
    "PLANNED",
    "RESEARCH",
    "DATA_AVAILABLE",
    "READY",
    "LIVE",
    "BLOCKED",
)

# First commercial wave (CEO directive) — still PLANNED until datasets exist.
_COMMERCIAL_WAVE: tuple[str, ...] = (
    "DE",
    "AT",
    "CH",
    "FR",
    "NL",
    "BE",
    "GB",
    "US",
    "CA",
    "AU",
    "ES",
    "IT",
    "PL",
)

# Region hints (coarse, for catalog / RapidAPI discovery metadata).
_REGION_HINTS: dict[str, str] = {
    "DE": "Europe",
    "AT": "Europe",
    "CH": "Europe",
    "FR": "Europe",
    "NL": "Europe",
    "BE": "Europe",
    "LU": "Europe",
    "IT": "Europe",
    "ES": "Europe",
    "PT": "Europe",
    "IE": "Europe",
    "GB": "Europe",
    "DK": "Europe",
    "SE": "Europe",
    "NO": "Europe",
    "FI": "Europe",
    "PL": "Europe",
    "CZ": "Europe",
    "US": "North America",
    "CA": "North America",
    "MX": "North America",
    "BR": "South America",
    "AR": "South America",
    "AU": "Oceania",
    "NZ": "Oceania",
    "JP": "Asia",
    "KR": "Asia",
    "CN": "Asia",
    "IN": "Asia",
    "SG": "Asia",
    "AE": "Middle East",
    "SA": "Middle East",
    "ZA": "Africa",
    "TR": "Europe",
    "IL": "Middle East",
}

# Only DE has an honest in-repo sample today (not claimed as full national coverage).
_LIVE_OVERRIDES: dict[str, dict[str, Any]] = {
    "DE": {
        "status": "LIVE",
        "language": "de",
        "currency": "EUR",
        "timezone": "Europe/Berlin",
        "postal_system": "PLZ",
        "address_system": "DE",
        "phone_system": "DE_E164",
        "vat_system": "DE_UStID",
        "available_datasets": ["de_plz_sample_v1"],
        "data_source": "virtus_sample_de_plz",
        "license": "internal_sample",
        "commercial_use_allowed": True,
        "coverage": "sample_major_cities_only",
        "capabilities": {
            "postal": True,
            "city": True,
            "address": False,
            "phone": False,
            "vat": False,
        },
    },
}


def _blank_market(code: str, name: str) -> dict[str, Any]:
    wave = _COMMERCIAL_WAVE.index(code) + 1 if code in _COMMERCIAL_WAVE else 0
    return {
        "country_code": code,
        "country_name": name,
        "region": _REGION_HINTS.get(code, "World"),
        "language": "",
        "currency": "",
        "timezone": "",
        "postal_system": "unknown",
        "address_system": "unknown",
        "phone_system": "unknown",
        "vat_system": "unknown",
        "available_datasets": [],
        "data_source": "",
        "license": "",
        "commercial_use_allowed": False,
        "coverage": "none",
        "status": "PLANNED",
        "commercial_wave": wave,
        "capabilities": {
            "postal": False,
            "city": False,
            "address": False,
            "phone": False,
            "vat": False,
        },
    }


class GlobalMarketRegistry:
    """Singleton-style registry built at import from ISO map + LIVE overrides."""

    def __init__(self) -> None:
        self._markets: dict[str, dict[str, Any]] = {}
        for code, name in ISO3166_ALPHA2:
            row = _blank_market(code, name)
            if code in _LIVE_OVERRIDES:
                row.update(_LIVE_OVERRIDES[code])
            self._markets[code] = row

    def get(self, country_code: str) -> dict[str, Any] | None:
        cc = (country_code or "").strip().upper()
        row = self._markets.get(cc)
        return deepcopy(row) if row else None

    def list(
        self,
        *,
        status: str | None = None,
        wave_only: bool = False,
    ) -> list[dict[str, Any]]:
        rows = list(self._markets.values())
        if status:
            st = status.strip().upper()
            rows = [r for r in rows if r.get("status") == st]
        if wave_only:
            rows = [r for r in rows if int(r.get("commercial_wave") or 0) > 0]
        rows.sort(
            key=lambda r: (
                0 if r.get("status") == "LIVE" else 1,
                int(r.get("commercial_wave") or 99) or 99,
                str(r.get("country_code") or ""),
            )
        )
        return [deepcopy(r) for r in rows]

    def is_live(self, country_code: str) -> bool:
        row = self.get(country_code)
        return bool(row and row.get("status") == "LIVE")

    def coverage(self) -> dict[str, Any]:
        counts: dict[str, int] = {s: 0 for s in MARKET_STATUS}
        for row in self._markets.values():
            st = str(row.get("status") or "PLANNED")
            counts[st] = counts.get(st, 0) + 1
        return {
            "countries_total": len(self._markets),
            "by_status": counts,
            "live": counts.get("LIVE", 0),
            "ready": counts.get("READY", 0),
            "data_available": counts.get("DATA_AVAILABLE", 0),
            "planned": counts.get("PLANNED", 0),
            "research": counts.get("RESEARCH", 0),
            "blocked": counts.get("BLOCKED", 0),
            "commercial_wave": list(_COMMERCIAL_WAVE),
            "honesty_rule": (
                "LIVE only with verified dataset + commercial_use_allowed. "
                "No invented postal/city data."
            ),
        }


_REGISTRY = GlobalMarketRegistry()


def get_market(country_code: str) -> dict[str, Any] | None:
    return _REGISTRY.get(country_code)


def list_markets(
    *,
    status: str | None = None,
    wave_only: bool = False,
) -> list[dict[str, Any]]:
    return _REGISTRY.list(status=status, wave_only=wave_only)


def coverage_summary() -> dict[str, Any]:
    return _REGISTRY.coverage()


def registry() -> GlobalMarketRegistry:
    return _REGISTRY
