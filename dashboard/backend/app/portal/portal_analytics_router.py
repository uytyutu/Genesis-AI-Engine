"""R5.2 — Protected Analytics Overview HTTP (read-only reference module).

GET /portal/websites/{website_id}/analytics
→ RequestPrincipal → AuthorizationFacade → AnalyticsFacade

Invariant:
  Authentication = who · Authorization = may · Module = what
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.portal.analytics_facade import AnalyticsFacade
from app.portal.analytics_view import AnalyticsOverviewView
from app.portal.authorization_facade import AuthorizationFacade

ENGINE_ID = "portal_analytics_router_v1"

portal_analytics_router = APIRouter(
    prefix="/portal",
    tags=["portal-analytics"],
)

_analytics_facade: AnalyticsFacade | None = None
_authz_facade: AuthorizationFacade | None = None


def set_analytics_facade(facade: AnalyticsFacade) -> None:
    global _analytics_facade
    _analytics_facade = facade


def set_authorization_facade(facade: AuthorizationFacade) -> None:
    global _authz_facade
    _authz_facade = facade


def clear_analytics_facade() -> None:
    global _analytics_facade, _authz_facade
    _analytics_facade = None
    _authz_facade = None


def get_analytics_facade() -> AnalyticsFacade:
    if _analytics_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_analytics_not_configured"
        )
    return _analytics_facade


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


@portal_analytics_router.get(
    "/websites/{website_id}/analytics",
    response_model=None,
)
def http_get_analytics(
    website_id: str,
    request: Request,
    analytics: Annotated[AnalyticsFacade, Depends(get_analytics_facade)],
    authz: Annotated[AuthorizationFacade, Depends(get_authorization_facade)],
) -> AnalyticsOverviewView:
    _require_authorized(request, website_id, authz)
    return analytics.get_overview(website_id)
