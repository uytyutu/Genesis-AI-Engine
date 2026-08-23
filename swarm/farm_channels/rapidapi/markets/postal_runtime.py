"""Global postal runtime — LIVE markets only; no invented cities."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote

from swarm.farm_channels.rapidapi.markets.datasets.de_plz_sample import (
    DE_PLZ_SAMPLE,
    lookup_de_plz,
)
from swarm.farm_channels.rapidapi.markets.registry import get_market, list_markets
from swarm.farm_channels.rapidapi.markets.schemas import location_payload, market_not_live

_POSTAL_RE = re.compile(
    r"^/v1/(?P<cc>[a-z]{2})/postal/(?P<code>[A-Za-z0-9][A-Za-z0-9\- ]{1,12})$",
    re.I,
)
_CITY_RE = re.compile(r"^/v1/(?P<cc>[a-z]{2})/city/(?P<city>[^/]+)$", re.I)
_CITY_POSTAL_RE = re.compile(
    r"^/v1/(?P<cc>[a-z]{2})/city/(?P<city>[^/]+)/postal$",
    re.I,
)
_COUNTRY_SUB = re.compile(
    r"^/v1/countries/(?P<cc>[a-z]{2})/(?P<sub>regions|languages|currencies|timezone)$",
    re.I,
)


def _require_live(cc: str) -> tuple[dict[str, Any] | None, tuple[int, dict[str, Any]] | None]:
    market = get_market(cc)
    if not market:
        return None, (404, {"error": "unknown_country", "country": cc})
    if market.get("status") != "LIVE":
        return None, (
            403,
            market_not_live(cc, status=str(market.get("status") or "PLANNED")),
        )
    return market, None


def handle_global_postal(
    method: str,
    path: str,
    body: Any = None,
    query: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    query = query or {}
    if method == "GET" and path in ("/v1/countries", "/v1/markets"):
        rows = list_markets()
        return 200, {
            "count": len(rows),
            "countries": [
                {
                    "country": r["country_code"],
                    "name": r["country_name"],
                    "status": r["status"],
                    "region": r.get("region"),
                }
                for r in rows
            ],
            "note": "LIVE countries serve postal data; others are registry-only.",
        }

    m_sub = _COUNTRY_SUB.match(path)
    if method == "GET" and m_sub:
        return _country_sub(m_sub.group("cc").upper(), m_sub.group("sub").lower())

    m_one = re.match(r"^/v1/countries/([a-z]{2})$", path, re.I)
    if method == "GET" and m_one:
        row = get_market(m_one.group(1))
        if not row:
            return 404, {"error": "unknown_country"}
        return 200, row

    # POST validate / bulk — LIVE only; never invent
    m_validate = re.match(r"^/v1/([a-z]{2})/postal/validate$", path, re.I)
    if method == "POST" and m_validate:
        return _postal_validate(m_validate.group(1).upper(), body)

    m_bulk = re.match(r"^/v1/([a-z]{2})/postal/bulk$", path, re.I)
    if method == "POST" and m_bulk:
        return _postal_bulk(m_bulk.group(1).upper(), body)

    m_search = re.match(r"^/v1/([a-z]{2})/postal/search$", path, re.I)
    if method == "GET" and m_search:
        return _postal_search(m_search.group(1).upper(), query)

    # city/{city}/postal before city/{city}
    m_cp = _CITY_POSTAL_RE.match(path)
    if method == "GET" and m_cp:
        return _city_postals(m_cp.group("cc").upper(), unquote(m_cp.group("city")))

    m_city = _CITY_RE.match(path)
    if method == "GET" and m_city:
        return _city_lookup(m_city.group("cc").upper(), unquote(m_city.group("city")))

    m = _POSTAL_RE.match(path)
    if method == "GET" and m:
        cc = m.group("cc").upper()
        code = m.group("code").strip()
        _, err = _require_live(cc)
        if err:
            return err
        return _lookup_live(cc, code)

    return 404, {"error": "not_found", "path": path}


def _country_sub(cc: str, sub: str) -> tuple[int, dict[str, Any]]:
    row = get_market(cc)
    if not row:
        return 404, {"error": "unknown_country", "country": cc}
    if sub == "timezone":
        tz = str(row.get("timezone") or "")
        return 200, {
            "country": cc,
            "timezone": tz or None,
            "known": bool(tz),
            "note": "Empty until market metadata filled — not invented.",
        }
    if sub == "languages":
        lang = str(row.get("language") or "")
        return 200, {
            "country": cc,
            "languages": [lang] if lang else [],
            "note": "Registry language only; no invented locale list.",
        }
    if sub == "currencies":
        cur = str(row.get("currency") or "")
        return 200, {
            "country": cc,
            "currencies": [cur] if cur else [],
            "note": "No live FX rates. Metadata only when known.",
        }
    if sub == "regions":
        # Only expose regions we can derive from a LIVE local dataset
        if row.get("status") == "LIVE" and cc == "DE":
            regions = sorted({v["region"] for v in DE_PLZ_SAMPLE.values()})
            return 200, {
                "country": cc,
                "regions": regions,
                "count": len(regions),
                "coverage": "sample_major_cities_only",
            }
        return 200, {
            "country": cc,
            "regions": [],
            "count": 0,
            "status": row.get("status"),
            "note": "No verified region dataset for this market.",
        }
    return 404, {"error": "not_found", "sub": sub}


def _postal_search(cc: str, query: dict[str, str]) -> tuple[int, dict[str, Any]]:
    _, err = _require_live(cc)
    if err:
        return err
    q = (query.get("q") or query.get("query") or "").strip()
    if len(q) < 2:
        return 400, {"error": "validation", "detail": "q must be at least 2 characters"}
    if cc != "DE":
        return 501, {"error": "dataset_not_wired", "country": cc}
    needle = q.casefold()
    hits = []
    for plz, row in DE_PLZ_SAMPLE.items():
        if needle in plz or needle in row["city"].casefold() or needle in row["region"].casefold():
            hits.append(
                location_payload(
                    country="DE",
                    postal_code=plz,
                    locality=row["city"],
                    region=row["region"],
                    extra={"plz": plz, "city": row["city"]},
                )
            )
    return 200, {
        "country": "DE",
        "q": q,
        "count": len(hits),
        "results": hits,
        "coverage": "sample_major_cities_only",
    }


def _postal_validate(cc: str, body: Any) -> tuple[int, dict[str, Any]]:
    _, err = _require_live(cc)
    if err:
        return err
    if not isinstance(body, dict):
        return 400, {"error": "validation", "detail": "JSON body with postal_code required"}
    code = str(body.get("postal_code") or body.get("plz") or "").strip()
    if not code:
        return 400, {"error": "validation", "detail": "postal_code required"}
    status, payload = _lookup_live(cc, code)
    if status == 200:
        return 200, {
            "valid": True,
            "format_valid": True,
            "exists_in_dataset": True,
            "result": payload,
            "note": "exists_in_dataset reflects sample/live local data — not national cadastre claim",
        }
    return 200, {
        "valid": False,
        "format_valid": bool(re.match(r"^\d{4,5}$", code)) if cc == "DE" else None,
        "exists_in_dataset": False,
        "postal_code": code,
        "country": cc,
    }


def _postal_bulk(cc: str, body: Any) -> tuple[int, dict[str, Any]]:
    _, err = _require_live(cc)
    if err:
        return err
    codes: list[str] = []
    if isinstance(body, dict):
        raw = body.get("postal_codes") or body.get("codes") or body.get("plz") or []
        if isinstance(raw, list):
            codes = [str(x).strip() for x in raw if str(x).strip()]
    if not codes:
        return 400, {"error": "validation", "detail": "postal_codes: string[] required"}
    if len(codes) > 100:
        return 400, {"error": "validation", "detail": "max 100 codes per bulk request"}
    results = []
    for code in codes:
        st, payload = _lookup_live(cc, code)
        results.append({"postal_code": code, "ok": st == 200, "result": payload if st == 200 else None})
    return 200, {"country": cc, "count": len(results), "results": results}


def _city_lookup(cc: str, city: str) -> tuple[int, dict[str, Any]]:
    _, err = _require_live(cc)
    if err:
        return err
    if cc != "DE":
        return 501, {"error": "dataset_not_wired", "country": cc}
    needle = (city or "").strip().casefold()
    hits = [
        location_payload(
            country="DE",
            postal_code=plz,
            locality=row["city"],
            region=row["region"],
            extra={"plz": plz, "city": row["city"]},
        )
        for plz, row in DE_PLZ_SAMPLE.items()
        if row["city"].casefold() == needle
    ]
    if not hits:
        return 404, {
            "error": "city_not_found",
            "country": "DE",
            "locality": city,
            "note": "v1 sample dataset (major cities only)",
        }
    return 200, {
        "country": "DE",
        "locality": hits[0]["locality"],
        "region": hits[0]["region"],
        "postal_codes": [h["postal_code"] for h in hits],
        "count": len(hits),
    }


def _city_postals(cc: str, city: str) -> tuple[int, dict[str, Any]]:
    return _city_lookup(cc, city)


def _lookup_live(cc: str, code: str) -> tuple[int, dict[str, Any]]:
    if cc == "DE":
        row = lookup_de_plz(code)
        if not row:
            return 404, {
                "error": "postal_not_found",
                "country": "DE",
                "postal_code": code,
                "note": "v1 sample dataset (major cities only)",
            }
        payload = location_payload(
            country="DE",
            postal_code=row["postal_code"],
            locality=row["locality"],
            region=row["region"],
            extra={"plz": row["postal_code"], "city": row["locality"]},
        )
        return 200, payload
    return 501, {
        "error": "dataset_not_wired",
        "country": cc,
        "detail": "Market marked LIVE but no adapter loaded — fix registry.",
    }


def handle_de_plz_compat(
    method: str,
    path: str,
    body: Any = None,
    query: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Legacy /v1/de/plz/{code} used by published RapidAPI listing."""
    m = re.match(r"^/v1/de/plz/(\d{4,5})$", path)
    if method == "GET" and m:
        return _lookup_live("DE", m.group(1))
    if method == "GET" and path == "/v1/de/plz":
        return 400, {"error": "validation", "detail": "Use /v1/de/plz/{code}"}
    if path.lower().startswith("/v1/de/postal/") or path.lower().startswith("/v1/de/city/"):
        return handle_global_postal(method, path, body, query=query)
    if method == "POST" and path.lower() in (
        "/v1/de/postal/validate",
        "/v1/de/postal/bulk",
    ):
        return handle_global_postal(method, path, body, query=query)
    return 404, {"error": "not_found", "path": path}
