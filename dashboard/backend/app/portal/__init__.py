"""Client Portal domain package (R3.5+ / R3.6+).

Architecture: Client → Website → Deployment | Asset | EditSession.
Read layer: Query → PortalReadService → View Models.
Factory builds artifacts; Portal manages Website — not Factory logic.
"""

from app.portal.asset import Asset, new_asset
from app.portal.client import Client, new_client, website_for_client
from app.portal.deployment import Deployment, attach_deployment, new_deployment
from app.portal.edit_session import EditSession, close_edit_session, new_edit_session
from app.portal.portal_bootstrap import PortalReadStack, compose_portal_read, teardown_portal_read
from app.portal.portal_read_router import portal_read_router
from app.portal.queries import AssetQuery, ClientQuery, WebsiteQuery
from app.portal.read_api_contract import PORTAL_READ_ROUTES, PortalReadRoute
from app.portal.read_api_handlers import PortalReadHandlers
from app.portal.read_service import PortalCatalog, PortalCatalogView, PortalReadService
from app.portal.views import (
    AssetView,
    ClientView,
    DeploymentView,
    EditSessionView,
    WebsiteView,
)
from app.portal.website import OrderWebsiteRef, Website, new_website

__all__ = [
    "Asset",
    "AssetQuery",
    "AssetView",
    "Client",
    "ClientQuery",
    "ClientView",
    "Deployment",
    "DeploymentView",
    "EditSession",
    "EditSessionView",
    "OrderWebsiteRef",
    "PORTAL_READ_ROUTES",
    "PortalCatalog",
    "PortalCatalogView",
    "PortalReadHandlers",
    "PortalReadRoute",
    "PortalReadService",
    "PortalReadStack",
    "Website",
    "WebsiteQuery",
    "WebsiteView",
    "attach_deployment",
    "close_edit_session",
    "compose_portal_read",
    "new_asset",
    "new_client",
    "new_deployment",
    "new_edit_session",
    "new_website",
    "portal_read_router",
    "teardown_portal_read",
    "website_for_client",
]
