"""R5.2 — Analytics View (HTTP/API shape).

Presentation only. No Auth · no domain rules · no persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.analytics import AnalyticsOverview

ENGINE_ID = "analytics_view_v1"


@dataclass(frozen=True)
class AnalyticsOverviewView:
    website_id: str
    visitors: int
    page_views: int
    last_updated: str
    data_source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "website_id": self.website_id,
            "visitors": self.visitors,
            "page_views": self.page_views,
            "last_updated": self.last_updated,
            "data_source": self.data_source,
        }


def build_analytics_overview_view(
    overview: AnalyticsOverview,
) -> AnalyticsOverviewView:
    return AnalyticsOverviewView(
        website_id=overview.website_id,
        visitors=overview.visitors,
        page_views=overview.page_views,
        last_updated=overview.last_updated,
        data_source=overview.data_source,
    )
