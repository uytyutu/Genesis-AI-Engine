"""R3.7.3 — FastAPI Portal Read Router (unmounted).

HTTP → Path/Query models → PortalReadHandlers → View Models.

Does not modify PortalReadService / domain / views / queries.
Not registered in main.py — mount later when catalog is wired.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.portal.asset import AssetType
from app.portal.read_api_contract import (
    ClientPath,
    WebsiteAssetsQuery,
    WebsitePath,
)
from app.portal.read_api_handlers import PortalReadHandlers
from app.portal.views import (
    AssetView,
    ClientView,
    DeploymentView,
    EditSessionView,
    WebsiteView,
)

ENGINE_ID = "portal_read_router_v1"

portal_read_router = APIRouter(prefix="/portal", tags=["portal-read"])

_handlers: PortalReadHandlers | None = None


def set_portal_read_handlers(handlers: PortalReadHandlers) -> None:
    """Test / future app wiring — not called from main.py in this slice."""
    global _handlers
    _handlers = handlers


def clear_portal_read_handlers() -> None:
    global _handlers
    _handlers = None


def get_portal_read_handlers() -> PortalReadHandlers:
    if _handlers is None:
        raise HTTPException(status_code=503, detail="portal_read_not_configured")
    return _handlers


@portal_read_router.get("/clients/{client_id}", response_model=None)
def http_get_client(
    client_id: str,
    handlers: Annotated[PortalReadHandlers, Depends(get_portal_read_handlers)],
) -> ClientView:
    view = handlers.get_client(ClientPath(client_id=client_id))
    if view is None:
        raise HTTPException(status_code=404, detail="client_not_found")
    return view


@portal_read_router.get("/websites/{website_id}", response_model=None)
def http_get_website(
    website_id: str,
    handlers: Annotated[PortalReadHandlers, Depends(get_portal_read_handlers)],
) -> WebsiteView:
    view = handlers.get_website(WebsitePath(website_id=website_id))
    if view is None:
        raise HTTPException(status_code=404, detail="website_not_found")
    return view


@portal_read_router.get("/websites/{website_id}/deployment", response_model=None)
def http_get_current_deployment(
    website_id: str,
    handlers: Annotated[PortalReadHandlers, Depends(get_portal_read_handlers)],
) -> DeploymentView:
    view = handlers.get_current_deployment(WebsitePath(website_id=website_id))
    if view is None:
        raise HTTPException(status_code=404, detail="deployment_not_found")
    return view


@portal_read_router.get("/websites/{website_id}/assets", response_model=None)
def http_get_assets(
    website_id: str,
    handlers: Annotated[PortalReadHandlers, Depends(get_portal_read_handlers)],
    asset_type: Annotated[AssetType | None, Query()] = None,
) -> list[AssetView]:
    # Empty list is a valid read result — handlers do not map absence → HTTP.
    return list(
        handlers.get_assets(
            WebsiteAssetsQuery(website_id=website_id, asset_type=asset_type)
        )
    )


@portal_read_router.get("/websites/{website_id}/edit-session", response_model=None)
def http_get_open_edit_session(
    website_id: str,
    handlers: Annotated[PortalReadHandlers, Depends(get_portal_read_handlers)],
) -> EditSessionView:
    view = handlers.get_open_edit_session(WebsitePath(website_id=website_id))
    if view is None:
        raise HTTPException(status_code=404, detail="edit_session_not_found")
    return view
