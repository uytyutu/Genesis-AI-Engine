"""R3.10.1 — Website Dashboard View.

Immutable aggregate for the future Portal cabinet home page.
Composes WebsiteView + site status + optional current DeploymentView.

Not an API · Auth · UI · or write path.
Does not expand WebsiteView with dashboard-only fields.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.views import DeploymentView
from app.portal.website import WebsiteStatus
from app.portal.website_view import WebsiteView

ENGINE_ID = "website_dashboard_view_v1"


@dataclass(frozen=True)
class WebsiteDashboardView:
    """Portal cabinet dashboard contract for one Website."""

    website: WebsiteView
    status: WebsiteStatus
    current_deployment: DeploymentView | None


def build_website_dashboard_view(
    website: WebsiteView,
    *,
    current_deployment: DeploymentView | None = None,
) -> WebsiteDashboardView:
    """Compose dashboard projection from existing read contracts only."""
    return WebsiteDashboardView(
        website=website,
        status=website.status,
        current_deployment=current_deployment,
    )
