"""R3.12.4 — Authentication Domain.

Answers only: are the presented credentials correct?

```text
ready
  │
  ▼
Authentication Attempt
  ├── authenticated
  └── failed
```

Binding rules:
* Requires ``Account.status == ready`` and an active ``PasswordCredential``.
* Compares **already computed** opaque hashes (infra hashes the presented password).
* Does **not** create session, JWT, cookie, or Bearer token.
* Does **not** change Account status.
* ``failure_reason`` values are **internal domain reasons** for tests and audit.
  HTTP/UI must not expose them verbatim — map to a generic user message
  (e.g. "Invalid email or password").

No HTTP · FastAPI · MFA · OAuth · rate limiting · password reset.
"""

from __future__ import annotations

import hmac
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from app.portal.account import Account
from app.portal.password_credential import PasswordCredential

ENGINE_ID = "authentication_domain_v1"

AuthenticationOutcome = Literal["authenticated", "failed"]

AuthenticationFailureReason = Literal[
    "account_not_ready",
    "account_suspended",
    "credential_missing",
    "credential_inactive",
    "account_mismatch",
    "hash_mismatch",
    "empty_presented_hash",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class AuthenticationAttempt:
    """One authentication try — record only, not a session."""

    attempt_id: str
    account_id: str
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuthenticationResult:
    """Outcome of one attempt — never carries tokens or cookies."""

    attempt_id: str
    account_id: str
    outcome: AuthenticationOutcome
    failure_reason: AuthenticationFailureReason | None
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def is_authenticated(self) -> bool:
        return self.outcome == "authenticated"


def authenticate(
    account: Account,
    credential: PasswordCredential | None,
    *,
    presented_password_hash: str,
    attempt_id: str | None = None,
) -> tuple[AuthenticationAttempt, AuthenticationResult]:
    """Verify opaque hashes. Does not log the user in."""
    now = _utc_now_iso()
    attempt = AuthenticationAttempt(
        attempt_id=attempt_id or str(uuid4()),
        account_id=account.account_id,
        created_at=now,
    )

    def fail(
        reason: AuthenticationFailureReason,
    ) -> tuple[AuthenticationAttempt, AuthenticationResult]:
        return attempt, AuthenticationResult(
            attempt_id=attempt.attempt_id,
            account_id=account.account_id,
            outcome="failed",
            failure_reason=reason,
            created_at=now,
        )

    if account.status == "suspended":
        return fail("account_suspended")
    if account.status != "ready":
        return fail("account_not_ready")
    if credential is None:
        return fail("credential_missing")
    if credential.account_id != account.account_id:
        return fail("account_mismatch")
    if credential.status != "active":
        return fail("credential_inactive")

    presented = presented_password_hash.strip()
    if not presented:
        return fail("empty_presented_hash")

    stored = credential.password_hash
    if not hmac.compare_digest(presented, stored):
        return fail("hash_mismatch")

    return attempt, AuthenticationResult(
        attempt_id=attempt.attempt_id,
        account_id=account.account_id,
        outcome="authenticated",
        failure_reason=None,
        created_at=now,
    )
