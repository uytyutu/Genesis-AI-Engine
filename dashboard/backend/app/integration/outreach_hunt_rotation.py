"""Round-robin Places hunt across enabled outreach markets (IP-safe pacing).

Each tick advances to the **next market** (not the next hub inside the same
country). Within a market, hubs × niches rotate on subsequent visits so every
enabled country gets work without long DE/US-only streaks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.integration.outreach_market_config import list_markets

_NICHES_BY_LANG: dict[str, list[str]] = {
    # Keep dental/auto/craft, add high-LTV professions so rotation is not ⅓ dentist.
    "de": [
        "Zahnarztpraxis",
        "Rechtsanwalt",
        "Photovoltaik Anbieter",
        "Steuerberater",
        "Architekturbüro",
        "Privatklinik",
        "Schönheitsklinik",
        "Finanzberater",
        "Immobilienmakler",
        "Maschinenbau Unternehmen",
        "Ingenieurbüro",
        "Kfz-Werkstatt",
        "Dachdecker",
        "Sanitär Notdienst",
    ],
    "en-us": [
        "dentist",
        "law firm",
        "solar panel installer",
        "accountant",
        "architect office",
        "private clinic",
        "cosmetic clinic",
        "financial advisor",
        "real estate agency",
        "manufacturing company",
        "engineering firm",
        "auto repair",
        "plumber",
    ],
    "en": [
        "dentist",
        "solicitor",
        "solar panel installer",
        "accountant",
        "architect",
        "private clinic",
        "cosmetic clinic",
        "financial advisor",
        "estate agent",
        "manufacturing company",
        "engineering consultancy",
        "auto repair",
        "plumber",
    ],
    "uk": [
        "стоматологія",
        "адвокат",
        "сонячні панелі",
        "бухгалтер",
        "архітектор",
        "приватна клініка",
        "косметологічна клініка",
        "фінансовий консультант",
        "агентство нерухомості",
        "виробниче підприємство",
        "інженерна компанія",
        "автосервіс",
        "сантехнік",
    ],
    "ru": [
        "стоматология",
        "юрист",
        "солнечные панели",
        "бухгалтер",
        "архитектор",
        "частная клиника",
        "косметологическая клиника",
        "финансовый консультант",
        "агентство недвижимости",
        "производственная компания",
        "инженерная компания",
        "автосервис",
        "сантехник",
    ],
    "ja": [
        "歯科医院",
        "法律事務所",
        "太陽光発電",
        "税理士",
        "建築設計事務所",
        "クリニック",
        "美容クリニック",
        "ファイナンシャルプランナー",
        "不動産会社",
        "製造業",
        "エンジニアリング",
        "自動車修理",
        "配管工事",
    ],
    "ko": [
        "치과",
        "법률사무소",
        "태양광",
        "세무사",
        "건축사무소",
        "클리닉",
        "피부과",
        "재무상담",
        "부동산",
        "제조업",
        "엔지니어링",
        "자동차정비",
        "배관",
    ],
}


_PLACES_LANG: dict[str, str] = {
    "de": "de",
    "en-us": "en",
    "en": "en",
    "uk": "uk",
    "ru": "ru",
    "ja": "ja",
    "ko": "ko",
}


def niches_for_language(language: str | None) -> list[str]:
    key = (language or "en-us").strip().lower()
    return list(_NICHES_BY_LANG.get(key) or _NICHES_BY_LANG["en-us"])


def places_language(language: str | None) -> str:
    key = (language or "en-us").strip().lower()
    return _PLACES_LANG.get(key) or "en"


def active_markets(
    *,
    paused_markets: dict[str, Any] | None = None,
    effective_cap_fn=None,
) -> list[dict[str, Any]]:
    paused = paused_markets or {}
    out: list[dict[str, Any]] = []
    for m in list_markets(enabled_only=True):
        code = str(m.get("code") or "").upper()
        if not code or paused.get(code):
            continue
        if effective_cap_fn is not None:
            try:
                if int(effective_cap_fn(code) or 0) <= 0:
                    continue
            except (TypeError, ValueError):
                continue
        out.append(m)
    return out


def build_hunt_slots(
    *,
    paused_markets: dict[str, Any] | None = None,
    effective_cap_fn=None,
) -> list[dict[str, Any]]:
    """Flatten enabled markets → hubs × niches (stable order; used for counts/tests)."""
    slots: list[dict[str, Any]] = []
    for m in active_markets(paused_markets=paused_markets, effective_cap_fn=effective_cap_fn):
        code = str(m.get("code") or "").upper()
        lang = str(m.get("language") or "en-us")
        niches = niches_for_language(lang)
        hubs = [str(h).strip() for h in (m.get("hubs") or []) if str(h).strip()] or [code]
        for hub in hubs:
            for niche in niches:
                slots.append(
                    {
                        "market": code,
                        "city": hub,
                        "query": niche,
                        "language": places_language(lang),
                        "market_language": lang,
                        "region": code.lower() if code != "GB" else "gb",
                        "flag": m.get("flag") or "",
                        "name_ru": m.get("name_ru") or code,
                    }
                )
    return slots


def _slot_for_market(m: dict[str, Any], *, hub_i: int, niche_i: int) -> dict[str, Any]:
    code = str(m.get("code") or "").upper()
    lang = str(m.get("language") or "en-us")
    niches = niches_for_language(lang)
    hubs = [str(h).strip() for h in (m.get("hubs") or []) if str(h).strip()] or [code]
    hub = hubs[hub_i % len(hubs)]
    niche = niches[niche_i % len(niches)]
    return {
        "market": code,
        "city": hub,
        "query": niche,
        "language": places_language(lang),
        "market_language": lang,
        "region": code.lower() if code != "GB" else "gb",
        "flag": m.get("flag") or "",
        "name_ru": m.get("name_ru") or code,
    }


class HuntRotationCursor:
    def __init__(self, memory_dir: Path | None) -> None:
        self._memory = memory_dir

    def _path(self) -> Path | None:
        if not self._memory:
            return None
        return Path(self._memory) / "outreach_hunt_cursor.json"

    def _load(self) -> dict[str, Any]:
        path = self._path()
        empty = {"market_index": 0, "within_market": {}}
        if not path or not path.is_file():
            return empty
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return empty
        if not isinstance(data, dict):
            return empty
        data.setdefault("market_index", 0)
        data.setdefault("within_market", {})
        # migrate legacy flat index → market_index
        if "index" in data and "market_index" not in data:
            data["market_index"] = int(data.get("index") or 0)
        return data

    def _save(self, data: dict[str, Any]) -> None:
        path = self._path()
        if not path:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def next_slot(
        self,
        *,
        paused_markets: dict[str, Any] | None = None,
        effective_cap_fn=None,
        market_override: str | None = None,
        city_override: str | None = None,
        query_override: str | None = None,
    ) -> dict[str, Any] | None:
        markets = active_markets(
            paused_markets=paused_markets,
            effective_cap_fn=effective_cap_fn,
        )
        if not markets:
            return None

        if market_override:
            code = market_override.strip().upper()
            m = next((x for x in markets if str(x.get("code") or "").upper() == code), None)
            if not m:
                return None
            lang = str(m.get("language") or "en-us")
            niches = niches_for_language(lang)
            hubs = [str(h).strip() for h in (m.get("hubs") or []) if str(h).strip()] or [code]
            city = (city_override or hubs[0]).strip()
            query = (query_override or niches[0]).strip()
            slot = _slot_for_market(m, hub_i=0, niche_i=0)
            slot["city"] = city
            slot["query"] = query
            return slot

        state = self._load()
        n = len(markets)
        mi = int(state.get("market_index") or 0) % n
        m = markets[mi]
        code = str(m.get("code") or "").upper()
        within = dict(state.get("within_market") or {})
        wm = dict(within.get(code) or {})
        hub_i = int(wm.get("hub_i") or 0)
        niche_i = int(wm.get("niche_i") or 0)
        slot = _slot_for_market(m, hub_i=hub_i, niche_i=niche_i)

        lang = str(m.get("language") or "en-us")
        niches = niches_for_language(lang)
        hubs = [str(h).strip() for h in (m.get("hubs") or []) if str(h).strip()] or [code]
        niche_i = (niche_i + 1) % max(1, len(niches))
        if niche_i == 0:
            hub_i = (hub_i + 1) % max(1, len(hubs))
        within[code] = {"hub_i": hub_i, "niche_i": niche_i}
        state["within_market"] = within
        state["market_index"] = (mi + 1) % n
        state["last"] = {
            "market": slot["market"],
            "city": slot["city"],
            "query": slot["query"],
        }
        self._save(state)
        slot["slot_index"] = mi
        slot["slots_total"] = n
        return slot
