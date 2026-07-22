"""R3.12.1 — Website Invitation (architecture only).

Models the *intent* to grant WebsiteOwnership to an email.
Does **not** send email, mint tokens, or accept invitations.

Activation Token / SMTP land in later R3.12 slices.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from app.portal.ownership import PortalRole
from app.portal.website import Website

ENGINE_ID = "website_invitation_v1"

InvitationStatus = Literal["pending", "accepted", "revoked", "expired"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class WebsiteInvitation:
    """Architectural invite row — no delivery channel in R3.12.1."""

    invitation_id: str
    website_id: str
    invited_email: str
    intended_role: PortalRole
    status: InvitationStatus
    created_at: str
    expires_at: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_website_invitation(
    website: Website,
    *,
    invited_email: str,
    intended_role: PortalRole = "owner",
    status: InvitationStatus = "pending",
    expires_at: str | None = None,
    invitation_id: str | None = None,
) -> WebsiteInvitation:
    """Construct an invitation record (in-memory; no email / token)."""
    return WebsiteInvitation(
        invitation_id=invitation_id or str(uuid4()),
        website_id=website.website_id,
        invited_email=invited_email.strip().lower(),
        intended_role=intended_role,
        status=status,
        created_at=_utc_now_iso(),
        expires_at=expires_at,
    )
