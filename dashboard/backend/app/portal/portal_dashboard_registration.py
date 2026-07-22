"""R3.11.1 / R4.4 — Register Protected Dashboard endpoint.

Mounts GET /portal/websites/{id}/dashboard with AuthorizationFacade gate.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.authorization_facade import AuthorizationFacade
from app.portal.ownership_directory import (
    OwnershipDirectory,
    empty_ownership_directory,
)
from app.portal.portal_dashboard_router import (
    portal_dashboard_router,
    set_authorization_facade,
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
    ownerships: OwnershipDirectory | None = None,
) -> bool:
    """Wire Dashboard + Authorization facades and mount router."""
    resolved = (
        catalog
        if catalog is not None
        else load_portal_catalog_from_factory_sandbox()
    )
    ownership_dir = (
        ownerships if ownerships is not None else empty_ownership_directory()
    )
    set_website_dashboard_facade(
        WebsiteDashboardFacade.from_query(
            WebsiteDashboardQuery.from_catalog(resolved)
        )
    )
    set_authorization_facade(AuthorizationFacade(ownership_dir))
    app.include_router(portal_dashboard_router)
    return True
