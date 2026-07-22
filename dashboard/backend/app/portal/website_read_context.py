"""R3.9.1 — Website Read Context.

First Portal business-facing read: load a Website by id.
Read-only · no endpoints · no Auth · no permissions · no mutations.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.queries import WebsiteQuery
from app.portal.read_service import PortalCatalogView, PortalReadService
from app.portal.website_view import WebsiteView

ENGINE_ID = "website_read_context_v1"


@dataclass(frozen=True)
class WebsiteReadContext:
    """Read-only Portal context for Website lookup."""

    _reads: PortalReadService

    @classmethod
    def from_service(cls, service: PortalReadService) -> WebsiteReadContext:
        return cls(_reads=service)

    @classmethod
    def from_catalog(cls, catalog: PortalCatalogView) -> WebsiteReadContext:
        return cls(_reads=PortalReadService(catalog))

    def get_website(self, website_id: str) -> WebsiteView | None:
        """Return WebsiteView for ``website_id``, or None if missing."""
        return self._reads.get_website(WebsiteQuery(website_id=website_id))
