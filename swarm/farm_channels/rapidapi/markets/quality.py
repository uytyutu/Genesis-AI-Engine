"""Market quality scores — honest zeros when no verified dataset."""

from __future__ import annotations

from typing import Any

from swarm.farm_channels.rapidapi.markets.data_sources import commercial_use_ok, get_source
from swarm.farm_channels.rapidapi.markets.registry import get_market, list_markets


def market_quality_score(country_code: str) -> dict[str, Any]:
    """
    Score 0–100 from real registry/source fields only.
    PLANNED markets without a source stay near 0 — never inflated.
    """
    row = get_market(country_code)
    if not row:
        return {
            "country": (country_code or "").upper(),
            "error": "unknown_country",
            "market_score": 0,
        }
    src_id = str(row.get("data_source") or "")
    source = get_source(src_id) if src_id else None
    status = str(row.get("status") or "PLANNED")

    coverage_score = 0
    data_quality_score = 0
    freshness_score = 0
    license_score = 0
    commercial_score = 0

    if source and commercial_use_ok(src_id):
        license_score = 80
        commercial_score = 70
        cov = str(source.get("coverage") or row.get("coverage") or "")
        if "sample" in cov:
            coverage_score = 25
            data_quality_score = 40
            freshness_score = 50
        elif cov and cov != "none":
            coverage_score = 60
            data_quality_score = 60
            freshness_score = 60
        if status == "LIVE":
            commercial_score = 85
        elif status == "READY":
            commercial_score = 75
    elif status == "BLOCKED":
        license_score = 0
        commercial_score = 0

    # Weighted blend — sample LIVE stays modest (not "perfect national API")
    market_score = int(
        round(
            coverage_score * 0.25
            + data_quality_score * 0.25
            + freshness_score * 0.15
            + license_score * 0.2
            + commercial_score * 0.15
        )
    )
    return {
        "country": row["country_code"],
        "status": status,
        "coverage_score": coverage_score,
        "data_quality_score": data_quality_score,
        "freshness_score": freshness_score,
        "license_score": license_score,
        "commercial_score": commercial_score,
        "market_score": market_score,
        "note": (
            "Scores reflect verified datasets only. "
            "Sample coverage is intentionally modest."
        ),
    }


def wave_quality_table() -> list[dict[str, Any]]:
    out = []
    for row in list_markets(wave_only=True):
        out.append(market_quality_score(str(row["country_code"])))
    return out
