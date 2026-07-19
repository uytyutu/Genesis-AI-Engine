"""Nominatim geocode → OSM embed URL. Disabled unless GENESIS_CAP_NOMINATIM=1."""

from __future__ import annotations

from urllib.parse import quote_plus

from app.integration.external_capabilities.http_util import http_get_json, url_with_query
from app.integration.external_capabilities.models import AdapterResult
from app.integration.external_capabilities.registry import is_enabled

_NOMINATIM = "https://nominatim.openstreetmap.org/search"


def google_maps_embed(query: str) -> str:
    q = quote_plus(query.strip() or "Deutschland")
    return f"https://maps.google.com/maps?q={q}&z=14&output=embed"


def osm_embed(*, lat: float, lon: float, zoom: int = 15) -> str:
    # ~0.01 deg box around point
    d = 0.012
    west, east = lon - d, lon + d
    south, north = lat - d, lat + d
    bbox = f"{west}%2C{south}%2C{east}%2C{north}"
    marker = f"{lat}%2C{lon}"
    return (
        f"https://www.openstreetmap.org/export/embed.html?"
        f"bbox={bbox}&layer=mapnik&marker={marker}"
    )


def resolve_maps_embed(
    *,
    business_name: str,
    city: str,
    street: str = "",
    country: str = "Deutschland",
) -> AdapterResult:
    """Return OSM embed when capability enabled; else Google embed fallback."""
    query = " ".join(p for p in (business_name, street, city, country) if p).strip()
    fallback_url = google_maps_embed(query)

    if not is_enabled("nominatim"):
        return AdapterResult(
            ok=True,
            capability_id="nominatim",
            data={
                "embed_url": fallback_url,
                "provider": "google_maps_embed",
                "attribution": None,
            },
            used_fallback=True,
            source=None,
            error="capability_disabled",
        )

    url = url_with_query(
        _NOMINATIM,
        {
            "q": query,
            "format": "json",
            "limit": "1",
        },
    )
    data, err = http_get_json(url, timeout=4.0)
    if err or not isinstance(data, list) or not data:
        return AdapterResult(
            ok=True,
            capability_id="nominatim",
            data={
                "embed_url": fallback_url,
                "provider": "google_maps_embed",
                "attribution": None,
            },
            used_fallback=True,
            source=None,
            error=err or "no_results",
        )

    hit = data[0] if isinstance(data[0], dict) else {}
    try:
        lat = float(hit.get("lat"))
        lon = float(hit.get("lon"))
    except (TypeError, ValueError):
        return AdapterResult(
            ok=True,
            capability_id="nominatim",
            data={
                "embed_url": fallback_url,
                "provider": "google_maps_embed",
            },
            used_fallback=True,
            error="bad_coords",
        )

    embed = osm_embed(lat=lat, lon=lon)
    return AdapterResult(
        ok=True,
        capability_id="nominatim",
        data={
            "embed_url": embed,
            "provider": "openstreetmap",
            "lat": lat,
            "lon": lon,
            "display_name": str(hit.get("display_name") or "")[:200],
            "attribution": "© OpenStreetMap contributors",
            "query": query,
        },
        used_fallback=False,
        source="https://www.openstreetmap.org/copyright",
    )
