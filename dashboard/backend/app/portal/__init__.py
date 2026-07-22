"""Client Portal domain package (R3.5+ / R3.6+ / R3.12+).

Commercial: Client → Website → Deployment | Asset | EditSession.
Portal access (R3.12.1): Account → WebsiteOwnership → Website.
Read layer: Query → PortalReadService → View Models.
Factory builds artifacts; Portal manages Website — not Factory logic.
"""

from app.portal.account import Account, new_account
from app.portal.account_ownership_architecture import (
    ENGINE_ID as ACCOUNT_OWNERSHIP_ARCHITECTURE_ENGINE_ID,
    OWNERSHIP_FUTURE_ROLES,
)
from app.portal.activation_token import (
    ActivationToken,
    ActivationTokenError,
    activate_token,
    consume_token,
    expire_token,
    is_usable,
    new_activation_token,
    refresh_expiry_status,
    revoke_token,
)
from app.portal.asset import Asset, new_asset
from app.portal.client import Client, new_client, website_for_client
from app.portal.deployment import Deployment, attach_deployment, new_deployment
from app.portal.edit_session import EditSession, close_edit_session, new_edit_session
from app.portal.invitation import WebsiteInvitation, new_website_invitation
from app.portal.ownership import (
    FUTURE_ROLES,
    WebsiteOwnership,
    account_ids_for_website,
    grant_website_ownership,
    ownership_for_account_website,
    website_ids_for_account,
)
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
)
from app.portal.portal_dashboard_registration import register_portal_dashboard
from app.portal.portal_dashboard_router import portal_dashboard_router
from app.portal.website_catalog import load_portal_catalog_from_factory_sandbox
from app.portal.website_dashboard_facade import WebsiteDashboardFacade
from app.portal.website_dashboard_query import WebsiteDashboardQuery
from app.portal.website_dashboard_view import WebsiteDashboardView, build_website_dashboard_view
from app.portal.website_read_context import WebsiteReadContext
from app.portal.website_read_facade import WebsiteReadFacade
from app.portal.website_read_query import WebsiteReadQuery
from app.portal.website_view import WebsiteView
from app.portal.website import OrderWebsiteRef, Website, new_website

__all__ = [
    "ACCOUNT_OWNERSHIP_ARCHITECTURE_ENGINE_ID",
    "Account",
    "ActivationToken",
    "ActivationTokenError",
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
    "FUTURE_ROLES",
    "OWNERSHIP_FUTURE_ROLES",
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
    "WebsiteDashboardFacade",
    "WebsiteDashboardQuery",
    "WebsiteDashboardView",
    "WebsiteInvitation",
    "WebsiteOwnership",
    "WebsiteQuery",
    "WebsiteReadContext",
    "WebsiteReadFacade",
    "WebsiteReadQuery",
    "WebsiteView",
    "account_ids_for_website",
    "activate_token",
    "attach_deployment",
    "build_website_dashboard_view",
    "close_edit_session",
    "compose_portal_read",
    "consume_token",
    "expire_token",
    "grant_website_ownership",
    "is_portal_feature_enabled",
    "is_usable",
    "load_portal_catalog_from_factory_sandbox",
    "new_account",
    "new_activation_token",
    "new_asset",
    "new_client",
    "new_deployment",
    "new_edit_session",
    "new_website",
    "new_website_invitation",
    "ownership_for_account_website",
    "portal_dashboard_router",
    "portal_lifecycle_snapshot",
    "portal_read_router",
    "portal_registration_snapshot",
    "refresh_expiry_status",
    "register_portal_dashboard",
    "register_portal_read",
    "resolve_portal_lifecycle_state",
    "revoke_token",
    "teardown_portal_read",
    "website_for_client",
    "website_ids_for_account",
]
