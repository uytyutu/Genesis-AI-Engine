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
from pathlib import Path
from typing import Any

import httpx

from app.config import env_config_file, get_api_key

_SETUP_STEPS = [
    {
        "step": 1,
        "title": "Google Cloud Console — Places API (New)",
        "detail": (
            "console.cloud.google.com → APIs & Services → Library → "
            "«Places API (New)» → Enable. Legacy Place Text Search не используется."
        ),
        "url": "https://console.cloud.google.com/apis/library/places.googleapis.com",
    },
    {
        "step": 2,
        "title": "Создать API Key",
        "detail": "APIs & Services → Credentials → Create Credentials → API Key → скопировать ключ.",
        "url": "https://console.cloud.google.com/apis/credentials",
    },
    {
        "step": 3,
        "title": "Вставить в Genesis",
        "detail": (
            "dashboard/backend/.env.local — GOOGLE_API_KEY=AIza… "
            "или GOOGLE_PLACES_API_KEY=… (без кавычек). Старый невалидный ключ удалите."
        ),
    },
    {
        "step": 4,
        "title": "Перезапустить Genesis.exe",
        "detail": "Остановить → Запустить снова, чтобы backend подхватил ключ.",
    },
    {
        "step": 5,
        "title": "Запустить автопилот",
        "detail": (
            "Spider / Acquisition → DE hubs (Berlin, Köln…) → "
            "появятся Handwerker / IT с сайтами."
        ),
    },
]

_PLACES_NEW_SEARCH = "https://places.googleapis.com/v1/places:searchText"
_PLACES_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,places.websiteUri,places.types"
)


@dataclass
class PlacesLead:
    place_id: str
    name: str
    address: str
    website: str | None
    types: list[str]


def _resolve_places_api_key() -> tuple[str, str]:
    """Load Places key from .env.local.

    Prefer GOOGLE_API_KEY when it looks like a standard Cloud key (AIza…),
    because a stale GOOGLE_PLACES_API_KEY often shadows the new working key.
    Returns (key, env_var_name).
    """
    places = get_api_key("GOOGLE_PLACES_API_KEY")
    google = get_api_key("GOOGLE_API_KEY")
    if google.startswith("AIza"):
        return google, "GOOGLE_API_KEY"
    if places:
        return places, "GOOGLE_PLACES_API_KEY"
    if google:
        return google, "GOOGLE_API_KEY"
    return "", "none"


class GooglePlacesService:
    def __init__(self, api_key: str | None = None, *, use_env: bool = True) -> None:
        self._key_source = "injected"
        if api_key is not None:
            self._api_key = api_key.strip()
        elif use_env:
            self._api_key, self._key_source = _resolve_places_api_key()
        else:
            self._api_key = ""
            self._key_source = "none"

    def configured(self) -> bool:
        return bool(self._api_key)

    def key_source(self) -> str:
        """Which env var supplied the key (never returns the secret)."""
        return self._key_source

    def setup_status(self) -> dict[str, Any]:
        """CEO onboarding — where to put GOOGLE_PLACES_API_KEY for Germany autopilot."""
        backend_dir = Path(__file__).resolve().parents[2]
        repo_root = backend_dir.parent.parent
        config_paths = [
            backend_dir / ".env.local",
            backend_dir / ".env",
            backend_dir.parent / ".env",
        ]
        existing_files = [
            str(p.relative_to(repo_root)).replace("\\", "/")
            for p in config_paths
            if p.is_file()
        ]
        configured = self.configured()
        return {
            "configured": configured,
            "autopilot_ready": configured,
            "env_var": self.key_source() if configured else "GOOGLE_PLACES_API_KEY|GOOGLE_API_KEY",
            "primary_config_file": env_config_file(),
            "config_files_found": existing_files,
            "setup_steps": _SETUP_STEPS,
            "free_tier_note": (
                "Google Places даёт бесплатный месячный лимит — для старта по всему миру "
                "обычно хватает бесплатного тарифа."
            ),
            "security_note": (
                "Credentials → API Key → API restrictions: разрешите «Places API (New)». "
                "Если стоит Restrict key и нет Places — будет Requests … are blocked."
            ),
            "usage": {
                "scan_mode": "Город + ниша → Поиск в одном городе",
                "network_scan": "Авто-поиск — до 1000 сайтов по всему миру",
                "global_spider": "Дополняет поиск по технологиям и проблемам сайтов",
            },
            "status_label": "Автопилот готов" if configured else "Нужен GOOGLE_PLACES_API_KEY",
        }

    def search_text(
        self,
        *,
        query: str,
        language: str = "de",
        region: str = "de",
        limit: int = 20,
        throttle_ms: int = 250,
        lat: float | None = None,
        lng: float | None = None,
        radius_m: int = 25000,
    ) -> list[PlacesLead]:
        """Text search via Places API (New). Returns up to `limit` leads.

        Optional lat/lng biases results to a city radius (e.g. Köln).
        """
        if not self._api_key:
            raise ValueError("places_not_configured")
        q = query.strip()
        if not q:
            return []
        limit = max(1, min(int(limit), 50))

        body: dict[str, Any] = {
            "textQuery": q,
            "languageCode": (language or "de").split("-")[0],
            "regionCode": (region or "de").upper()[:2],
            "maxResultCount": min(limit, 20),
        }
        if lat is not None and lng is not None:
            body["locationBias"] = {
                "circle": {
                    "center": {"latitude": float(lat), "longitude": float(lng)},
                    "radius": float(max(1000, min(int(radius_m), 50000))),
                }
            }

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": _PLACES_FIELD_MASK,
        }

        with httpx.Client(timeout=30.0) as client:
            if throttle_ms > 0:
                time.sleep(min(throttle_ms / 1000.0, 1.0))
            res = client.post(_PLACES_NEW_SEARCH, json=body, headers=headers)
            if res.status_code >= 400:
                detail = ""
                try:
                    detail = str((res.json() or {}).get("error", {}).get("message") or res.text)[:220]
                except Exception:
                    detail = res.text[:220]
                raise RuntimeError(f"places_textsearch_status:{detail or res.status_code}")

            payload = res.json() if res.content else {}
            places = payload.get("places") or []
            leads: list[PlacesLead] = []
            for r in places:
                if len(leads) >= limit:
                    break
                place_id = str(r.get("id") or "").strip()
                if place_id.startswith("places/"):
                    place_id = place_id.split("/", 1)[-1]
                display = r.get("displayName") if isinstance(r.get("displayName"), dict) else {}
                name = str(display.get("text") or "").strip()
                address = str(r.get("formattedAddress") or "").strip()
                website = str(r.get("websiteUri") or "").strip() or None
                types = [str(t) for t in (r.get("types") or []) if str(t).strip()]
                if not place_id and not name:
                    continue
                leads.append(
                    PlacesLead(
                        place_id=place_id or name,
                        name=name or place_id,
                        address=address,
                        website=website,
                        types=types,
                    )
                )
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
        status = str(data.get("status") or "").strip()
        if status and status not in ("OK",):
            return ""
        result = data.get("result") if isinstance(data.get("result"), dict) else {}
        website = str((result or {}).get("website") or "").strip()
        return website

