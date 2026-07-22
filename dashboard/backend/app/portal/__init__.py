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
from app.portal.authentication import (
    AuthenticationAttempt,
    AuthenticationResult,
    authenticate,
)
from app.portal.authentication_facade import (
    AuthenticationFacade,
    InMemoryAuthenticationDirectory,
    empty_authentication_directory,
)
from app.portal.authorization import (
    AUTHORIZATION_FUTURE_ROLES,
    DEFAULT_ALLOWED_ROLES,
    AuthorizationRequest,
    AuthorizationResult,
    authorize,
    authorize_account_for_website,
    new_authorization_request,
)
from app.portal.authorization_facade import AuthorizationFacade
from app.portal.client import Client, new_client, website_for_client
from app.portal.deployment import Deployment, attach_deployment, new_deployment
from app.portal.edit_session import EditSession, close_edit_session, new_edit_session
from app.portal.invitation import WebsiteInvitation, new_website_invitation
from app.portal.login_api_contract import LoginRequest, LoginResponse
from app.portal.ownership import (
    FUTURE_ROLES,
    WebsiteOwnership,
    account_ids_for_website,
    grant_website_ownership,
    ownership_for_account_website,
    website_ids_for_account,
)
from app.portal.password_credential import (
    PasswordCredential,
    PasswordCredentialError,
    complete_account_activation,
    create_primary_password,
    is_ready_for_authentication,
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
from app.portal.session import Session, create_session
from app.portal.session_cookie import SessionCookieFactory
from app.portal.session_facade import SessionFacade
from app.portal.session_store import InMemorySessionStore
from app.portal.views import (
    AssetView,
    ClientView,
    DeploymentView,
    EditSessionView,
)
from app.portal.portal_authentication_middleware import (
    register_portal_authentication_middleware,
)
from app.portal.portal_dashboard_registration import register_portal_dashboard
from app.portal.portal_dashboard_router import portal_dashboard_router
from app.portal.portal_login_registration import register_portal_login
from app.portal.portal_login_router import portal_login_router
from app.portal.portal_user_journey import (
    PortalOwnerJourneyState,
    build_published_owner_journey,
)
from app.portal.portal_website_settings_registration import (
    register_portal_website_settings,
)
from app.portal.portal_website_settings_router import portal_website_settings_router
from app.portal.portal_analytics_registration import register_portal_analytics
from app.portal.portal_analytics_router import portal_analytics_router
from app.portal.portal_website_domain_registration import (
    register_portal_website_domain,
)
from app.portal.portal_website_domain_router import portal_website_domain_router
from app.portal.portal_chatbot_registration import register_portal_chatbot
from app.portal.portal_chatbot_router import portal_chatbot_router
from app.portal.portal_product_catalog_registration import (
    register_portal_product_catalog,
)
from app.portal.portal_product_catalog_router import portal_product_catalog_router
from app.portal.portal_my_products_registration import register_portal_my_products
from app.portal.portal_my_products_router import portal_my_products_router
from app.portal.portal_product_activation_registration import (
    register_portal_product_activation,
)
from app.portal.portal_product_activation_router import (
    portal_product_activation_router,
)
from app.portal.analytics import AnalyticsOverview, empty_analytics_overview
from app.portal.analytics_facade import AnalyticsFacade
from app.portal.analytics_store import InMemoryAnalyticsStore
from app.portal.analytics_view import AnalyticsOverviewView
from app.portal.chatbot import (
    ChatBotConnection,
    ChatBotConnectionUpdate,
    apply_chatbot_connection_update,
    empty_chatbot_connection,
)
from app.portal.chatbot_facade import ChatBotFacade
from app.portal.chatbot_integration_adapter import StubChatBotIntegrationAdapter
from app.portal.chatbot_store import InMemoryChatBotStore
from app.portal.chatbot_view import ChatBotView
from app.portal.product import Product, default_product_catalog
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_activation_store import InMemoryProductActivationStore
from app.portal.product_catalog_facade import ProductCatalogFacade
from app.portal.product_catalog_store import InMemoryProductCatalogStore
from app.portal.product_catalog_view import ProductCatalogItemView
from app.portal.product_ownership import ProductOwnership, new_product_ownership
from app.portal.product_ownership_facade import ProductOwnershipFacade
from app.portal.product_ownership_store import InMemoryProductOwnershipStore
from app.portal.product_ownership_view import MyProductView
from app.portal.website_ownership_bridge import WebsiteOwnershipBridge
from app.portal.website_domain import (
    WebsiteDomain,
    WebsiteDomainUpdate,
    apply_website_domain_update,
    empty_website_domain,
)
from app.portal.website_domain_facade import WebsiteDomainFacade
from app.portal.website_domain_store import InMemoryWebsiteDomainStore
from app.portal.website_domain_view import WebsiteDomainView
from app.portal.website_settings import (
    WebsiteSettings,
    WebsiteSettingsUpdate,
    apply_website_settings_update,
    empty_website_settings,
)
from app.portal.website_settings_facade import WebsiteSettingsFacade
from app.portal.website_settings_store import InMemoryWebsiteSettingsStore
from app.portal.website_settings_view import WebsiteSettingsView
from app.portal.request_principal import ANONYMOUS, RequestPrincipal
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
    "AuthenticationAttempt",
    "AuthenticationFacade",
    "AuthenticationResult",
    "AUTHORIZATION_FUTURE_ROLES",
    "AuthorizationFacade",
    "AuthorizationRequest",
    "AuthorizationResult",
    "Client",
    "ClientQuery",
    "ClientView",
    "DEFAULT_ALLOWED_ROLES",
    "Deployment",
    "DeploymentView",
    "EditSession",
    "EditSessionView",
    "FUTURE_ROLES",
    "InMemoryAuthenticationDirectory",
    "LoginRequest",
    "LoginResponse",
    "OWNERSHIP_FUTURE_ROLES",
    "OrderWebsiteRef",
    "PORTAL_PROFILE",
    "PORTAL_READ_ROUTES",
    "PasswordCredential",
    "PasswordCredentialError",
    "PortalCatalog",
    "PortalCatalogView",
    "PortalReadHandlers",
    "PortalReadRoute",
    "PortalReadService",
    "PortalReadStack",
    "PortalOwnerJourneyState",
    "build_published_owner_journey",
    "ANONYMOUS",
    "AnalyticsFacade",
    "AnalyticsOverview",
    "AnalyticsOverviewView",
    "ChatBotConnection",
    "ChatBotConnectionUpdate",
    "ChatBotFacade",
    "ChatBotView",
    "Product",
    "ProductActivationFacade",
    "ProductCatalogFacade",
    "ProductCatalogItemView",
    "ProductOwnership",
    "ProductOwnershipFacade",
    "MyProductView",
    "RequestPrincipal",
    "register_portal_authentication_middleware",
    "InMemoryAnalyticsStore",
    "InMemoryChatBotStore",
    "InMemoryProductActivationStore",
    "InMemoryProductCatalogStore",
    "InMemoryProductOwnershipStore",
    "InMemoryWebsiteDomainStore",
    "StubChatBotIntegrationAdapter",
    "WebsiteOwnershipBridge",
    "apply_chatbot_connection_update",
    "default_product_catalog",
    "new_product_ownership",
    "empty_analytics_overview",
    "empty_chatbot_connection",
    "empty_website_domain",
    "apply_website_domain_update",
    "Session",
    "SessionCookieFactory",
    "SessionFacade",
    "InMemorySessionStore",
    "Website",
    "WebsiteDashboardFacade",
    "WebsiteDashboardQuery",
    "WebsiteDashboardView",
    "WebsiteDomain",
    "WebsiteDomainFacade",
    "WebsiteDomainUpdate",
    "WebsiteDomainView",
    "WebsiteInvitation",
    "WebsiteOwnership",
    "WebsiteQuery",
    "WebsiteReadContext",
    "WebsiteReadFacade",
    "WebsiteReadQuery",
    "WebsiteSettings",
    "WebsiteSettingsFacade",
    "WebsiteSettingsUpdate",
    "WebsiteSettingsView",
    "WebsiteView",
    "InMemoryWebsiteSettingsStore",
    "account_ids_for_website",
    "apply_website_settings_update",
    "empty_website_settings",
    "activate_token",
    "attach_deployment",
    "authenticate",
    "authorize",
    "authorize_account_for_website",
    "build_website_dashboard_view",
    "close_edit_session",
    "complete_account_activation",
    "compose_portal_read",
    "consume_token",
    "create_primary_password",
    "create_session",
    "empty_authentication_directory",
    "expire_token",
    "grant_website_ownership",
    "is_portal_feature_enabled",
    "is_ready_for_authentication",
    "is_usable",
    "load_portal_catalog_from_factory_sandbox",
    "new_account",
    "new_activation_token",
    "new_asset",
    "new_authorization_request",
    "new_client",
    "new_deployment",
    "new_edit_session",
    "new_website",
    "new_website_invitation",
    "ownership_for_account_website",
    "portal_analytics_router",
    "portal_chatbot_router",
    "portal_dashboard_router",
    "portal_lifecycle_snapshot",
    "portal_login_router",
    "portal_my_products_router",
    "portal_product_activation_router",
    "portal_product_catalog_router",
    "portal_read_router",
    "portal_registration_snapshot",
    "portal_website_domain_router",
    "portal_website_settings_router",
    "refresh_expiry_status",
    "register_portal_analytics",
    "register_portal_chatbot",
    "register_portal_dashboard",
    "register_portal_login",
    "register_portal_my_products",
    "register_portal_product_activation",
    "register_portal_product_catalog",
    "register_portal_read",
    "register_portal_website_domain",
    "register_portal_website_settings",
    "resolve_portal_lifecycle_state",
    "revoke_token",
    "teardown_portal_read",
    "website_for_client",
    "website_ids_for_account",
]
