"""Common location schemas — country-agnostic field names."""

from __future__ import annotations

from typing import Any


def location_payload(
    *,
    country: str,
    postal_code: str,
    locality: str,
    region: str = "",
    administrative_area: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Canonical response for LIVE postal lookups."""
    out: dict[str, Any] = {
        "country": (country or "").upper(),
        "postal_code": str(postal_code or ""),
        "locality": locality or "",
        "region": region or "",
        "administrative_area": administrative_area or region or "",
    }
    if extra:
        out.update(extra)
    return out


def market_not_live(country: str, *, status: str = "PLANNED") -> dict[str, Any]:
    return {
        "error": "market_not_live",
        "country": (country or "").upper(),
        "status": status,
        "detail": (
            "Endpoint enabled only for LIVE markets with a verified commercial dataset. "
            "No invented city/postal data."
        ),
    }
