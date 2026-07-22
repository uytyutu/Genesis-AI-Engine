"""OR1 — Request correlation context (portal ops)."""

from __future__ import annotations

from contextvars import ContextVar, Token
from uuid import uuid4

ENGINE_ID = "operational_context_v1"

_REQUEST_ID: ContextVar[str | None] = ContextVar("portal_ops_request_id", default=None)

HEADER_REQUEST_ID = "X-Request-ID"


def get_request_id() -> str | None:
    return _REQUEST_ID.get()


def set_request_id(request_id: str) -> Token:
    return _REQUEST_ID.set(request_id.strip() or str(uuid4()))


def ensure_request_id(existing: str | None = None) -> str:
    current = get_request_id()
    if current:
        return current
    rid = (existing or "").strip() or str(uuid4())
    _REQUEST_ID.set(rid)
    return rid


def clear_request_id() -> None:
    _REQUEST_ID.set(None)
