"""R3.12.1 — Website Ownership (Account ↔ Website).

Commercial ownership remains ``Website.client_id → Client``.
Portal access ownership is ``WebsiteOwnership`` (Account on Website).

Rules (R3.12.1):
* One Account may own / access many Websites (multi-site).
* One Website may have many Account memberships (multi-user later).
* Only role in force today: ``owner``.

No permissions engine · no Auth · no HTTP.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Literal
from uuid import uuid4

from app.portal.account import Account
from app.portal.website import Website

ENGINE_ID = "website_ownership_v1"

# Only "owner" is constructible today. Names below are architectural intent.
FUTURE_ROLES: tuple[str, ...] = ("owner", "manager", "editor", "viewer")
PortalRole = Literal["owner"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class WebsiteOwnership:
    """Account's portal relationship to one Website."""

    ownership_id: str
    account_id: str
    website_id: str
    role: PortalRole
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def grant_website_ownership(
    account: Account,
    website: Website,
    *,
    role: PortalRole = "owner",
    ownership_id: str | None = None,
) -> WebsiteOwnership:
    """Grant portal access. Does not change Website.client_id (commercial)."""
    return WebsiteOwnership(
        ownership_id=ownership_id or str(uuid4()),
        account_id=account.account_id,
        website_id=website.website_id,
        role=role,
        created_at=_utc_now_iso(),
    )


def website_ids_for_account(
    ownerships: Iterable[WebsiteOwnership],
    account_id: str,
) -> tuple[str, ...]:
    """Multi-site: all website_ids an Account may access."""
    return tuple(
        o.website_id for o in ownerships if o.account_id == account_id
    )


def account_ids_for_website(
    ownerships: Iterable[WebsiteOwnership],
    website_id: str,
) -> tuple[str, ...]:
    """Multi-user ready: all account_ids on one Website."""
    return tuple(
        o.account_id for o in ownerships if o.website_id == website_id
    )


def ownership_for_account_website(
    ownerships: Iterable[WebsiteOwnership],
    *,
    account_id: str,
    website_id: str,
) -> WebsiteOwnership | None:
    for o in ownerships:
        if o.account_id == account_id and o.website_id == website_id:
            return o
    return None
