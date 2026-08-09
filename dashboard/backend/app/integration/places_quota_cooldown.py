"""Pause Places Hunt when Google SearchText daily quota is exhausted.

Avoids burning the rest of the day on doomed requests across every market.
Daily Google quotas typically reset at midnight Pacific Time; without tzdata
we fall back to a 24h pause from the moment of the error.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _utc_now()).isoformat()


def _path(memory_dir: Path | None) -> Path | None:
    if not memory_dir:
        return None
    return Path(memory_dir) / "places_quota_cooldown.json"


def _load(memory_dir: Path | None) -> dict[str, Any]:
    path = _path(memory_dir)
    empty: dict[str, Any] = {
        "until": None,
        "last_reason": None,
        "detail": None,
        "updated_at": None,
    }
    if not path or not path.is_file():
        return empty
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty
    return data if isinstance(data, dict) else empty


def _save(memory_dir: Path | None, data: dict[str, Any]) -> None:
    path = _path(memory_dir)
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_until(raw: object) -> datetime | None:
    if not raw:
        return None
    try:
        text = str(raw).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        until = datetime.fromisoformat(text)
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
        return until.astimezone(timezone.utc)
    except ValueError:
        return None


def next_pacific_midnight_utc(*, now: datetime | None = None) -> datetime:
    """Next America/Los_Angeles midnight as UTC (Google daily quota reset).

    Falls back to now+24h when zone database (tzdata) is unavailable on Windows.
    """
    now_utc = now or _utc_now()
    try:
        from zoneinfo import ZoneInfo

        pacific = ZoneInfo("America/Los_Angeles")
        now_p = now_utc.astimezone(pacific)
        tomorrow = now_p.date() + timedelta(days=1)
        local_midnight = datetime(
            tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=pacific
        )
        return local_midnight.astimezone(timezone.utc)
    except Exception:
        return now_utc + timedelta(hours=24)


def is_quota_exceeded_message(text: str) -> bool:
    t = (text or "").lower()
    return "quota exceeded" in t and (
        "searchtext" in t or "places.googleapis.com" in t or "places_error" in t
    )


def mark_places_quota_exceeded(
    memory_dir: Path | None,
    *,
    detail: str = "",
    reason: str = "SearchTextRequest_per_day",
) -> dict[str, Any]:
    until = next_pacific_midnight_utc()
    data = {
        "until": _iso(until),
        "last_reason": reason,
        "detail": str(detail or "")[:400],
        "updated_at": _iso(),
    }
    _save(memory_dir, data)
    return data


def clear_places_quota_cooldown(
    memory_dir: Path | None,
    *,
    cleared_reason: str = "cleared_by_operator",
) -> dict[str, Any]:
    data = {
        "until": None,
        "last_reason": None,
        "detail": None,
        "updated_at": _iso(),
        "cleared_reason": str(cleared_reason or "cleared")[:120],
    }
    _save(memory_dir, data)
    return data


def places_quota_status(memory_dir: Path | None) -> dict[str, Any]:
    data = _load(memory_dir)
    until = _parse_until(data.get("until"))
    now = _utc_now()
    active = bool(until and until > now)
    if data.get("until") and not active:
        clear_places_quota_cooldown(memory_dir, cleared_reason="auto_clear_expired")
        data = _load(memory_dir)
        until = None
    blocker = ""
    if active and until:
        blocker = (
            "Google Places: суточная квота SearchText исчерпана. "
            f"Hunt на паузе до сброса (~{until.strftime('%Y-%m-%d %H:%M')} UTC). "
            "Смена рынка не поможет."
        )
    return {
        "active": active,
        "until": _iso(until) if until else None,
        "last_reason": data.get("last_reason"),
        "detail": data.get("detail"),
        "blocker_ru": blocker,
        "ok": not active,
    }


def is_places_quota_blocked(memory_dir: Path | None) -> bool:
    return bool(places_quota_status(memory_dir).get("active"))
