"""R3.11.1 / R4.4 — Protected Dashboard Read Endpoint.

GET /portal/websites/{website_id}/dashboard
→ RequestPrincipal → AuthorizationFacade → WebsiteDashboardFacade

Invariant:
  Authentication = who · Authorization = may · Dashboard = what
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.portal.authorization_facade import AuthorizationFacade
from app.portal.website_dashboard_facade import WebsiteDashboardFacade
from app.portal.website_dashboard_view import WebsiteDashboardView

ENGINE_ID = "portal_dashboard_router_v1"

portal_dashboard_router = APIRouter(prefix="/portal", tags=["portal-dashboard"])

_dash_facade: WebsiteDashboardFacade | None = None
_authz_facade: AuthorizationFacade | None = None


def set_website_dashboard_facade(facade: WebsiteDashboardFacade) -> None:
    global _dash_facade
    _dash_facade = facade


def set_authorization_facade(facade: AuthorizationFacade) -> None:
    global _authz_facade
    _authz_facade = facade


def clear_website_dashboard_facade() -> None:
    global _dash_facade, _authz_facade
    _dash_facade = None
    _authz_facade = None


def get_website_dashboard_facade() -> WebsiteDashboardFacade:
    if _dash_facade is None:
        raise HTTPException(status_code=503, detail="portal_dashboard_not_configured")
    return _dash_facade


def get_authorization_facade() -> AuthorizationFacade:
    if _authz_facade is None:
        raise HTTPException(status_code=503, detail="portal_authorization_not_configured")
    return _authz_facade


@portal_dashboard_router.get(
    "/websites/{website_id}/dashboard",
    response_model=None,
)
def http_get_dashboard(
    website_id: str,
    request: Request,
    dash: Annotated[WebsiteDashboardFacade, Depends(get_website_dashboard_facade)],
    authz: Annotated[AuthorizationFacade, Depends(get_authorization_facade)],
) -> WebsiteDashboardView:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")

    decision = authz.check_website_access(account, website_id)
    if not decision.is_allowed:
        raise HTTPException(status_code=403, detail="forbidden")

    view = dash.get_dashboard(website_id)
    if view is None:
        raise HTTPException(status_code=404, detail="dashboard_not_found")
    return view
