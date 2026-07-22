"""R3.9.4 — Website Read Facade.

Single Portal UI entry for Website reads.
Facade → WebsiteReadQuery → WebsiteReadContext → WebsiteView.

Only ``get_website(website_id)``.
No FastAPI · Auth · Domain Website · mutations · business logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.website_read_query import WebsiteReadQuery
from app.portal.website_view import WebsiteView

ENGINE_ID = "website_read_facade_v1"


@dataclass(frozen=True)
class WebsiteReadFacade:
    """Sole entry point for future Portal UI Website reads."""

    _query: WebsiteReadQuery

    @classmethod
    def from_query(cls, query: WebsiteReadQuery) -> WebsiteReadFacade:
        return cls(_query=query)

    def get_website(self, website_id: str) -> WebsiteView | None:
        return self._query.execute(website_id)
