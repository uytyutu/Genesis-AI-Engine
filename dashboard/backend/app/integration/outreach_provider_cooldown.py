"""Provider cooldown for outreach sends (Resend 429 etc.).

Reality: hammering Resend after rate-limit empties the Ready queue visually
while nothing leaves the mailbox. Cool down and prefer Gmail when available.

Test cooldowns (reason starts with manual_/test_) auto-clear on status read
so diagnostic experiments cannot block production sending overnight.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_DEFAULT_RESEND_COOLDOWN_SEC = 900  # 15 minutes after 429
_TEST_REASON_PREFIXES = ("manual_", "test_", "diag_", "failover_test")


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


def _is_test_reason(reason: object) -> bool:
    text = str(reason or "").strip().lower()
    return any(text.startswith(p) for p in _TEST_REASON_PREFIXES)


def clear_resend_cooldown(
    memory_dir: Path | None,
    *,
    cleared_reason: str = "cleared_by_operator",
) -> dict[str, Any]:
    """Wipe Resend cooldown so sending can resume (CEO / health monitor)."""
    data = {
        "resend_until": None,
        "last_reason": None,
        "updated_at": _iso(),
        "cleared_reason": str(cleared_reason or "cleared")[:120],
    }
    _save(memory_dir, data)
    return data


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
    # Drop diagnostic cooldowns automatically — they must not block production.
    data = _load(memory_dir)
    if _is_test_reason(data.get("last_reason")):
        clear_resend_cooldown(memory_dir, cleared_reason="auto_clear_test_cooldown")
        return True
    until = _parse_until(data.get("resend_until"))
    if until is None:
        return True
    if _utc_now() >= until:
        # Expired — normalize file so UI does not show stale reason
        if data.get("resend_until") or data.get("last_reason"):
            clear_resend_cooldown(memory_dir, cleared_reason="auto_clear_expired")
        return True
    return False


def cooldown_status(memory_dir: Path | None) -> dict[str, Any]:
    available = resend_available(memory_dir)
    data = _load(memory_dir)
    reason = data.get("last_reason")
    until = data.get("resend_until")
    if available:
        return {
            "resend_available": True,
            "resend_until": None,
            "last_reason": None,
            "blocker_ru": None,
            "human_ru": "Resend доступен",
        }
    until_short = str(until or "")[:19]
    return {
        "resend_available": False,
        "resend_until": until,
        "last_reason": reason,
        "blocker_ru": (
            f"Resend на паузе до {until_short} "
            f"(причина: {reason or 'rate_limit'}). "
            "Если Gmail не подключён — отправка лидов стоит."
        ),
        "human_ru": (
            f"Resend недоступен до {until_short}. "
            "Подключите Gmail или дождитесь снятия лимита."
        ),
    }
