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

_SETUP_STEPS = [
    {
        "step": 1,
        "title": "Google Cloud Console",
        "detail": (
            "console.cloud.google.com → новый проект (Genesis-Engine) → "
            "APIs & Services → Library → Places API → Enable."
        ),
        "url": "https://console.cloud.google.com/apis/library/places-backend.googleapis.com",
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
            "Файл dashboard/backend/.env.local — строка "
            "GOOGLE_PLACES_API_KEY=ваш_ключ (без кавычек)."
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
            "Engine → Локальные услуги → город (Berlin, Hamburg…) → "
            "«Поиск целей» или «DE · до 1000 URL»."
        ),
    },
]


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
            "env_var": "GOOGLE_PLACES_API_KEY",
            "primary_config_file": "dashboard/backend/.env.local",
            "config_files_found": existing_files,
            "setup_steps": _SETUP_STEPS,
            "free_tier_note": (
                "Google Places даёт бесплатный месячный лимит — для старта в Германии "
                "вы не выйдете за пределы free tier при обычном CEO-пути."
            ),
            "security_note": (
                "В Google Cloud → Credentials → API Key → Application restrictions: "
                "IP addresses (ваш IP или 127.0.0.1 для локального Genesis)."
            ),
            "usage": {
                "scan_mode": "Локальные услуги + город → Поиск целей",
                "network_scan": "DE · до 1000 URL — массовый обход городов Германии",
                "global_spider": "Дополняет seed URL; Places усиливает охват",
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
                status = str(payload.get("status") or "").strip()
                if status and status not in ("OK", "ZERO_RESULTS"):
                    message = str(payload.get("error_message") or status).strip()
                    raise RuntimeError(f"places_textsearch_status:{message}")
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
        status = str(data.get("status") or "").strip()
        if status and status not in ("OK",):
            return ""
        result = data.get("result") if isinstance(data.get("result"), dict) else {}
        website = str((result or {}).get("website") or "").strip()
        return website

