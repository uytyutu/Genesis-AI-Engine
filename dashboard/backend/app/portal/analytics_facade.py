"""R5.2 — AnalyticsFacade (reference read-only ModuleFacade).

```text
Authorization (caller)
    ↓
AnalyticsFacade
    ↓
Analytics Domain + Store
```

Sole application entry for Analytics Overview reads.
Does not authenticate · authorize · know cookies · Session · Ownership.
No PUT / write API on this facade.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.analytics import (
    empty_analytics_overview,
    normalize_analytics_overview,
)
from app.portal.analytics_store import AnalyticsStore
from app.portal.analytics_view import (
    AnalyticsOverviewView,
    build_analytics_overview_view,
)

ENGINE_ID = "analytics_facade_v1"


@dataclass(frozen=True)
class AnalyticsFacade:
    """Read-only ModuleFacade — copy this shape for other GET modules."""

    _store: AnalyticsStore

    @classmethod
    def from_store(cls, store: AnalyticsStore) -> AnalyticsFacade:
        return cls(_store=store)

    def get_overview(self, website_id: str) -> AnalyticsOverviewView:
        row = self._store.get_overview(website_id)
        if row is None:
            row = empty_analytics_overview(website_id)
        return build_analytics_overview_view(normalize_analytics_overview(row))
