"""Google Places API (v1) client — lead research only.

Scope guard:
- No scraping
- No bypassing Google limits
- Rate-limited requests
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class PlacesLead:
    place_id: str
    name: str
    address: str
    website: str | None
    types: list[str]


class GooglePlacesService:
    def __init__(self) -> None:
        self._api_key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()

    def configured(self) -> bool:
        return bool(self._api_key)

    def search_text(
        self,
        *,
        query: str,
        language: str = "de",
        region: str = "de",
        limit: int = 20,
        throttle_ms: int = 250,
    ) -> list[PlacesLead]:
        """Text search + details (website). Returns up to `limit` leads.

        Uses Places Text Search + Place Details (website field).
        """
        if not self._api_key:
            raise ValueError("places_not_configured")
        q = query.strip()
        if not q:
            return []
        limit = max(1, min(int(limit), 50))

        leads: list[PlacesLead] = []
        next_page: str | None = None

        with httpx.Client(timeout=30.0) as client:
            while len(leads) < limit:
                params = {
                    "query": q,
                    "language": language,
                    "region": region,
                    "key": self._api_key,
                }
                if next_page:
                    params["pagetoken"] = next_page
                res = client.get(
                    "https://maps.googleapis.com/maps/api/place/textsearch/json",
                    params=params,
                )
                if res.status_code >= 400:
                    raise RuntimeError(f"places_textsearch_error:{res.status_code}")
                payload = res.json()
                results = payload.get("results") or []
                for r in results:
                    if len(leads) >= limit:
                        break
                    place_id = str(r.get("place_id") or "").strip()
                    if not place_id:
                        continue
                    name = str(r.get("name") or "").strip()
                    address = str(r.get("formatted_address") or r.get("vicinity") or "").strip()
                    types = [str(t) for t in (r.get("types") or []) if str(t).strip()]

                    website = self._fetch_website(client=client, place_id=place_id, throttle_ms=throttle_ms)
                    leads.append(
                        PlacesLead(
                            place_id=place_id,
                            name=name,
                            address=address,
                            website=website or None,
                            types=types,
                        )
                    )
                next_page = payload.get("next_page_token")
                if not next_page:
                    break
                # Google requires a short delay before token becomes valid.
                time.sleep(max(0.2, throttle_ms / 1000.0))

        return leads

    def _fetch_website(self, *, client: httpx.Client, place_id: str, throttle_ms: int) -> str:
        time.sleep(max(0.05, throttle_ms / 1000.0))
        params = {
            "place_id": place_id,
            "fields": "website",
            "key": self._api_key,
        }
        res = client.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params=params,
        )
        if res.status_code >= 400:
            return ""
        data: dict[str, Any] = res.json() if res.content else {}
        result = data.get("result") if isinstance(data.get("result"), dict) else {}
        website = str((result or {}).get("website") or "").strip()
        return website

