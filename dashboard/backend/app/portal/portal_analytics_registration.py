"""R5.2 — Register Analytics Overview module (read-only reference).

Mounts GET /portal/websites/{id}/analytics with AuthorizationFacade gate.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.analytics_facade import AnalyticsFacade
from app.portal.analytics_store import AnalyticsStore, InMemoryAnalyticsStore
from app.portal.authorization_facade import AuthorizationFacade
from app.portal.ownership_directory import (
    OwnershipDirectory,
    empty_ownership_directory,
)
from app.portal.portal_analytics_router import (
    portal_analytics_router,
    set_analytics_facade,
    set_authorization_facade,
)

ENGINE_ID = "portal_analytics_registration_v1"


def register_portal_analytics(
    app: FastAPI,
    *,
    ownerships: OwnershipDirectory | None = None,
    store: AnalyticsStore | None = None,
) -> bool:
    """Wire Analytics + Authorization facades and mount router."""
    ownership_dir = (
        ownerships if ownerships is not None else empty_ownership_directory()
    )
    analytics_store = store if store is not None else InMemoryAnalyticsStore()
    set_analytics_facade(AnalyticsFacade.from_store(analytics_store))
    set_authorization_facade(AuthorizationFacade(ownership_dir))
    app.include_router(portal_analytics_router)
    return True
