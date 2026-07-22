"""R3.6.1–R3.6.3 — Portal Read Service.

Read-only access via Query objects → View Models.
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
from app.portal.views import (
    AssetView,
    ClientView,
    DeploymentView,
    EditSessionView,
    WebsiteView,
    to_asset_view,
    to_client_view,
    to_deployment_view,
    to_edit_session_view,
    to_website_view,
)
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

    Returns View Models only (not domain entities). Missing → ``None`` or ``()``.
    """

    def __init__(self, catalog: PortalCatalogView) -> None:
        self._catalog = catalog

    def get_client(self, query: ClientQuery) -> ClientView | None:
        client = self._catalog.clients.get(query.client_id)
        return to_client_view(client) if client is not None else None

    def get_website(self, query: WebsiteQuery) -> WebsiteView | None:
        website = self._catalog.websites.get(query.website_id)
        return to_website_view(website) if website is not None else None

    def get_current_deployment(self, query: WebsiteQuery) -> DeploymentView | None:
        website = self._catalog.websites.get(query.website_id)
        if website is None or not website.deployment_id:
            return None
        dep = self._catalog.deployments.get(website.deployment_id)
        if dep is None or dep.website_id != query.website_id:
            return None
        return to_deployment_view(dep)

    def get_assets(self, query: AssetQuery) -> tuple[AssetView, ...]:
        rows = [
            a
            for a in self._catalog.assets.values()
            if a.website_id == query.website_id
        ]
        if query.asset_type is not None:
            rows = [a for a in rows if a.asset_type == query.asset_type]
        return tuple(to_asset_view(a) for a in rows)

    def get_open_edit_session(self, query: WebsiteQuery) -> EditSessionView | None:
        opens = [
            s
            for s in self._catalog.edit_sessions.values()
            if s.website_id == query.website_id and s.status == "open"
        ]
        if not opens:
            return None
        opens.sort(key=lambda s: s.started_at)
        return to_edit_session_view(opens[0])
