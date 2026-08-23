"""Hunt slot efficiency memory — city×niche yield before burning SearchText.

Mission 1.1: a slot that already returned 0 new companies must not be
SearchText'd again until cooldown (Places daily reset / 24h).
Does not touch Smart Offer / Outbox / email.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def slot_key(*, market: str, city: str, query: str) -> str:
    return "|".join(
        [
            (market or "").strip().upper(),
            (city or "").strip().casefold(),
            (query or "").strip().casefold(),
        ]
    )


def _path(memory_dir: Path | None) -> Path | None:
    if not memory_dir:
        return None
    return Path(memory_dir) / "outreach_hunt_slot_memory.json"


def _load(memory_dir: Path | None) -> dict[str, Any]:
    path = _path(memory_dir)
    empty: dict[str, Any] = {"slots": {}, "updated_at": None}
    if not path or not path.is_file():
        return empty
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty
    if not isinstance(data, dict):
        return empty
    data.setdefault("slots", {})
    if not isinstance(data["slots"], dict):
        data["slots"] = {}
    return data


def _save(memory_dir: Path | None, data: dict[str, Any]) -> None:
    path = _path(memory_dir)
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _utc_now().isoformat()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_ts(raw: Any) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _cooldown_until(*, created: int) -> datetime:
    """Zero-yield slots cool until Places daily reset; positive yield cools briefly."""
    now = _utc_now()
    if int(created or 0) <= 0:
        try:
            from app.integration.places_quota_cooldown import next_pacific_midnight_utc

            return next_pacific_midnight_utc()
        except Exception:
            return now + timedelta(hours=24)
    # Already harvested this city×niche — avoid immediate re-query (same place_ids).
    return now + timedelta(hours=12)


def is_slot_exhausted(
    memory_dir: Path | None,
    *,
    market: str,
    city: str,
    query: str,
    now: datetime | None = None,
) -> bool:
    """True → do not call SearchText for this city×niche yet.

    Covers zero-yield exhaustion and short cool-down after a successful harvest
    (same place_ids would burn quota again).
    """
    data = _load(memory_dir)
    row = data["slots"].get(slot_key(market=market, city=city, query=query))
    if not isinstance(row, dict):
        return False
    until = _parse_ts(row.get("cool_until") or row.get("exhausted_until"))
    if not until:
        return False
    return until > (now or _utc_now())


def record_slot_hunt(
    memory_dir: Path | None,
    *,
    market: str,
    city: str,
    query: str,
    created: int,
) -> dict[str, Any]:
    """Record SearchText outcome. created==0 → exhaust until cooldown."""
    if not memory_dir:
        return {}
    data = _load(memory_dir)
    key = slot_key(market=market, city=city, query=query)
    prev = data["slots"].get(key) if isinstance(data["slots"].get(key), dict) else {}
    created_n = max(0, int(created or 0))
    cool = _cooldown_until(created=created_n)
    row = {
        "market": (market or "").strip().upper(),
        "city": (city or "").strip(),
        "query": (query or "").strip(),
        "searches": int(prev.get("searches") or 0) + 1,
        "total_created": int(prev.get("total_created") or 0) + created_n,
        "last_created": created_n,
        "last_searched_at": _utc_now().isoformat(),
        "cool_until": cool.isoformat(),
        "exhausted_until": cool.isoformat() if created_n <= 0 else prev.get("exhausted_until"),
    }
    if created_n > 0:
        # Harvested: cool via cool_until; clear hard exhausted flag.
        row["exhausted_until"] = None
    data["slots"][key] = row
    _save(memory_dir, data)
    return row


def slot_memory_stats(memory_dir: Path | None, *, now: datetime | None = None) -> dict[str, Any]:
    """CEO snapshot: how many slots are cooling / exhausted."""
    data = _load(memory_dir)
    now = now or _utc_now()
    total = 0
    cooling = 0
    zero_yield = 0
    for row in (data.get("slots") or {}).values():
        if not isinstance(row, dict):
            continue
        total += 1
        if int(row.get("last_created") or 0) <= 0 and int(row.get("searches") or 0) > 0:
            zero_yield += 1
        until = _parse_ts(row.get("cool_until") or row.get("exhausted_until"))
        if until and until > now:
            cooling += 1
    return {
        "slots_tracked": total,
        "slots_cooling": cooling,
        "slots_last_zero_yield": zero_yield,
    }
