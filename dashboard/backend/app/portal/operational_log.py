"""OR2 — Structured logging for Conversation → AI → Actions."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.portal.operational_context import get_request_id

ENGINE_ID = "operational_log_v1"

_logger = logging.getLogger("virtus.portal.ops")


def emit_ops_event(
    *,
    operation: str,
    status: str = "ok",
    level: str = "info",
    conversation_id: str | None = None,
    channel: str | None = None,
    provider: str | None = None,
    duration_ms: float | None = None,
    error: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Emit one JSON ops event (searchable by request_id / conversation_id)."""
    event: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "level": level,
        "request_id": get_request_id(),
        "conversation_id": conversation_id,
        "channel": channel,
        "provider": provider,
        "operation": operation,
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
        "status": status,
        "error": error,
    }
    for key, value in extra.items():
        if value is not None:
            event[key] = value
    payload = {k: v for k, v in event.items() if v is not None}
    line = json.dumps(payload, ensure_ascii=False)
    if level == "error":
        _logger.error(line)
    elif level == "warning":
        _logger.warning(line)
    else:
        _logger.info(line)
    return payload
