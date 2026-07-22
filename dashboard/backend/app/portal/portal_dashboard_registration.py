"""R3.11.1 — Register Dashboard Read Endpoint.

Mounts GET /portal/websites/{id}/dashboard via WebsiteDashboardFacade.
Independent of PORTAL_PROFILE.feature_enabled (first live Dashboard read).
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.portal_bootstrap import empty_portal_catalog
from app.portal.portal_dashboard_router import (
    portal_dashboard_router,
    set_website_dashboard_facade,
)
from app.portal.read_service import PortalCatalogView
from app.portal.website_dashboard_facade import WebsiteDashboardFacade
from app.portal.website_dashboard_query import WebsiteDashboardQuery

ENGINE_ID = "portal_dashboard_registration_v1"


def register_portal_dashboard(
    app: FastAPI,
    *,
    catalog: PortalCatalogView | None = None,
) -> bool:
    """Wire facade + mount Dashboard read router. Returns True when mounted."""
    resolved = catalog if catalog is not None else empty_portal_catalog()
    facade = WebsiteDashboardFacade.from_query(
        WebsiteDashboardQuery.from_catalog(resolved)
    )
    set_website_dashboard_facade(facade)
    app.include_router(portal_dashboard_router)
    return True
