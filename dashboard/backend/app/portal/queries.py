"""R3.6.2 — Portal Query Objects.

Search parameters only — no business logic, no HTTP, no mutations.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.asset import AssetType

ENGINE_ID = "portal_query_v1"


@dataclass(frozen=True)
class ClientQuery:
    """Locate a Client by id."""

    client_id: str


@dataclass(frozen=True)
class WebsiteQuery:
    """Locate a Website by id (also used for website-scoped reads)."""

    website_id: str


@dataclass(frozen=True)
class AssetQuery:
    """List/filter Assets for a Website."""

    website_id: str
    asset_type: AssetType | None = None
