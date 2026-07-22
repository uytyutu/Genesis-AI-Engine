"""R3.11.1 / R3.11.2 — Register Dashboard Read Endpoint.

Mounts GET /portal/websites/{id}/dashboard via WebsiteDashboardFacade.
Default catalog: Factory sandbox (R3.11.2) — not an empty in-memory stub.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.portal_dashboard_router import (
    portal_dashboard_router,
    set_website_dashboard_facade,
)
from app.portal.read_service import PortalCatalogView
from app.portal.website_catalog import load_portal_catalog_from_factory_sandbox
from app.portal.website_dashboard_facade import WebsiteDashboardFacade
from app.portal.website_dashboard_query import WebsiteDashboardQuery

ENGINE_ID = "portal_dashboard_registration_v1"


def register_portal_dashboard(
    app: FastAPI,
    *,
    catalog: PortalCatalogView | None = None,
) -> bool:
    """Wire facade from Factory sandbox catalog (or override) + mount router."""
    resolved = (
        catalog
        if catalog is not None
        else load_portal_catalog_from_factory_sandbox()
    )
    facade = WebsiteDashboardFacade.from_query(
        WebsiteDashboardQuery.from_catalog(resolved)
    )
    set_website_dashboard_facade(facade)
    app.include_router(portal_dashboard_router)
    return True
