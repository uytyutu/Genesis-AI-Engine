"""R4.2 — Session domain.

Server-side login session bound to an Account.
Authentication Domain does not know about Session.

No middleware · no cookie reading · no JWT in this module.
"""

from __future__ import annotations

import secrets
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "session_domain_v1"

SessionStatus = Literal["active", "revoked"]
DEFAULT_SESSION_TTL = timedelta(days=7)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def new_session_id() -> str:
    """Unpredictable session identifier (not a JWT)."""
    return secrets.token_urlsafe(32)


@dataclass(frozen=True)
class Session:
    """Server-held session row — client only receives the id via HttpOnly cookie."""

    session_id: str
    account_id: str
    status: SessionStatus
    created_at: str
    expires_at: str
    revoked_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class SessionError(ValueError):
    """Invalid session lifecycle transition."""


def create_session(
    account_id: str,
    *,
    ttl: timedelta = DEFAULT_SESSION_TTL,
    session_id: str | None = None,
    now: datetime | None = None,
) -> Session:
    moment = now or _utc_now()
    return Session(
        session_id=session_id or new_session_id(),
        account_id=account_id,
        status="active",
        created_at=moment.isoformat(),
        expires_at=(moment + ttl).isoformat(),
        revoked_at=None,
    )


def revoke_session(session: Session, *, now: datetime | None = None) -> Session:
    if session.status == "revoked":
        raise SessionError("session already revoked")
    moment = now or _utc_now()
    return replace(
        session,
        status="revoked",
        revoked_at=moment.isoformat(),
    )


def is_session_active(session: Session, *, now: datetime | None = None) -> bool:
    if session.status != "active":
        return False
    moment = now or _utc_now()
    expires = datetime.fromisoformat(session.expires_at.replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return moment < expires
