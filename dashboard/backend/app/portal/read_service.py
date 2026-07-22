"""R3.6.1 — Portal Read Service.

Read-only access to Portal domain entities.
No mutations · no persistence · no API · no Auth · no UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.portal.asset import Asset
from app.portal.client import Client
from app.portal.deployment import Deployment
from app.portal.edit_session import EditSession
from app.portal.website import Website

ENGINE_ID = "portal_read_service_v1"


@dataclass(frozen=True)
class PortalCatalog:
    """In-memory snapshot of Portal domain rows — not a database."""

    clients: Mapping[str, Client]
    websites: Mapping[str, Website]
    deployments: Mapping[str, Deployment]
    assets: Mapping[str, Asset]
    edit_sessions: Mapping[str, EditSession]


class PortalReadService:
    """Query Portal domain models without changing state."""

    def __init__(self, catalog: PortalCatalog) -> None:
        self._catalog = catalog

    def get_client(self, client_id: str) -> Client | None:
        return self._catalog.clients.get(client_id)

    def get_website(self, website_id: str) -> Website | None:
        return self._catalog.websites.get(website_id)

    def get_current_deployment(self, website_id: str) -> Deployment | None:
        website = self.get_website(website_id)
        if website is None or not website.deployment_id:
            return None
        dep = self._catalog.deployments.get(website.deployment_id)
        if dep is None or dep.website_id != website_id:
            return None
        return dep

    def get_assets(self, website_id: str) -> tuple[Asset, ...]:
        return tuple(
            a
            for a in self._catalog.assets.values()
            if a.website_id == website_id
        )

    def get_open_edit_session(self, website_id: str) -> EditSession | None:
        opens = [
            s
            for s in self._catalog.edit_sessions.values()
            if s.website_id == website_id and s.status == "open"
        ]
        if not opens:
            return None
        # Prefer earliest start; multi-open is a future invariant concern.
        opens.sort(key=lambda s: s.started_at)
        return opens[0]
