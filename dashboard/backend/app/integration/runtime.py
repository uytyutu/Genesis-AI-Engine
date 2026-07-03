"""Process uptime — avoids circular imports between context and mission_control."""

from __future__ import annotations

from datetime import datetime, timezone

_server_started_at: datetime | None = None
_brain_paused: bool = False


def mark_server_started() -> None:
    global _server_started_at
    _server_started_at = datetime.now(timezone.utc)


def get_server_started_at() -> datetime:
    global _server_started_at
    if _server_started_at is None:
        _server_started_at = datetime.now(timezone.utc)
    return _server_started_at


def set_brain_paused(value: bool) -> None:
    global _brain_paused
    _brain_paused = value


def is_brain_paused() -> bool:
    return _brain_paused


def light_system_status() -> dict:
    """Fast /api/status payload — no Brain/Kernel init."""
    started = get_server_started_at()
    uptime = max(0.0, (datetime.now(timezone.utc) - started).total_seconds())
    return {
        "name": "Genesis ABOS",
        "version": "0.2.0",
        "phase": "Integration Layer v0.1 (live)",
        "paused": is_brain_paused(),
        "uptime_sec": round(uptime, 1),
    }
