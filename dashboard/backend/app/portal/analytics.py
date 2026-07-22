"""R5.2 — Analytics Domain (Overview, read-only).

Reference **read** Portal module. Answers: what overview metrics
exist for this Website right now?

```text
AnalyticsOverview
  visitors · page_views · last_updated · data_source
```

Does not authenticate · authorize · know Session · Ownership · HTTP.
No charts · GA4 · Matomo · events · writes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal

ENGINE_ID = "analytics_domain_v1"

AnalyticsDataSource = Literal["in_memory", "unknown"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class AnalyticsOverview:
    """Read-only overview snapshot for one Website."""

    website_id: str
    visitors: int
    page_views: int
    last_updated: str
    data_source: AnalyticsDataSource

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def empty_analytics_overview(website_id: str) -> AnalyticsOverview:
    """Default overview when no metrics are stored yet."""
    return AnalyticsOverview(
        website_id=website_id,
        visitors=0,
        page_views=0,
        last_updated=_utc_now_iso(),
        data_source="in_memory",
    )


def normalize_analytics_overview(overview: AnalyticsOverview) -> AnalyticsOverview:
    """Domain guard: non-negative counters only. No writes to external systems."""
    visitors = max(0, int(overview.visitors))
    page_views = max(0, int(overview.page_views))
    return AnalyticsOverview(
        website_id=overview.website_id,
        visitors=visitors,
        page_views=page_views,
        last_updated=overview.last_updated or _utc_now_iso(),
        data_source=overview.data_source,
    )
