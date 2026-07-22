"""R3.12.5 — Authorization Domain.

Answers only: may this Account access this Website (for the given roles)?

```text
Account
    │
    ▼
WebsiteOwnership
    │
    ▼
Website
    │
    ▼
AuthorizationResult  (allowed | denied)
```

Binding rules:
* Access is decided **only** via ``WebsiteOwnership`` — never Account→Website alone.
* Authentication is assumed already successful; this module does not authenticate.
* Does not create Session / JWT / cookie; does not know Dashboard UI or HTTP.
* Role check uses an ``allowed_roles`` set (today typically ``{"owner"}``);
  future roles expand the set without changing this architecture.
* ``denial_reason`` values are internal — HTTP must not expose them verbatim.
* **Module-agnostic:** Authorization does not know *why* access is requested
  (Dashboard, CRM, Analytics, ChatBot, …). It only answers whether the Account
  has a required role on the Website. Callers supply ``allowed_roles``.

No Permissions engine · ACL editor · MFA · OAuth.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Collection, Iterable, Literal
from uuid import uuid4

from app.portal.account import Account
from app.portal.ownership import (
    FUTURE_ROLES,
    PortalRole,
    WebsiteOwnership,
    ownership_for_account_website,
)
from app.portal.website import Website

ENGINE_ID = "authorization_domain_v1"

# Default gate for R3.12.5 — expand later without changing authorize() shape.
DEFAULT_ALLOWED_ROLES: frozenset[str] = frozenset({"owner"})

AuthorizationOutcome = Literal["allowed", "denied"]

AuthorizationDenialReason = Literal[
    "ownership_missing",
    "role_not_allowed",
    "account_mismatch",
    "website_mismatch",
    "empty_allowed_roles",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class AuthorizationRequest:
    """Intent to access one Website as one Account — not an HTTP request."""

    request_id: str
    account_id: str
    website_id: str
    allowed_roles: frozenset[str]
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["allowed_roles"] = sorted(self.allowed_roles)
        return data


@dataclass(frozen=True)
class AuthorizationResult:
    """Outcome of one authorization check — never a session or token."""

    request_id: str
    account_id: str
    website_id: str
    outcome: AuthorizationOutcome
    denial_reason: AuthorizationDenialReason | None
    matched_role: str | None
    ownership_id: str | None
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def is_allowed(self) -> bool:
        return self.outcome == "allowed"


def new_authorization_request(
    account: Account,
    website: Website,
    *,
    allowed_roles: Collection[str] | None = None,
    request_id: str | None = None,
) -> AuthorizationRequest:
    roles = (
        frozenset(allowed_roles)
        if allowed_roles is not None
        else DEFAULT_ALLOWED_ROLES
    )
    return AuthorizationRequest(
        request_id=request_id or str(uuid4()),
        account_id=account.account_id,
        website_id=website.website_id,
        allowed_roles=roles,
        created_at=_utc_now_iso(),
    )


def authorize(
    request: AuthorizationRequest,
    ownerships: Iterable[WebsiteOwnership],
    *,
    account: Account | None = None,
    website: Website | None = None,
) -> AuthorizationResult:
    """Decide access via WebsiteOwnership + allowed_roles. No Authentication."""
    now = _utc_now_iso()

    def deny(
        reason: AuthorizationDenialReason,
    ) -> AuthorizationResult:
        return AuthorizationResult(
            request_id=request.request_id,
            account_id=request.account_id,
            website_id=request.website_id,
            outcome="denied",
            denial_reason=reason,
            matched_role=None,
            ownership_id=None,
            created_at=now,
        )

    if account is not None and account.account_id != request.account_id:
        return deny("account_mismatch")
    if website is not None and website.website_id != request.website_id:
        return deny("website_mismatch")
    if not request.allowed_roles:
        return deny("empty_allowed_roles")

    ownership = ownership_for_account_website(
        ownerships,
        account_id=request.account_id,
        website_id=request.website_id,
    )
    if ownership is None:
        return deny("ownership_missing")

    role: str = ownership.role
    if role not in request.allowed_roles:
        return deny("role_not_allowed")

    return AuthorizationResult(
        request_id=request.request_id,
        account_id=request.account_id,
        website_id=request.website_id,
        outcome="allowed",
        denial_reason=None,
        matched_role=role,
        ownership_id=ownership.ownership_id,
        created_at=now,
    )


def authorize_account_for_website(
    account: Account,
    website: Website,
    ownerships: Iterable[WebsiteOwnership],
    *,
    allowed_roles: Collection[str] | None = None,
) -> AuthorizationResult:
    """Convenience: build request + authorize (still Ownership-only)."""
    request = new_authorization_request(
        account, website, allowed_roles=allowed_roles
    )
    return authorize(request, ownerships, account=account, website=website)


# Re-export for discoverability next to FUTURE_ROLES.
AUTHORIZATION_FUTURE_ROLES = FUTURE_ROLES
_ = PortalRole  # typing anchor — constructible role remains ownership's PortalRole
