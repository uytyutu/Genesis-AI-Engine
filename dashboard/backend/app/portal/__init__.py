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
from app.portal.portal_health import portal_registration_snapshot
from app.portal.portal_lifecycle import (
    resolve_portal_lifecycle_state,
    portal_lifecycle_snapshot,
)
from app.portal.portal_profile import PORTAL_PROFILE, is_portal_feature_enabled
from app.portal.portal_read_router import portal_read_router
from app.portal.portal_registration import register_portal_read
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
from app.portal.website_dashboard_view import WebsiteDashboardView, build_website_dashboard_view
from app.portal.website_read_context import WebsiteReadContext
from app.portal.website_read_facade import WebsiteReadFacade
from app.portal.website_read_query import WebsiteReadQuery
from app.portal.website_view import WebsiteView
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
    "PORTAL_PROFILE",
    "PORTAL_READ_ROUTES",
    "PortalCatalog",
    "PortalCatalogView",
    "PortalReadHandlers",
    "PortalReadRoute",
    "PortalReadService",
    "PortalReadStack",
    "Website",
    "WebsiteQuery",
    "WebsiteDashboardView",
    "WebsiteReadContext",
    "WebsiteReadFacade",
    "WebsiteReadQuery",
    "WebsiteView",
    "attach_deployment",
    "build_website_dashboard_view",
    "close_edit_session",
    "compose_portal_read",
    "is_portal_feature_enabled",
    "new_asset",
    "new_client",
    "new_deployment",
    "new_edit_session",
    "new_website",
    "portal_lifecycle_snapshot",
    "portal_read_router",
    "portal_registration_snapshot",
    "register_portal_read",
    "resolve_portal_lifecycle_state",
    "teardown_portal_read",
    "website_for_client",
]
