"""R3.10.2 — Website Dashboard Query.

execute(website_id) → WebsiteDashboardView | None

Composes WebsiteReadFacade (website) + PortalReadService (current deployment).
No Domain Website · FastAPI · Auth · writes · business logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.queries import WebsiteQuery
from app.portal.read_service import PortalCatalogView, PortalReadService
from app.portal.website_dashboard_view import (
    WebsiteDashboardView,
    build_website_dashboard_view,
)
from app.portal.website_read_context import WebsiteReadContext
from app.portal.website_read_facade import WebsiteReadFacade
from app.portal.website_read_query import WebsiteReadQuery

ENGINE_ID = "website_dashboard_query_v1"


@dataclass(frozen=True)
class WebsiteDashboardQuery:
    """One use case: load the cabinet dashboard aggregate for a Website."""

    _facade: WebsiteReadFacade
    _reads: PortalReadService

    @classmethod
    def from_parts(
        cls,
        facade: WebsiteReadFacade,
        reads: PortalReadService,
    ) -> WebsiteDashboardQuery:
        return cls(_facade=facade, _reads=reads)

    @classmethod
    def from_catalog(cls, catalog: PortalCatalogView) -> WebsiteDashboardQuery:
        reads = PortalReadService(catalog)
        facade = WebsiteReadFacade.from_query(
            WebsiteReadQuery.from_context(WebsiteReadContext.from_service(reads))
        )
        return cls.from_parts(facade, reads)

    def execute(self, website_id: str) -> WebsiteDashboardView | None:
        website = self._facade.get_website(website_id)
        if website is None:
            return None
        deployment = self._reads.get_current_deployment(
            WebsiteQuery(website_id=website_id)
        )
        return build_website_dashboard_view(
            website,
            current_deployment=deployment,
        )
