"""R4.4 — AuthorizationFacade (HTTP → Authorization Domain).

Answers: may this Account access this Website?
Does not know cookies, sessions, or Dashboard content.
Does not authenticate.
"""

from __future__ import annotations

from typing import Collection
from uuid import uuid4

from app.portal.account import Account
from app.portal.authorization import (
    DEFAULT_ALLOWED_ROLES,
    AuthorizationRequest,
    AuthorizationResult,
    authorize,
)
from app.portal.ownership_directory import OwnershipDirectory

ENGINE_ID = "authorization_facade_v1"


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class AuthorizationFacade:
    """Sole application entry for Website access checks."""

    def __init__(self, ownerships: OwnershipDirectory) -> None:
        self._ownerships = ownerships

    def check_website_access(
        self,
        account: Account,
        website_id: str,
        *,
        allowed_roles: Collection[str] | None = None,
    ) -> AuthorizationResult:
        roles = (
            frozenset(allowed_roles)
            if allowed_roles is not None
            else DEFAULT_ALLOWED_ROLES
        )
        request = AuthorizationRequest(
            request_id=str(uuid4()),
            account_id=account.account_id,
            website_id=website_id,
            allowed_roles=roles,
            created_at=_utc_now_iso(),
        )
        return authorize(
            request,
            self._ownerships.all_ownerships(),
            account=account,
        )
