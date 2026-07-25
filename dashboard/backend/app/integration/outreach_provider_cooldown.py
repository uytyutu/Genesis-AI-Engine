"""Provider cooldown for outreach sends (Resend 429 etc.).

Reality: hammering Resend after rate-limit empties the Ready queue visually
while nothing leaves the mailbox. Cool down and prefer Gmail when available.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_DEFAULT_RESEND_COOLDOWN_SEC = 900  # 15 minutes after 429


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _utc_now()).isoformat()


def _path(memory_dir: Path | None) -> Path | None:
    if not memory_dir:
        return None
    return Path(memory_dir) / "outreach_provider_cooldown.json"


def _load(memory_dir: Path | None) -> dict[str, Any]:
    path = _path(memory_dir)
    empty = {"resend_until": None, "last_reason": None, "updated_at": None}
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


def mark_resend_rate_limited(
    memory_dir: Path | None,
    *,
    seconds: int = _DEFAULT_RESEND_COOLDOWN_SEC,
    reason: str = "resend_error:429",
) -> dict[str, Any]:
    until = _utc_now() + timedelta(seconds=max(60, int(seconds)))
    data = {
        "resend_until": _iso(until),
        "last_reason": reason,
        "updated_at": _iso(),
    }
    _save(memory_dir, data)
    return data


def resend_available(memory_dir: Path | None) -> bool:
    data = _load(memory_dir)
    raw = data.get("resend_until")
    if not raw:
        return True
    try:
        text = str(raw).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        until = datetime.fromisoformat(text)
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
        return _utc_now() >= until.astimezone(timezone.utc)
    except ValueError:
        return True


def cooldown_status(memory_dir: Path | None) -> dict[str, Any]:
    data = _load(memory_dir)
    available = resend_available(memory_dir)
    return {
        "resend_available": available,
        "resend_until": None if available else data.get("resend_until"),
        "last_reason": data.get("last_reason"),
        "blocker_ru": (
            None
            if available
            else (
                "Resend rate limit (429) — пауза до "
                f"{str(data.get('resend_until') or '')[:19]}. "
                "Пока пробуем Gmail, если подключён; иначе очередь ждёт."
            )
        ),
    }
