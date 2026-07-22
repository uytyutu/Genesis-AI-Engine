"""R3.6.1 / R3.6.2 — Portal Read Service.

Read-only access to Portal domain entities via Query objects.
Depends on a catalog *view* (Protocol) — not a concrete store.
No mutations · no persistence · no API · no Auth · no UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, runtime_checkable

from app.portal.asset import Asset
from app.portal.client import Client
from app.portal.deployment import Deployment
from app.portal.edit_session import EditSession
from app.portal.queries import AssetQuery, ClientQuery, WebsiteQuery
from app.portal.website import Website

ENGINE_ID = "portal_read_service_v1"


@runtime_checkable
class PortalCatalogView(Protocol):
    """Abstraction over Portal rows — snapshot, repository, or DB later."""

    clients: Mapping[str, Client]
    websites: Mapping[str, Website]
    deployments: Mapping[str, Deployment]
    assets: Mapping[str, Asset]
    edit_sessions: Mapping[str, EditSession]


@dataclass(frozen=True)
class PortalCatalog:
    """In-memory snapshot of Portal domain rows — not a database."""

    clients: Mapping[str, Client]
    websites: Mapping[str, Website]
    deployments: Mapping[str, Deployment]
    assets: Mapping[str, Asset]
    edit_sessions: Mapping[str, EditSession]


class PortalReadService:
    """Query Portal domain models without changing state.

    Missing entities return ``None`` (or empty tuple for collections) —
    consistent style for the Portal read layer.
    """

    def __init__(self, catalog: PortalCatalogView) -> None:
        self._catalog = catalog

    def get_client(self, query: ClientQuery) -> Client | None:
        return self._catalog.clients.get(query.client_id)

    def get_website(self, query: WebsiteQuery) -> Website | None:
        return self._catalog.websites.get(query.website_id)

    def get_current_deployment(self, query: WebsiteQuery) -> Deployment | None:
        website = self.get_website(query)
        if website is None or not website.deployment_id:
            return None
        dep = self._catalog.deployments.get(website.deployment_id)
        if dep is None or dep.website_id != query.website_id:
            return None
        return dep

    def get_assets(self, query: AssetQuery) -> tuple[Asset, ...]:
        rows = [
            a
            for a in self._catalog.assets.values()
            if a.website_id == query.website_id
        ]
        if query.asset_type is not None:
            rows = [a for a in rows if a.asset_type == query.asset_type]
        return tuple(rows)

    def get_open_edit_session(self, query: WebsiteQuery) -> EditSession | None:
        opens = [
            s
            for s in self._catalog.edit_sessions.values()
            if s.website_id == query.website_id and s.status == "open"
        ]
        if not opens:
            return None
        opens.sort(key=lambda s: s.started_at)
        return opens[0]
