"""R3.12.2 — Activation Token domain.

One-time activation material bound to an Account.
Lifecycle only — no email, HTTP, links, passwords, or JWT.

States: created → active → used | expired | revoked

Binding rule — not authentication:
``ActivationToken`` exists only for **primary account activation**.
It is never a temporary login, session, or general-purpose auth factor.
After a successful activation path the token reaches a terminal state;
ongoing access uses the future Authentication system (R3.12.4+).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from app.portal.account import Account

ENGINE_ID = "activation_token_domain_v1"

ActivationTokenStatus = Literal[
    "created",
    "active",
    "used",
    "expired",
    "revoked",
]

_TERMINAL: frozenset[ActivationTokenStatus] = frozenset(
    {"used", "expired", "revoked"}
)
DEFAULT_TTL = timedelta(hours=48)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _parse_iso(value: str) -> datetime:
    # Accept trailing Z
    normalized = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass(frozen=True)
class ActivationToken:
    """Opaque activation record for one Account — not a URL, not a password."""

    token_id: str
    account_id: str
    status: ActivationTokenStatus
    created_at: str
    expires_at: str
    used_at: str | None
    revoked_at: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ActivationTokenError(ValueError):
    """Invalid lifecycle transition or invariant breach."""


def new_activation_token(
    account: Account,
    *,
    expires_at: str | None = None,
    ttl: timedelta = DEFAULT_TTL,
    token_id: str | None = None,
    status: ActivationTokenStatus = "created",
) -> ActivationToken:
    """Create a token in ``created`` (default). Does not send or hash anything."""
    if status not in ("created", "active"):
        raise ActivationTokenError(
            f"new_activation_token cannot start as {status!r}"
        )
    now = _utc_now()
    exp = expires_at if expires_at is not None else (now + ttl).isoformat()
    if _parse_iso(exp) <= now:
        raise ActivationTokenError("expires_at must be in the future")
    return ActivationToken(
        token_id=token_id or str(uuid4()),
        account_id=account.account_id,
        status=status,
        created_at=now.isoformat(),
        expires_at=exp,
        used_at=None,
        revoked_at=None,
    )


def activate_token(token: ActivationToken) -> ActivationToken:
    """created → active."""
    if token.status != "created":
        raise ActivationTokenError(
            f"activate requires status=created, got {token.status!r}"
        )
    if _is_past_expiry(token):
        raise ActivationTokenError("cannot activate an expired token")
    return replace(token, status="active")


def consume_token(
    token: ActivationToken,
    *,
    now: datetime | None = None,
) -> ActivationToken:
    """active → used (one-shot). Rejects non-active, already-used, expired."""
    moment = now or _utc_now()
    if token.status == "used":
        raise ActivationTokenError("token already used")
    if token.status == "revoked":
        raise ActivationTokenError("token revoked")
    if token.status == "expired" or _is_past_expiry(token, now=moment):
        raise ActivationTokenError("token expired")
    if token.status != "active":
        raise ActivationTokenError(
            f"consume requires status=active, got {token.status!r}"
        )
    return replace(
        token,
        status="used",
        used_at=moment.replace(microsecond=0).isoformat(),
    )


def expire_token(token: ActivationToken) -> ActivationToken:
    """created|active → expired. Terminal states stay terminal."""
    if token.status in _TERMINAL:
        raise ActivationTokenError(
            f"cannot expire terminal status {token.status!r}"
        )
    return replace(token, status="expired")


def revoke_token(token: ActivationToken) -> ActivationToken:
    """created|active → revoked."""
    if token.status in _TERMINAL:
        raise ActivationTokenError(
            f"cannot revoke terminal status {token.status!r}"
        )
    return replace(
        token,
        status="revoked",
        revoked_at=_utc_now_iso(),
    )


def is_usable(
    token: ActivationToken,
    *,
    now: datetime | None = None,
) -> bool:
    """True only when status is active and before expires_at."""
    if token.status != "active":
        return False
    return not _is_past_expiry(token, now=now or _utc_now())


def refresh_expiry_status(
    token: ActivationToken,
    *,
    now: datetime | None = None,
) -> ActivationToken:
    """If created/active and past expires_at → expired; else unchanged."""
    if token.status not in ("created", "active"):
        return token
    if _is_past_expiry(token, now=now or _utc_now()):
        return replace(token, status="expired")
    return token


def _is_past_expiry(
    token: ActivationToken,
    *,
    now: datetime | None = None,
) -> bool:
    return (now or _utc_now()) >= _parse_iso(token.expires_at)
