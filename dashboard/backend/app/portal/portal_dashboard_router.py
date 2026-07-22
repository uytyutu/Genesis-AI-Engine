"""R3.11.1 — Dashboard Read Endpoint.

GET /portal/websites/{website_id}/dashboard
→ WebsiteDashboardFacade.get_dashboard → WebsiteDashboardView

Auth: temporary stub (always allows) until real Portal Auth.
No write operations.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.portal.website_dashboard_facade import WebsiteDashboardFacade
from app.portal.website_dashboard_view import WebsiteDashboardView

ENGINE_ID = "portal_dashboard_router_v1"

portal_dashboard_router = APIRouter(prefix="/portal", tags=["portal-dashboard"])

_facade: WebsiteDashboardFacade | None = None


def set_website_dashboard_facade(facade: WebsiteDashboardFacade) -> None:
    global _facade
    _facade = facade


def clear_website_dashboard_facade() -> None:
    global _facade
    _facade = None


def get_website_dashboard_facade() -> WebsiteDashboardFacade:
    if _facade is None:
        raise HTTPException(status_code=503, detail="portal_dashboard_not_configured")
    return _facade


def dashboard_auth_stub() -> None:
    """Temporary Auth stub — always allows. Replace with real Auth later."""
    return None


@portal_dashboard_router.get(
    "/websites/{website_id}/dashboard",
    response_model=None,
)
def http_get_dashboard(
    website_id: str,
    facade: Annotated[WebsiteDashboardFacade, Depends(get_website_dashboard_facade)],
    _: Annotated[None, Depends(dashboard_auth_stub)] = None,
) -> WebsiteDashboardView:
    view = facade.get_dashboard(website_id)
    if view is None:
        raise HTTPException(status_code=404, detail="dashboard_not_found")
    return view
