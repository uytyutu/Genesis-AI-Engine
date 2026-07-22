"""R3.9.3 — Website Read Query.

Formal read query: execute(website_id) → WebsiteView | None.
Uses WebsiteReadContext only — never the Website domain model.
No FastAPI · Auth · mutations · business logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.website_read_context import WebsiteReadContext
from app.portal.website_view import WebsiteView

ENGINE_ID = "website_read_query_v1"


@dataclass(frozen=True)
class WebsiteReadQuery:
    """Executable Website read — Portal boundary entry for one lookup."""

    _context: WebsiteReadContext

    @classmethod
    def from_context(cls, context: WebsiteReadContext) -> WebsiteReadQuery:
        return cls(_context=context)

    def execute(self, website_id: str) -> WebsiteView | None:
        return self._context.get_website(website_id)
