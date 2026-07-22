"""R3.12.3 — Password Creation domain (primary credentials only).

Sequence:

```text
Account Created          (pending_activation)
        │
        ▼
Activated                (activated)  ← ActivationToken consumed
        │
        ▼
Password Created         (PasswordCredential)
        │
        ▼
Ready for Authentication (ready)
```

Binding rules:
* Password Creation does **not** log the user in (no session / JWT / cookie).
* Domain stores only an opaque ``password_hash`` — hashing algorithm is infrastructure.
* Primary password may be set **once**; reset/change are later slices.
* Requires a **used** ActivationToken for the same Account (activation completed).
* **Sole path to ``Account.ready``:** successful ``create_primary_password`` after
  activation. No other module may set ``ready`` arbitrarily.

No Login · Authentication · HTTP · Email · SMTP · UI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from app.portal.account import Account, AccountStatus
from app.portal.activation_token import (
    ActivationToken,
    ActivationTokenError,
    consume_token,
)

ENGINE_ID = "password_credential_domain_v1"

PasswordCredentialStatus = Literal["active"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class PasswordCredential:
    """Primary password material for one Account — hash only, never plaintext."""

    credential_id: str
    account_id: str
    password_hash: str
    status: PasswordCredentialStatus
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class PasswordCredentialError(ValueError):
    """Invariant breach during primary password creation."""


def complete_account_activation(
    account: Account,
    token: ActivationToken,
    *,
    now: datetime | None = None,
) -> tuple[Account, ActivationToken]:
    """pending_activation + usable token → activated + used token.

    Does not create a password and does not authenticate.
    """
    if account.status != "pending_activation":
        raise PasswordCredentialError(
            f"activation requires pending_activation, got {account.status!r}"
        )
    if token.account_id != account.account_id:
        raise PasswordCredentialError("activation token account mismatch")
    try:
        used = consume_token(token, now=now)
    except ActivationTokenError as exc:
        raise PasswordCredentialError(str(exc)) from exc
    activated = replace(
        account,
        status="activated",
        updated_at=_utc_now_iso(),
    )
    return activated, used


def create_primary_password(
    account: Account,
    *,
    password_hash: str,
    activation_token: ActivationToken,
    existing: PasswordCredential | None = None,
    credential_id: str | None = None,
) -> tuple[Account, PasswordCredential]:
    """activated + used token → ready + PasswordCredential.

    Does **not** perform login. Rejects repeat primary setup.
    """
    if existing is not None:
        raise PasswordCredentialError("primary password already set")
    if account.status != "activated":
        raise PasswordCredentialError(
            f"password requires activated account, got {account.status!r}"
        )
    if activation_token.account_id != account.account_id:
        raise PasswordCredentialError("activation token account mismatch")
    if activation_token.status != "used":
        raise PasswordCredentialError(
            f"password requires used activation token, got {activation_token.status!r}"
        )
    opaque = password_hash.strip()
    if not opaque:
        raise PasswordCredentialError("password_hash must be non-empty opaque material")
    if "\n" in opaque or "\r" in opaque:
        raise PasswordCredentialError("password_hash must be a single opaque string")

    credential = PasswordCredential(
        credential_id=credential_id or str(uuid4()),
        account_id=account.account_id,
        password_hash=opaque,
        status="active",
        created_at=_utc_now_iso(),
    )
    ready: Account = replace(
        account,
        status="ready",
        updated_at=_utc_now_iso(),
    )
    # status is AccountStatus — "ready" must be in Literal
    _assert_ready(ready.status)
    return ready, credential


def is_ready_for_authentication(account: Account) -> bool:
    """True when primary password path completed — still not logged in."""
    return account.status == "ready"


def _assert_ready(status: AccountStatus) -> None:
    if status != "ready":
        raise PasswordCredentialError(f"internal: expected ready, got {status!r}")
