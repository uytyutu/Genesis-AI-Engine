"""R3.10.3 — Website Dashboard Facade.

Single entry for future Dashboard API / UI.
Facade → WebsiteDashboardQuery → WebsiteDashboardView.

Only ``get_dashboard(website_id)``.
No FastAPI · Auth · Domain · writes · business logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.website_dashboard_query import WebsiteDashboardQuery
from app.portal.website_dashboard_view import WebsiteDashboardView

ENGINE_ID = "website_dashboard_facade_v1"


@dataclass(frozen=True)
class WebsiteDashboardFacade:
    """Sole entry point for Portal Dashboard reads."""

    _query: WebsiteDashboardQuery

    @classmethod
    def from_query(cls, query: WebsiteDashboardQuery) -> WebsiteDashboardFacade:
        return cls(_query=query)

    def get_dashboard(self, website_id: str) -> WebsiteDashboardView | None:
        return self._query.execute(website_id)
