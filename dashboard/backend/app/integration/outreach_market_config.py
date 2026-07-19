"""Config-driven outreach markets — add a country = add JSON row, not code."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).resolve().parent / "outreach_markets.json"


@lru_cache(maxsize=1)
def _load_raw() -> dict[str, Any]:
    data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("markets"), list):
        raise ValueError("outreach_markets.json invalid")
    return data


def reload_outreach_markets() -> None:
    _load_raw.cache_clear()


def outreach_markets_config() -> dict[str, Any]:
    return dict(_load_raw())


def list_markets(*, enabled_only: bool = False, phase: int | None = None) -> list[dict[str, Any]]:
    rows = []
    for m in _load_raw().get("markets") or []:
        if not isinstance(m, dict) or not m.get("code"):
            continue
        if enabled_only and not m.get("enabled"):
            continue
        if phase is not None and int(m.get("phase") or 0) != phase:
            continue
        rows.append(dict(m))
    return rows


def get_market(code: str | None) -> dict[str, Any] | None:
    if not code:
        return None
    want = str(code).strip().upper()
    aliases = {"UK": "GB", "USA": "US", "SNG": "CIS"}
    want = aliases.get(want, want)
    for m in list_markets():
        if str(m.get("code", "")).upper() == want:
            return m
    return None


def market_daily_cap(code: str) -> int:
    m = get_market(code)
    if not m:
        return 20
    try:
        return max(1, min(200, int(m.get("daily_cap") or 20)))
    except (TypeError, ValueError):
        return 20


def market_template_lang(code: str | None) -> str | None:
    m = get_market(code)
    if not m:
        return None
    return str(m.get("template") or m.get("language") or "").strip() or None


def market_send_pool(code: str | None) -> str:
    m = get_market(code)
    if not m:
        return "de"
    pool = str(m.get("send_pool") or "de").strip().lower()
    return pool if pool in ("de", "cis", "us") else "de"


def market_legal_profile(code: str | None) -> str:
    m = get_market(code)
    if not m:
        return "de_impressum"
    return str(m.get("legal_profile") or "eu_gdpr")


def market_hubs(code: str | None) -> list[str]:
    m = get_market(code)
    if not m:
        return []
    hubs = m.get("hubs") or []
    return [str(h) for h in hubs if h]


def default_global_daily_cap() -> int:
    try:
        return int(_load_raw().get("global_daily_cap_default") or 120)
    except (TypeError, ValueError):
        return 120


def default_min_interval_sec() -> int:
    try:
        return int(_load_raw().get("min_interval_sec_default") or 90)
    except (TypeError, ValueError):
        return 90


def enabled_markets_sum_caps() -> int:
    return sum(market_daily_cap(str(m["code"])) for m in list_markets(enabled_only=True))


def allocation_mode() -> str:
    mode = str(_load_raw().get("allocation_mode") or "shared_global").strip().lower()
    return mode if mode in ("shared_global", "per_market") else "shared_global"


def quality_first() -> bool:
    return bool(_load_raw().get("quality_first", True))


def force_fill_quotas() -> bool:
    return bool(_load_raw().get("force_fill_quotas", False))


def shared_global_mode() -> bool:
    """One mailbox / one daily ceiling; soft per-country budgets only."""
    return allocation_mode() == "shared_global"


def market_website_profile(code: str | None) -> dict[str, Any]:
    m = get_market(code)
    if not m:
        return {}
    site = m.get("website") if isinstance(m.get("website"), dict) else {}
    currency = str(m.get("currency") or "EUR")
    symbol = str(m.get("symbol") or "€")
    # Commerce registry is source of truth for checkout currency/symbol.
    try:
        from app.integration.market_registry import MARKET_DEFAULT, get_market as get_commerce

        cm = get_commerce(str(m.get("code") or ""))
        if cm.code != MARKET_DEFAULT:
            currency = cm.currency
            symbol = cm.symbol
    except Exception:
        pass
    return {
        "code": str(m.get("code") or "").upper(),
        "language": m.get("language"),
        "template": m.get("template"),
        "currency": currency,
        "symbol": symbol,
        "legal_profile": m.get("legal_profile"),
        "locale": site.get("locale") or m.get("language") or "en",
        "hreflang": site.get("hreflang") or "",
        "legal_pages": list(site.get("legal_pages") or []),
        "footer_profile": site.get("footer_profile") or m.get("legal_profile"),
        "flag": m.get("flag") or "",
        "name_en": m.get("name_en") or m.get("code"),
        "name_ru": m.get("name_ru") or m.get("code"),
        "enabled": bool(m.get("enabled")),
    }


def list_website_markets(*, enabled_only: bool = True) -> list[dict[str, Any]]:
    return [
        market_website_profile(str(m["code"]))
        for m in list_markets(enabled_only=enabled_only)
    ]
