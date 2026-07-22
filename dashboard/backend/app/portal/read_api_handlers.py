"""R3.7.2 — Portal Read API Handlers.

Bridge: Contract path/query models → PortalReadService → View Models.

No HTTP · no FastAPI · no Auth · no framework reply types · not mounted.
"""

from __future__ import annotations

from app.portal.queries import AssetQuery, ClientQuery, WebsiteQuery
from app.portal.read_api_contract import (
    ClientPath,
    WebsiteAssetsQuery,
    WebsitePath,
)
from app.portal.read_service import PortalReadService
from app.portal.views import (
    AssetView,
    ClientView,
    DeploymentView,
    EditSessionView,
    WebsiteView,
)

ENGINE_ID = "portal_read_api_handlers_v1"


class PortalReadHandlers:
    """One handler per GET contract route — framework-agnostic."""

    def __init__(self, read_service: PortalReadService) -> None:
        self._reads = read_service

    def get_client(self, path: ClientPath) -> ClientView | None:
        return self._reads.get_client(ClientQuery(client_id=path.client_id))

    def get_website(self, path: WebsitePath) -> WebsiteView | None:
        return self._reads.get_website(WebsiteQuery(website_id=path.website_id))

    def get_current_deployment(self, path: WebsitePath) -> DeploymentView | None:
        return self._reads.get_current_deployment(
            WebsiteQuery(website_id=path.website_id)
        )

    def get_assets(self, query: WebsiteAssetsQuery) -> tuple[AssetView, ...]:
        return self._reads.get_assets(
            AssetQuery(
                website_id=query.website_id,
                asset_type=query.asset_type,
            )
        )

    def get_open_edit_session(self, path: WebsitePath) -> EditSessionView | None:
        return self._reads.get_open_edit_session(
            WebsiteQuery(website_id=path.website_id)
        )


HANDLER_NAMES: tuple[str, ...] = (
    "get_client",
    "get_website",
    "get_current_deployment",
    "get_assets",
    "get_open_edit_session",
)
