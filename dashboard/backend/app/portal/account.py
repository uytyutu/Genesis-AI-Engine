"""R3.12.1 — Account domain model.

Account = human platform subject (will authenticate later).
Client  = commercial party (buyer / company) — see ``client.py``.

Account is **not** Client. Access to sites is via WebsiteOwnership, not via
Website.client_id.

No password · no JWT · no HTTP · no email in this slice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "account_domain_v1"

AccountStatus = Literal["pending_activation", "active", "suspended"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Account:
    """Platform login subject — not a commercial Client, not a Website."""

    account_id: str
    email: str
    display_name: str
    status: AccountStatus
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_account(
    *,
    email: str,
    display_name: str,
    status: AccountStatus = "pending_activation",
    account_id: str | None = None,
) -> Account:
    """Construct an Account row (in-memory only — no auth, no persistence)."""
    now = _utc_now_iso()
    return Account(
        account_id=account_id or str(uuid4()),
        email=email.strip().lower(),
        display_name=display_name.strip(),
        status=status,
        created_at=now,
        updated_at=now,
    )
