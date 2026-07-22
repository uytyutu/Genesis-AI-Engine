"""R5.2 — AnalyticsStore (temporary in-memory adapter).

``AnalyticsStore`` is the abstraction; ``InMemoryAnalyticsStore`` is today's
adapter. Future GA4/Matomo adapters plug in without changing the Facade.
"""

from __future__ import annotations

from typing import Protocol

from app.portal.analytics import AnalyticsOverview

ENGINE_ID = "analytics_store_v1"


class AnalyticsStore(Protocol):
    def get_overview(self, website_id: str) -> AnalyticsOverview | None: ...


class InMemoryAnalyticsStore:
    """Process-local overview map — replace with real analytics later."""

    def __init__(
        self,
        *,
        overviews: dict[str, AnalyticsOverview] | None = None,
    ) -> None:
        self._rows: dict[str, AnalyticsOverview] = dict(overviews or {})

    def get_overview(self, website_id: str) -> AnalyticsOverview | None:
        return self._rows.get(website_id)

    def put_overview(self, overview: AnalyticsOverview) -> None:
        """Test/seed helper — not exposed via Facade HTTP writes."""
        self._rows[overview.website_id] = overview
