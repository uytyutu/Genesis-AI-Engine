"""R5.3 — Protected Website Domain HTTP (resource-state reference module).

GET/PUT /portal/websites/{website_id}/domain
→ RequestPrincipal → AuthorizationFacade → WebsiteDomainFacade

Invariant:
  Authentication = who · Authorization = may · Module = what
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.portal.authorization_facade import AuthorizationFacade
from app.portal.website_domain import WebsiteDomainError
from app.portal.website_domain_facade import WebsiteDomainFacade
from app.portal.website_domain_view import WebsiteDomainView

ENGINE_ID = "portal_website_domain_router_v1"

portal_website_domain_router = APIRouter(
    prefix="/portal",
    tags=["portal-website-domain"],
)

_domain_facade: WebsiteDomainFacade | None = None
_authz_facade: AuthorizationFacade | None = None


class WebsiteDomainWriteBody(BaseModel):
    """HTTP DTO — Website↔domain state only (stable when backends evolve)."""

    primary_domain: str = Field(default="", max_length=253)
    custom_domain: str = Field(default="", max_length=253)
    domain_status: Literal["none", "pending", "active", "error"] = "none"
    verification_status: Literal[
        "unverified", "pending", "verified", "failed"
    ] = "unverified"


def set_website_domain_facade(facade: WebsiteDomainFacade) -> None:
    global _domain_facade
    _domain_facade = facade


def set_authorization_facade(facade: AuthorizationFacade) -> None:
    global _authz_facade
    _authz_facade = facade


def clear_website_domain_facade() -> None:
    global _domain_facade, _authz_facade
    _domain_facade = None
    _authz_facade = None


def get_website_domain_facade() -> WebsiteDomainFacade:
    if _domain_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_website_domain_not_configured"
        )
    return _domain_facade


def get_authorization_facade() -> AuthorizationFacade:
    if _authz_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_authorization_not_configured"
        )
    return _authz_facade


def _require_authorized(
    request: Request,
    website_id: str,
    authz: AuthorizationFacade,
) -> None:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    decision = authz.check_website_access(account, website_id)
    if not decision.is_allowed:
        raise HTTPException(status_code=403, detail="forbidden")


@portal_website_domain_router.get(
    "/websites/{website_id}/domain",
    response_model=None,
)
def http_get_domain(
    website_id: str,
    request: Request,
    domain: Annotated[WebsiteDomainFacade, Depends(get_website_domain_facade)],
    authz: Annotated[AuthorizationFacade, Depends(get_authorization_facade)],
) -> WebsiteDomainView:
    _require_authorized(request, website_id, authz)
    return domain.get_domain(website_id)


@portal_website_domain_router.put(
    "/websites/{website_id}/domain",
    response_model=None,
)
def http_put_domain(
    website_id: str,
    body: WebsiteDomainWriteBody,
    request: Request,
    domain: Annotated[WebsiteDomainFacade, Depends(get_website_domain_facade)],
    authz: Annotated[AuthorizationFacade, Depends(get_authorization_facade)],
) -> WebsiteDomainView:
    _require_authorized(request, website_id, authz)
    try:
        return domain.update_domain(
            website_id,
            primary_domain=body.primary_domain,
            custom_domain=body.custom_domain,
            domain_status=body.domain_status,
            verification_status=body.verification_status,
        )
    except WebsiteDomainError:
        raise HTTPException(status_code=400, detail="invalid_domain") from None
