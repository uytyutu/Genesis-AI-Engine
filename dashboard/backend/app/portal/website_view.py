"""R3.9.2 — Website View Contract.

Immutable read projection of a Website for Portal.
Portal must never receive the Website domain model directly.

No endpoints · Auth · mutations · business logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.website import Website, WebsiteStatus

ENGINE_ID = "website_view_contract_v1"

WEBSITE_VIEW_FIELDS: tuple[str, ...] = (
    "website_id",
    "client_id",
    "product_id",
    "market_code",
    "status",
    "deployment_id",
)


@dataclass(frozen=True)
class WebsiteView:
    """Stable Portal read contract for one Website."""

    website_id: str
    client_id: str
    product_id: str
    market_code: str
    status: WebsiteStatus
    deployment_id: str | None


def to_website_view(website: Website) -> WebsiteView:
    """Map domain Website → WebsiteView (Portal boundary)."""
    return WebsiteView(
        website_id=website.website_id,
        client_id=website.client_id,
        product_id=website.product_id,
        market_code=website.market_code,
        status=website.status,
        deployment_id=website.deployment_id,
    )
