from fastapi import FastAPI, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import io
import os

from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse
from contextlib import asynccontextmanager
import logging

from app.env_loader import load_local_env

load_local_env()

from app.config import genesis_env, is_production
from app.integration.context import get_integration, reset_integration
from app.integration.runtime import light_system_status, mark_server_started, set_brain_paused
from app.integration.genesis_ai_service import GenesisAIService
from app.integration.genesis_brain.brain import BRAIN_VERSION
from app.integration.genesis_ai_setup_service import GenesisAISetupService
from app.integration.genesis_tts import GenesisTtsService, VOICE_BUILD
from app.integration.knowledge_intake_service import KnowledgeIntakeService
from app.integration.public_chat_attachments import PublicChatAttachmentService
from app.integration.startup_validation import log_startup_report, run_startup_validation
from app.integration.deployment_health import build_health_payload, build_status_payload
from app.security import (
    api_access_denied_response,
    dev_mode_allowed,
    is_internal_api_path,
    is_owner_api_path,
    is_public_api_path,
    local_owner_access_allowed,
    production_api_allowed,
    support_bridge_allowed,
)
from app.security_hardening import (
    apply_security_headers,
    check_rate_limit,
    cors_allow_origins,
    portal_path_should_rate_limit,
    portal_rate_limit_per_min,
    public_rate_limit_per_min,
    rate_limit_key,
    rate_limited_response,
)
from app.integration.owner_auth import owner_access_allowed
from app.integration.support_remote import proxy_support, remote_enabled
from app.schemas import (
    ActivityResponse,
    AssistantRequest,
    AssistantResponse,
    ChatAttachmentResponse,
    ChatSessionCreateRequest,
    ChatSessionCreateResponse,
    ChatSessionDetailResponse,
    ChatSessionListResponse,
    ChatSessionPinRequest,
    ChatSessionRenameRequest,
    ChatSessionSummary,
    ConciergeRequest,
    ConciergeResponse,
    CursorHandoffHistoryResponse,
    CursorHandoffRequest,
    CursorHandoffResponse,
    CursorLastHandoffResponse,
    CursorStatusResponse,
    CursorTask,
    CursorTaskResponse,
    CursorTasksListResponse,
    CursorVerifyResponse,
    ControlResponse,
    CreateTaskRequest,
    DemoRunResponse,
    FactoryImproveRequest,
    FactoryIntentRequest,
    FactoryIntentResponse,
    FactoryIntentsResponse,
    FactoryProduct,
    FactoryProductsResponse,
    SalesCheckoutRequest,
    SalesCheckoutResponse,
    SalesOrderPublicStatus,
    DeploymentPreferenceRequest,
    PublishStatusRequest,
    NextOfferInterestRequest,
    ClientReviewSubmitRequest,
    ClientReviewGuestSubmitRequest,
    ClientReviewSubmitResponse,
    ClientReviewsPublicResponse,
    ClientReviewModerateRequest,
    ClientReviewModerationItem,
    ClientReviewsPendingResponse,
    ClientReviewsOwnerListResponse,
    ClientReviewOwnerPublishRequest,
    PaymentStatusResponse,
    PricingEventRequest,
    PricingEventResponse,
    PathAFunnelDashboard,
    VisualExperiencePreviewResponse,
    EmailStatusResponse,
    SalesOrderActionResponse,
    SalesOrderCreateRequest,
    SalesOrderCreatedResponse,
    SalesOrdersListResponse,
    OrderMaterialUploadResponse,
    OrderInsightsPreviewRequest,
    OrderInsightsPreviewResponse,
    SalesPackage,
    SalesPackagesResponse,
    PathADeliveryMatrixResponse,
    CompanyOverview,
    BusinessHealthDashboard,
    BusinessHealthManualBumpRequest,
    DemoModeRequest,
    DemoModeResponse,
    FinanceCenter,
    GrowthCenter,
    MissionControl,
    SystemCheckResponse,
    ModulesResponse,
    ModuleStatus,
    OwnerDashboard,
    OwnerNotification,
    OwnerNotificationsResponse,
    OpportunityCreateRequest,
    OpportunityCreatedResponse,
    OpportunityDashboard,
    OpportunityListResponse,
    OpportunityRecord,
    OpportunitySourcesResponse,
    OpportunitySource,
    OpportunityType,
    OpportunityStatusOption,
    OpportunityUpdatedResponse,
    OpportunityUpdateRequest,
    LeadIntakeRequest,
    LeadIntakeResponse,
    LeadInboxResponse,
    AssetScannerDashboard,
    AssetNichesResponse,
    AssetScanRequest,
    AssetScanResponse,
    AssetActionResponse,
    AssetTargetsResponse,
    EngineDashboard,
    EngineScanRequest,
    EngineScanResponse,
    EngineScanModeRequest,
    EngineScanModeResponse,
    EngineJunkArchiveResponse,
    EngineNetworkScanRequest,
    EngineNetworkScanResponse,
    EngineGlobalSpiderScanRequest,
    EngineGlobalSpiderScanResponse,
    EngineActivateBusinessRequest,
    ConnectWalletRequest,
    WithdrawRequest,
    WithdrawResponse,
    PaymentSyncResponse,
    EngineTaxSettings,
    EngineAccountingSummary,
    EngineFinancialExportSummary,
    SiteAnalysisResult,
    AcquisitionStudioStatus,
    AcquisitionApprovalQueueResponse,
    AcquisitionApprovalItem,
    AcquisitionPrepareRequest,
    AcquisitionPrepareResponse,
    AcquisitionApproveResponse,
    AcquisitionInteractionRequest,
    AcquisitionEvidenceReport,
    AcquisitionDailyWorklist,
    AcquisitionCatalogResponse,
    PaymentRecordedResponse,
    PaymentStatusResponse,
    PaymentWebhookRequest,
    PublicLaunchChecklist,
    RevenuePaymentResponse,
    QueueStats,
    SystemStatus,
    TaskCreatedResponse,
    TaskItem,
    TasksResponse,
    TtsRequest,
    TimelineResponse,
    AiHubApproveRequest,
    AiHubPlanStep,
    AiHubTask,
    AiHubTaskCreate,
    AiHubTaskResponse,
    AiHubTasksListResponse,
    AiHubVerifyResponse,
    AiProvidersResponse,
    GenesisAISetupRequest,
    GenesisAISetupResponse,
    GenesisAISetupStatus,
    ClientRegisterRequest,
    ClientRegisterConfirmRequest,
    ClientLoginRequest,
    ClientWelcomeAnswerRequest,
    ClientMergeVisitorRequest,
    ClientBotCreateRequest,
    ClientBotUpdateRequest,
    ClientBotTelegramConnectRequest,
    ClientBotDisconnectRequest,
    ClientBotMetaOAuthStartRequest,
    ClientBotOrderDraftRequest,
    DevBuildEntry,
    DevFileEntry,
    DevProject,
    DevSuggestion,
    DevWorkspaceSnapshot,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    mark_server_started()
    if GenesisAIService([]).llm_configured():
        logging.getLogger("genesis").info("Genesis Brain: cloud workforce employee(s) active")
    else:
        logging.getLogger("genesis").info(
            "Genesis Brain: Local Genesis active — connect Groq/Gemini on /setup to expand workforce"
        )

    from pathlib import Path

    backend_dir = Path(__file__).resolve().parents[1]
    repo_root = backend_dir.parent.parent
    mem = os.getenv("GENESIS_MEMORY_DIR", "").strip()
    memory_dir = Path(mem).expanduser() if mem else backend_dir / "memory"
    report = run_startup_validation(memory_dir=memory_dir, repo_root=repo_root)
    app.state.startup_report = report
    log_startup_report(report)
    logging.getLogger("genesis").info("Genesis env=%s", genesis_env())

    def _warm_integration() -> None:
        try:
            ctx = get_integration()
            set_brain_paused(ctx.adapter.is_paused)
            owner_name = ctx.owner.owner_name()
            ctx.micro_farm.warm_dashboard_cache(owner_name)
        except Exception:
            logging.getLogger("genesis").exception("startup warm failed")

    import threading

    threading.Thread(target=_warm_integration, daemon=True, name="genesis-warm").start()

    # Country Desk: resume auto-send after launcher restart; otherwise stay stopped until Пуск.
    try:
        from app.integration.outreach_ceo_prefs import load_prefs, save_prefs
        from app.integration.outreach_runner_service import OutreachRunnerService

        prefs = load_prefs(memory_dir)
        runner = OutreachRunnerService(memory_dir)
        if prefs.get("auto_send"):
            save_prefs(memory_dir, auto_refresh=True)
            runner.start()
            logging.getLogger("genesis").info(
                "Country Desk resumed on startup (Автоотправка was on)"
            )
        else:
            save_prefs(memory_dir, auto_refresh=False)
            runner.stop()
            logging.getLogger("genesis").info(
                "Country Desk market forced STOP on startup (Пуск only)"
            )
    except Exception:
        logging.getLogger("genesis").exception("market runner startup preference failed")

    def _country_desk_bg_ticks() -> None:
        """Send/hunt without CEO keeping /acquisition open (browser tick is optional)."""
        import time

        log = logging.getLogger("genesis")
        while True:
            time.sleep(45)
            try:
                from app.integration.outreach_ceo_prefs import outreach_send_allowed
                from app.integration.context import get_integration

                ctx = get_integration()
                st = ctx.acquisition.runner_status()
                if not st.get("running"):
                    # Auto-heal: prefs say send, but runner died / was never started
                    if outreach_send_allowed(memory_dir):
                        ctx.acquisition._get_runner().start()
                    continue
                ctx.acquisition.runner_tick()
            except Exception:
                log.exception("country desk background tick failed")

    threading.Thread(
        target=_country_desk_bg_ticks, daemon=True, name="genesis-country-desk"
    ).start()

    yield


app = FastAPI(
    title="Virtus Core API",
    description="Integration Layer v0.1 — live Brain data",
    version="0.2.0",
    lifespan=lifespan,
    docs_url=None if is_production() else "/docs",
    redoc_url=None if is_production() else "/redoc",
    openapi_url=None if is_production() else "/openapi.json",
)

# Always keep local Mission Control origins — empty/override GENESIS_CORS_ORIGINS
# must not break Genesis.exe desk (browser → :8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins(extra_csv=os.getenv("GENESIS_CORS_ORIGINS", "")),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.webhooks.stripe import router as stripe_webhook_router

app.include_router(stripe_webhook_router)
from app.api.webhooks.resend_inbound import router as resend_inbound_webhook_router

app.include_router(resend_inbound_webhook_router)

# Commercial API Gateway v0 — sell Virtus audit/leads (additive; no farm finance changes)
from app.commercial_api.router import router as commercial_api_router

app.include_router(commercial_api_router)

# Virtus Office Job Engine Stage 1 — lifecycle + ingest (pipeline_live=False)
from app.integration.virtus_office.router import router as virtus_office_router

app.include_router(virtus_office_router)


# R3.8.2 — controlled Portal registration (no-op while feature_enabled=False)
from app.portal.portal_registration import register_portal_read

register_portal_read(app)

# R3.11.1 — Dashboard read endpoint (Facade → WebsiteDashboardView; Auth stub)
from app.portal.portal_dashboard_registration import register_portal_dashboard

register_portal_dashboard(app)

# R5.1 — Website Settings Basic Profile (reference ModuleFacade)
from app.portal.portal_website_settings_registration import (
    register_portal_website_settings,
)

register_portal_website_settings(app)

# R5.2 — Analytics Overview (read-only ModuleFacade)
from app.portal.portal_analytics_registration import register_portal_analytics

register_portal_analytics(app)

# R5.3 — Website Domain Management (resource-state ModuleFacade)
from app.portal.portal_website_domain_registration import (
    register_portal_website_domain,
)

register_portal_website_domain(app)

# R5.4 — ChatBot Integration (integration ModuleFacade · stub adapter)
from app.portal.portal_chatbot_registration import register_portal_chatbot

register_portal_chatbot(app)

# Mission 6.1 — Product Catalog (platform-level · independent of Website)
from app.portal.portal_product_catalog_registration import (
    register_portal_product_catalog,
)
from app.portal.product_catalog_store import InMemoryProductCatalogStore

_portal_product_catalog_store = InMemoryProductCatalogStore()
register_portal_product_catalog(app, store=_portal_product_catalog_store)

# Mission 6.2 / 6.3 — shared ProductOwnership + Activation stores
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_activation_store import InMemoryProductActivationStore
from app.portal.product_ownership_store import InMemoryProductOwnershipStore

_portal_product_ownership_store = InMemoryProductOwnershipStore()
_portal_product_activation_store = InMemoryProductActivationStore()
_portal_product_activation_facade = ProductActivationFacade.from_parts(
    catalog=_portal_product_catalog_store,
    ownerships=_portal_product_ownership_store,
    activations=_portal_product_activation_store,
)

# Mission 6.2 — My Products (ProductOwnership + WebsiteOwnershipBridge)
from app.portal.portal_my_products_registration import register_portal_my_products

register_portal_my_products(
    app,
    ownership_store=_portal_product_ownership_store,
    catalog=_portal_product_catalog_store,
)

# Mission 6.3 — Product Activation → native ProductOwnership
from app.portal.portal_product_activation_registration import (
    register_portal_product_activation,
)

register_portal_product_activation(
    app,
    ownership_store=_portal_product_ownership_store,
    catalog=_portal_product_catalog_store,
    activation_store=_portal_product_activation_store,
    facade=_portal_product_activation_facade,
)

# Commercial Platform 6.5 — Licenses (entitlement → redeem → Activation)
from app.portal.license_store import InMemoryLicenseStore
from app.portal.portal_license_registration import register_portal_licenses

_portal_license_store = InMemoryLicenseStore()
_portal_license_facade = register_portal_licenses(
    app,
    activation=_portal_product_activation_facade,
    catalog=_portal_product_catalog_store,
    license_store=_portal_license_store,
)

# Commercial Platform 6.6 — Billing (financial ledger only)
from app.portal.billing_store import InMemoryBillingStore
from app.portal.portal_billing_registration import register_portal_billing

_portal_billing_store = InMemoryBillingStore()
_portal_billing_facade = register_portal_billing(
    app,
    store=_portal_billing_store,
)

# Commercial Platform 6.4 — Purchases → Billing → License → Activation
from app.portal.portal_purchase_registration import register_portal_purchases

register_portal_purchases(
    app,
    licenses=_portal_license_facade,
    billing=_portal_billing_facade,
    catalog=_portal_product_catalog_store,
)

# Business Product BP1.1 — ChatBot Business Profile & Industry Template
from app.portal.chatbot_business_profile_store import (
    InMemoryChatBotBusinessProfileStore,
)
from app.portal.industry_template import InMemoryIndustryTemplateStore
from app.portal.portal_chatbot_product_registration import (
    register_portal_chatbot_product,
)

_portal_chatbot_profile_store = InMemoryChatBotBusinessProfileStore()
_portal_chatbot_template_store = InMemoryIndustryTemplateStore()
register_portal_chatbot_product(
    app,
    profile_store=_portal_chatbot_profile_store,
    template_store=_portal_chatbot_template_store,
)

# Business Product BP1.2 — Business Knowledge (facts only)
from app.portal.business_knowledge_store import InMemoryBusinessKnowledgeStore
from app.portal.portal_chatbot_knowledge_registration import (
    register_portal_chatbot_knowledge,
)

_portal_chatbot_knowledge_store = InMemoryBusinessKnowledgeStore()
_portal_chatbot_knowledge_facade = register_portal_chatbot_knowledge(
    app,
    profiles=_portal_chatbot_profile_store,
    knowledge_store=_portal_chatbot_knowledge_store,
)

# Business Product BP1.3 — Channel Connections (stub registry)
from app.portal.channel_connection_store import InMemoryChannelConnectionStore
from app.portal.portal_chatbot_channels_registration import (
    register_portal_chatbot_channels,
)

_portal_chatbot_channel_store = InMemoryChannelConnectionStore()
register_portal_chatbot_channels(
    app,
    profiles=_portal_chatbot_profile_store,
    channel_store=_portal_chatbot_channel_store,
)

# AI Platform AP1.1 — Provider Layer (stub LLM abstraction)
from app.portal.ai_provider_store import InMemoryAIProviderStore
from app.portal.portal_chatbot_providers_registration import (
    register_portal_chatbot_providers,
)

_portal_ai_provider_store = InMemoryAIProviderStore()
_portal_ai_provider_facade = register_portal_chatbot_providers(
    app,
    store=_portal_ai_provider_store,
    seed_stubs=True,
)

# Business Product BP1.4 — Conversation Engine (context → Provider Protocol)
from app.portal.portal_chatbot_conversations_registration import (
    register_portal_chatbot_conversations,
)

_portal_chatbot_conversation_facade = register_portal_chatbot_conversations(
    app,
    profiles=_portal_chatbot_profile_store,
    knowledge=_portal_chatbot_knowledge_store,
    channels=_portal_chatbot_channel_store,
    templates=_portal_chatbot_template_store,
    providers=_portal_ai_provider_facade.manager,
)

# PT4 — Business Actions (explicit operator approval)
from app.portal.portal_chatbot_actions_registration import (
    register_portal_chatbot_actions,
)

register_portal_chatbot_actions(
    app,
    conversations=_portal_chatbot_conversation_facade,
    knowledge=_portal_chatbot_knowledge_facade,
)

from app.portal.portal_chatbot_ops_registration import register_portal_chatbot_ops

register_portal_chatbot_ops(app)

# R4.1 / R4.2 — HTTP Login + Session cookie
from app.portal.portal_login_registration import register_portal_login

register_portal_login(app)

# R4.3 — Authentication Middleware (identity only; never 401/403)
from app.portal.portal_authentication_middleware import (
    register_portal_authentication_middleware,
)

register_portal_authentication_middleware(app)

# OR1 — Request correlation for /portal/*
from app.portal.portal_operational_middleware import (
    register_portal_operational_middleware,
)

register_portal_operational_middleware(app)

# Research Visual Experience stills / demos (Path A preview — read-only assets)
from pathlib import Path as _Path

from fastapi.staticfiles import StaticFiles as _StaticFiles

_research_3d_root = _Path(__file__).resolve().parents[1] / "_research_3d"
if _research_3d_root.is_dir():
    app.mount(
        "/research-3d",
        _StaticFiles(directory=str(_research_3d_root)),
        name="research_3d",
    )


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """S1.2 — baseline hardening headers on every API response."""
    response = await call_next(request)
    return apply_security_headers(response)


@app.middleware("http")
async def rate_limit_public_and_portal(request: Request, call_next):
    """S1.2 — DoS guard: public chat (prod) + portal (always, per IP)."""
    from collections import defaultdict

    path = request.url.path
    if not hasattr(app.state, "_rate_buckets"):
        app.state._rate_buckets = defaultdict(list)
    if not hasattr(app.state, "_portal_rate_buckets"):
        app.state._portal_rate_buckets = defaultdict(list)

    key = rate_limit_key(request)
    if is_production() and path.startswith("/api/public/"):
        if not check_rate_limit(
            app.state._rate_buckets,
            key=key,
            limit=public_rate_limit_per_min(),
            window_sec=60.0,
        ):
            return apply_security_headers(rate_limited_response())
    if portal_path_should_rate_limit(path):
        if not check_rate_limit(
            app.state._portal_rate_buckets,
            key=key,
            limit=portal_rate_limit_per_min(),
            window_sec=60.0,
        ):
            return apply_security_headers(rate_limited_response())
    return await call_next(request)


@app.middleware("http")
async def guard_internal_routes(request: Request, call_next):
    path = request.url.path
    method = request.method
    if is_production():
        if path.startswith("/api/support") and support_bridge_allowed(request):
            return await call_next(request)
        # Public storefront / webhooks only — unless authenticated owner (remote CEO).
        if is_owner_api_path(path):
            if owner_access_allowed(request):
                return await call_next(request)
            return JSONResponse(
                status_code=401,
                content={"detail": "Owner authentication required"},
            )
        if is_internal_api_path(path) and not is_public_api_path(path, method):
            if owner_access_allowed(request):
                return await call_next(request)
            return JSONResponse(
                status_code=403,
                content=api_access_denied_response(path, method),
            )
        if not production_api_allowed(path, method):
            return JSONResponse(
                status_code=403,
                content=api_access_denied_response(path, method),
            )
    elif is_internal_api_path(path) and not (
        owner_access_allowed(request)
        if is_owner_api_path(path)
        else (
            owner_access_allowed(request)
            if (
                (request.headers.get("x-forwarded-for") or "").strip()
                or (request.headers.get("x-real-ip") or "").strip()
            )
            else local_owner_access_allowed(request)
        )
    ):
        status = 401 if is_owner_api_path(path) else 403
        return JSONResponse(
            status_code=status,
            content=(
                {"detail": "Unauthorized"}
                if status == 401
                else api_access_denied_response(path, method)
            ),
        )
    return await call_next(request)


@app.middleware("http")
async def support_inbox_remote_proxy(request: Request, call_next):
    """Local Genesis.exe desk → Railway Support Inbox (shared volume of truth)."""
    path = request.url.path
    if not (path.startswith("/api/support") and not is_production()):
        return await call_next(request)

    load_local_env()
    origin = (request.headers.get("origin") or "").strip()
    allowed = {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        *[o.strip() for o in os.getenv("GENESIS_CORS_ORIGINS", "").split(",") if o.strip()],
    }

    def with_cors(response: JSONResponse | Response) -> Response:
        if origin in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*, Authorization, Content-Type, X-Support-Bridge"
            response.headers["Vary"] = "Origin"
        return response

    # Early proxy return bypasses CORSMiddleware — answer preflight here.
    if request.method == "OPTIONS":
        return with_cors(Response(status_code=204))

    # Unsubscribe must succeed for Country Desk even if Railway is behind / 403 / 404.
    is_unsub = path.endswith("/unsubscribe") or path.endswith("/do-not-email")
    if is_unsub and request.method == "POST":
        import json as _json
        import re as _re

        body_bytes = await request.body()
        email = ""
        tid = ""
        try:
            payload = _json.loads(body_bytes.decode("utf-8") or "{}")
            if isinstance(payload, dict):
                email = str(payload.get("email") or "").strip()
        except Exception:
            payload = {}
        if "/threads/" in path and path.endswith("/unsubscribe"):
            tid = path.rsplit("/threads/", 1)[-1].split("/", 1)[0]
        # Pull email from local thread when UI body omitted it
        if (not email or "@" not in email) and tid:
            try:
                thr = _ctx().support.get_thread(tid)
                if thr:
                    email = str(thr.get("from") or "").strip()
            except Exception:
                pass
        m = _re.search(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", email or "", _re.I)
        if m:
            email = m.group(0)

        local_out: dict | None = None
        if email and "@" in email:
            try:
                local_out = _ctx().support.unsubscribe_email(
                    email,
                    thread_id=tid,
                    source="support_ui",
                )
            except ValueError:
                local_out = None

        # Never proxy unsubscribe to Railway — old remote returns bare "Not Found"
        # and blocks the CEO desk. Local Do Not Send is the source of truth.
        if local_out:
            return with_cors(JSONResponse(local_out))
        async def _receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        return await call_next(Request(request.scope, _receive))

    if remote_enabled():
        from app.integration.support_remote import remote_response_is_unavailable
        from fastapi import HTTPException as _HTTPException

        try:
            proxied = await proxy_support(request, path)
        except _HTTPException as exc:
            # Remote unreachable → local desk still works with .env.local keys.
            if int(getattr(exc, "status_code", 0) or 0) in (502, 503, 504):
                proxied = None
            else:
                raise
        if proxied is not None and not remote_response_is_unavailable(proxied):
            return with_cors(proxied)
        # Railway 404 / gateway down → local Support handlers (keys from .env.local).
    return await call_next(request)


def _ctx():
    return get_integration()


def _memory_dir():
    return _ctx().adapter.brain.config.memory_dir


def _ai_hub():
    from app.integration.ai_hub.ai_hub_service import AiHubService

    cursor = _ctx().cursor_handoff
    return AiHubService(cursor._memory, cursor)


def _dev_workspace():
    from app.integration.ai_hub.dev_workspace_service import DevWorkspaceService

    hub = _ai_hub()
    return DevWorkspaceService(_ctx().cursor_handoff, hub)


@app.get("/health")
def health_check() -> dict:
    return build_health_payload()


@app.get("/status")
def deployment_status() -> dict:
    return build_status_payload(memory_dir=_memory_dir())


@app.get("/api/status", response_model=SystemStatus)
def get_status() -> SystemStatus:
    return SystemStatus(**light_system_status())


@app.get("/api/workspace/health")
def workspace_layer_health(request: Request) -> dict:
    """Foundation F4 — workspace layer stub (disabled until FeatureRegistry enables workspace)."""
    from app.integration.feature_registry import FeatureRegistry

    if not owner_access_allowed(request):
        raise HTTPException(status_code=403, detail="Workspace layer requires owner access")
    enabled = FeatureRegistry(memory_dir=_memory_dir()).is_enabled("workspace")
    return {
        "layer": "workspace",
        "enabled": enabled,
        "status": "ready" if enabled else "stub",
    }


@app.get("/api/project/health")
def project_layer_health(request: Request) -> dict:
    """Foundation F4 — project layer stub (under workspace; disabled by default)."""
    from app.integration.feature_registry import FeatureRegistry

    if not owner_access_allowed(request):
        raise HTTPException(status_code=403, detail="Project layer requires owner access")
    ws = FeatureRegistry(memory_dir=_memory_dir()).is_enabled("workspace")
    return {
        "layer": "project",
        "enabled": ws,
        "status": "stub",
        "note": "Projects activate with Customer Workspace",
    }


@app.get("/api/owner/dashboard", response_model=OwnerDashboard)
def get_owner_dashboard() -> OwnerDashboard:
    data = _ctx().owner.dashboard()
    return OwnerDashboard(**data)


@app.get("/api/owner/finance", response_model=FinanceCenter)
def get_finance_center() -> FinanceCenter:
    ctx = _ctx()
    dash = ctx.owner.dashboard()
    opps = ctx.opportunity.list_opportunities(source_id="asset_scan", limit=1000)
    data = ctx.finance.finance_center(
        dash["owner_name"],
        dash["greeting"],
        business_mode=ctx.business_mode,
        opportunities=opps,
    )
    data["global_revenue"] = ctx.finance.global_revenue_report(opps)
    return FinanceCenter(**data)


@app.post("/api/owner/finance/reconcile")
def reconcile_finance() -> dict:
    ctx = _ctx()
    opps = ctx.opportunity.list_opportunities(source_id="asset_scan", limit=1000)
    if ctx.business_mode.is_live():
        try:
            ctx.monetization_engine.sync_payment_providers()
        except Exception:
            pass
    return ctx.finance.reconcile(business_mode=ctx.business_mode, opportunities=opps)


@app.get("/api/owner/finance/global-revenue")
def get_global_revenue_report() -> dict:
    ctx = _ctx()
    opps = ctx.opportunity.list_opportunities(source_id="asset_scan", limit=1000)
    return ctx.finance.global_revenue_report(opps)


@app.get("/api/owner/finance/ops")
def get_finance_ops_center() -> dict:
    """Finance & Tax Center — income, billing monitor, pay links, tax export meta."""
    from app.integration.finance_ops_service import FinanceOpsService

    ctx = _ctx()
    return FinanceOpsService(ctx.finance._memory).dashboard()  # noqa: SLF001


@app.post("/api/owner/finance/ops/documents")
def add_finance_ops_document(payload: dict) -> dict:
    from app.integration.finance_ops_service import FinanceOpsService

    ctx = _ctx()
    return FinanceOpsService(ctx.finance._memory).add_document(payload)  # noqa: SLF001


@app.get("/api/owner/finance/tax-export")
def download_tax_export(year: int | None = None):
    from fastapi.responses import Response

    from app.integration.finance_ops_service import FinanceOpsService

    ctx = _ctx()
    raw, filename = FinanceOpsService(ctx.finance._memory).build_tax_export_zip(year=year)  # noqa: SLF001
    return Response(
        content=raw,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/owner/finance/finanzamt-report.html", response_class=HTMLResponse)
def download_finanzamt_report_html(year: int | None = None) -> HTMLResponse:
    """Printable Finanzamt work-aid — browser Print → PDF."""
    from datetime import datetime, timezone

    from app.integration.finance_ops_service import FinanceOpsService

    ctx = _ctx()
    html = FinanceOpsService(ctx.finance._memory).build_finanzamt_html(year=year)  # noqa: SLF001
    y = year or datetime.now(timezone.utc).year
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f'inline; filename="Finanzamt_Bericht_{y}.html"'},
    )


@app.get("/api/owner/company", response_model=CompanyOverview)
def get_company_overview() -> CompanyOverview:
    data = _ctx().company.overview()
    return CompanyOverview(**data)


def _business_health():
    from app.integration.business_health_service import BusinessHealthService

    ctx = _ctx()
    return BusinessHealthService(ctx.opportunity.memory_dir, ctx.opportunity)


@app.get("/api/owner/business-health", response_model=BusinessHealthDashboard)
def get_business_health() -> BusinessHealthDashboard:
    data = _business_health().dashboard()
    data["ceo_outbox"] = _ctx().acquisition.ceo_outbox_summary()
    monitor = _ctx().micro_farm.money_monitor_panel(lite=True)
    data["money_monitor"] = monitor
    data["mission2_kpi"] = monitor.get("mission2_kpi")
    from app.integration.mission_proof_service import build_mission_proof

    ctx = _ctx()
    fin = ctx.finance
    inputs = fin.real_money_inputs()
    data["mission_proof"] = build_mission_proof(
        ctx.opportunity.list_opportunities(limit=5000),
        settlements=inputs.get("settlements"),
        memory_dir=ctx.opportunity.memory_dir,
    )
    from app.integration.revenue_engines_service import build_revenue_engines

    data["revenue_engines"] = build_revenue_engines(
        memory_dir=ctx.opportunity.memory_dir,
        finance_snapshot=inputs.get("finance_snapshot") or {},
        settlements=inputs.get("settlements"),
        farm_state=ctx.micro_farm._load_state(),  # noqa: SLF001
    )
    return BusinessHealthDashboard(**data)


@app.get("/api/owner/mission2-kpi")
def get_mission2_kpi() -> dict:
    from app.integration.mission2_kpi_service import build_mission2_kpi
    from app.integration.finance_service import FinanceService

    ctx = _ctx()
    opps = ctx.opportunity.list_opportunities(limit=5000)
    pending = sum(1 for r in opps if r.get("outreach_status") == "pending_approval")
    state = ctx.micro_farm._load_state()  # noqa: SLF001
    fin = FinanceService(ctx.opportunity.memory_dir)
    inputs = fin.real_money_inputs()
    from app.integration.real_money_service import build_real_money_tiers

    tiers = build_real_money_tiers(
        finance_snapshot=inputs["finance_snapshot"],
        transactions=inputs["transactions"],
        pending_payments=inputs["pending_payments"],
        payout_history=inputs["payout_history"],
        payment_connected=inputs["payment_connected"],
        demo_mode=inputs["demo_mode"],
        farm_training_eur=float(state.get("total_earned_eur") or 0),
        opportunities=opps,
    )
    return build_mission2_kpi(
        opps,
        received_eur=float(tiers.get("paid_by_client", tiers["received"])["amount_eur"]),
        training_eur=float(state.get("total_earned_eur") or 0),
        outbox_pending=pending,
    )


@app.get("/api/owner/stripe-setup")
def get_stripe_setup(request: Request) -> dict:
    base = str(request.base_url).rstrip("/")
    return _ctx().monetization_engine._checkout.stripe_setup_status(public_api_base=base)  # noqa: SLF001


@app.get("/api/owner/gmail", response_class=HTMLResponse)
def owner_gmail_center(request: Request) -> str:
    """One-time Gmail OAuth desk — localhost only (owner middleware)."""
    import html as html_lib

    from app.integration import gmail_mail_service as gmail

    base = str(request.base_url).rstrip("/")
    st = gmail.status(public_api_base=base)
    redirect = html_lib.escape(str(st.get("redirect_uri") or ""))
    sender = html_lib.escape(str(st.get("sender") or "—"))
    ready = "✅" if st.get("send_ready") else "❌"
    oauth = "✅" if st.get("oauth_client_ready") else "❌"
    has_rt = "✅" if st.get("has_refresh_token") else "❌"
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"/><title>Gmail Mail — Virtus Core</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:640px;margin:40px auto;padding:0 16px;color:#111;background:#fafafa}}
code,pre{{background:#eee;padding:2px 6px;border-radius:4px}}
pre{{padding:12px;overflow:auto;white-space:pre-wrap}}
a.btn{{display:inline-block;margin-top:16px;padding:12px 18px;background:#111;color:#fff;text-decoration:none;border-radius:8px}}
.muted{{color:#666;font-size:14px;line-height:1.5}}
</style></head><body>
<h1>Gmail API — авторизация</h1>
<p class="muted">Один раз: <strong>Connect Gmail</strong> → токен сам пишется в
<code>.env.local</code> → перезапуск Genesis. Resend основной; Gmail — запас при 429.</p>
<ul>
<li>OAuth client (ID+Secret): {oauth}</li>
<li>Refresh token в .env: {has_rt}</li>
<li>Готов слать: {ready}</li>
<li>Отправитель: <code>{sender}</code></li>
<li>Redirect URI (добавьте в Google Cloud → OAuth client):<br/><code>{redirect}</code></li>
</ul>
<a class="btn" href="/api/owner/gmail/oauth/start" target="_top" rel="noopener">Connect Gmail</a>
<a class="btn" href="/api/owner/gmail/test-send" target="_blank" rel="noopener" style="margin-left:8px;background:#0a7">Тестовая отправка</a>
<p class="muted" style="margin-top:24px"><strong>Важно:</strong> открывайте эту страницу в обычной вкладке браузера
(<code>http://localhost:8000/api/owner/gmail</code>), не внутри Mission Control — Google блокирует вход во iframe (белый экран).</p>
<p class="muted">Scope: <code>gmail.send</code> · только localhost CEO desk.
Если старый токен скомпрометирован: отзовите доступ на
<a href="https://myaccount.google.com/permissions" target="_blank" rel="noreferrer">myaccount.google.com/permissions</a>,
затем Connect снова.</p>
</body></html>"""


@app.get("/api/owner/gmail/status")
def owner_gmail_status(request: Request) -> dict:
    from app.integration import gmail_mail_service as gmail

    return gmail.status(public_api_base=str(request.base_url).rstrip("/"))


@app.get("/api/owner/gmail/oauth/start", response_class=HTMLResponse)
def owner_gmail_oauth_start(request: Request):
    """Break out of Mission Control iframe — Google OAuth cannot render inside frames."""
    import html as html_lib
    import json

    from fastapi.responses import RedirectResponse

    from app.integration import gmail_mail_service as gmail

    if not gmail.oauth_client_ready():
        raise HTTPException(
            status_code=400,
            detail="Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env.local",
        )
    base = str(request.base_url).rstrip("/")
    redirect_uri = gmail.default_redirect_uri(base)
    state = gmail.create_oauth_state()
    url = gmail.authorization_url(redirect_uri=redirect_uri, state=state)
    # Prefer HTML breakout: empty 302 inside iframe = white screen (X-Frame-Options: DENY).
    accept = (request.headers.get("accept") or "").lower()
    if "text/html" in accept or "mozilla" in (request.headers.get("user-agent") or "").lower():
        safe = html_lib.escape(url, quote=True)
        js_url = json.dumps(url)
        return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"/>
<meta http-equiv="refresh" content="0;url={safe}"/>
<title>Redirect to Google…</title></head>
<body style="font-family:system-ui;padding:2rem;background:#111;color:#eee">
<p>Переход к Google… Если экран пустой — откройте ссылку в новой вкладке:</p>
<p><a href="{safe}" target="_top" style="color:#8cf">Continue to Google</a></p>
<script>
try {{ window.top.location.href = {js_url}; }}
catch (e) {{ window.location.href = {js_url}; }}
</script>
</body></html>"""
    return RedirectResponse(url, status_code=302)


@app.get("/api/owner/gmail/oauth/callback", response_class=HTMLResponse)
def owner_gmail_oauth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> str:
    import html as html_lib

    from app.integration import gmail_mail_service as gmail

    if error:
        return (
            "<!DOCTYPE html><html><body><h1>Gmail OAuth error</h1>"
            f"<pre>{html_lib.escape(error)}</pre>"
            '<p><a href="/api/owner/gmail">Назад</a></p></body></html>'
        )
    if not state or not gmail.consume_oauth_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    base = str(request.base_url).rstrip("/")
    redirect_uri = gmail.default_redirect_uri(base)
    result = gmail.exchange_code(code=code, redirect_uri=redirect_uri)
    if not result.get("ok"):
        detail = html_lib.escape(str(result.get("detail") or result.get("reason") or ""))
        return (
            "<!DOCTYPE html><html><body><h1>Token exchange failed</h1>"
            f"<pre>{detail}</pre>"
            '<p><a href="/api/owner/gmail">Повторить</a></p></body></html>'
        )
    refresh = result.get("refresh_token")
    if not refresh:
        hint = html_lib.escape(str(result.get("hint") or "No refresh_token returned"))
        return (
            "<!DOCTYPE html><html><body><h1>Нет refresh_token</h1>"
            f"<p>{hint}</p>"
            '<p><a href="/api/owner/gmail">Connect снова</a></p></body></html>'
        )
    saved = gmail.persist_refresh_token(str(refresh))
    saved_ok = bool(saved.get("ok"))
    ready = "✅" if gmail.send_ready() else "❌"
    safe = html_lib.escape(str(refresh))
    if saved_ok:
        body_main = (
            f"<p class=\"ok\">Токен записан в <code>dashboard/backend/.env.local</code>. "
            f"send_ready={ready}. Перезапустите Genesis.exe один раз.</p>"
        )
    else:
        body_main = (
            "<p class=\"warn\">Автозапись не удалась — скопируйте вручную:</p>"
            f"<pre>GMAIL_REFRESH_TOKEN={safe}</pre>"
        )
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"/><title>Gmail Refresh Token</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 16px}}
pre{{background:#111;color:#9f9;padding:16px;border-radius:8px;overflow:auto;word-break:break-all}}
.warn{{color:#a60;font-size:14px}}
.ok{{color:#060;font-size:14px}}
</style></head><body>
<h1>Gmail авторизация успешна</h1>
{body_main}
<p class="warn">Не коммитьте .env.local и не отправляйте токен в чат.</p>
<p>Проверка: <a href="/api/owner/gmail/status">/api/owner/gmail/status</a></p>
<p><a class="btn" href="/api/owner/gmail/test-send">Тестовая отправка</a></p>
</body></html>"""


@app.post("/api/owner/gmail/test-send")
@app.get("/api/owner/gmail/test-send")
def owner_gmail_test_send(request: Request, to: str | None = None) -> dict:
    """CEO desk: refresh access token + send one short test mail."""
    from app.integration import gmail_mail_service as gmail

    if not gmail.send_ready():
        return {
            "ok": False,
            "reason": "gmail_not_ready",
            "status": gmail.status(public_api_base=str(request.base_url).rstrip("/")),
            "fix": "Open /api/owner/gmail → Connect Gmail, then retry.",
        }
    refreshed = gmail.access_token_from_refresh()
    if not refreshed.get("ok"):
        return {
            "ok": False,
            "reason": refreshed.get("reason") or "refresh_failed",
            "detail": refreshed.get("detail"),
            "fix": "Revoke app at https://myaccount.google.com/permissions then Connect again.",
        }
    target = (to or str(gmail.status().get("sender") or "")).strip()
    if not target:
        return {"ok": False, "reason": "no_sender"}
    sent = gmail.send_email(
        to=target,
        subject="Virtus Core — Gmail test OK",
        text=(
            "Gmail OAuth refresh + send works.\n"
            "Lead outreach failover can use Gmail again.\n"
        ),
        html=(
            "<p>Gmail OAuth refresh + send works.</p>"
            "<p>Lead outreach failover can use Gmail again.</p>"
        ),
    )
    return {
        "ok": bool(sent.get("ok")),
        "refresh_ok": True,
        "send": {k: v for k, v in sent.items() if k != "raw"},
        "to": target,
    }


@app.post("/api/acquisition/auto-prepare-discovery")
def acquisition_auto_prepare_discovery(body: dict | None = None) -> dict:
    body = body or {}
    limit = int(body.get("limit") or 3)
    return _ctx().acquisition.auto_prepare_discovery_leads(
        limit=limit,
        min_score=int(body.get("min_score") or 50),
        min_win_pct=int(body.get("min_win_pct") or 55),
    )


@app.post("/api/acquisition/approve-batch")
def acquisition_approve_batch(body: dict | None = None) -> dict:
    body = body or {}
    ids = body.get("opportunity_ids")
    if ids is not None and not isinstance(ids, list):
        raise HTTPException(status_code=400, detail="opportunity_ids must be a list")
    return _ctx().acquisition.approve_batch(
        opportunity_ids=ids,
        limit=int(body.get("limit") or 5),
    )


@app.post("/api/owner/business-health/manual", response_model=BusinessHealthDashboard)
def bump_business_health_manual(body: BusinessHealthManualBumpRequest) -> BusinessHealthDashboard:
    try:
        data = _business_health().bump_manual(body.field, body.delta)
    except ValueError as exc:
        if str(exc) == "invalid_field":
            raise HTTPException(status_code=400, detail="invalid_field") from exc
        raise
    return BusinessHealthDashboard(**data)


@app.get("/api/owner/system-check", response_model=SystemCheckResponse)
def get_system_check() -> SystemCheckResponse:
    data = _ctx().system_check.run()
    return SystemCheckResponse(**data)


@app.get("/api/owner/income-engine")
def owner_income_engine() -> dict:
    """Owner-only Income Engine — Opportunity Optimizer (not a commercial product)."""
    return _ctx().micro_farm.income_engine_v1()


@app.get("/api/owner/apify/status")
def owner_apify_status() -> dict:
    """Owner-only Apify credentials + Actor product line (never exposed to clients)."""
    from app.integration.apify_service import owner_apify_panel

    return owner_apify_panel()


@app.post("/api/owner/income-engine/start")
def owner_income_engine_start(body: dict) -> dict:
    """START INCOME ENGINE — swarm mission (expected ROI, not guaranteed profit)."""
    bal = float((body or {}).get("balance_eur") or 0)
    limit_raw = (body or {}).get("auto_approve_limit_eur")
    limit = float(limit_raw) if limit_raw is not None else None
    simulate_fast = bool((body or {}).get("simulate_fast", True))
    return _ctx().micro_farm.income_engine_v1_start(
        balance_eur=bal,
        auto_approve_limit_eur=limit,
        simulate_fast=simulate_fast,
    )


@app.post("/api/owner/income-engine/approve")
def owner_income_engine_approve(body: dict) -> dict:
    """Approve once | batch_limit (all deals up to auto-approve €X)."""
    oid = str((body or {}).get("opportunity_id") or "").strip()
    if not oid:
        raise HTTPException(status_code=400, detail="opportunity_id_required")
    mode = str((body or {}).get("mode") or "once").strip() or "once"
    note = str((body or {}).get("note") or "")
    return _ctx().micro_farm.income_engine_v1_approve(oid, mode=mode, note=note)


@app.post("/api/owner/income-engine/reject")
def owner_income_engine_reject(body: dict) -> dict:
    oid = str((body or {}).get("opportunity_id") or "").strip()
    if not oid:
        raise HTTPException(status_code=400, detail="opportunity_id_required")
    note = str((body or {}).get("note") or "")
    return _ctx().micro_farm.income_engine_v1_reject(oid, note=note)


@app.post("/api/owner/income-engine/auto-limit")
def owner_income_engine_auto_limit(body: dict) -> dict:
    limit = float((body or {}).get("auto_approve_limit_eur") or 0)
    return _ctx().micro_farm.income_engine_v1_set_auto_limit(limit)


@app.post("/api/owner/income-engine/reinvest")
def owner_income_engine_reinvest(body: dict) -> dict:
    enabled = bool((body or {}).get("enabled"))
    return _ctx().micro_farm.income_engine_v1_set_reinvest(enabled)


@app.post("/api/owner/income-engine/record-outcome")
def owner_income_engine_record_outcome(body: dict) -> dict:
    """Record realized payout only — never estimates as profit."""
    oid = str((body or {}).get("opportunity_id") or "").strip()
    if not oid:
        raise HTTPException(status_code=400, detail="opportunity_id_required")
    profit = float((body or {}).get("profit_eur") or 0)
    success = bool((body or {}).get("success"))
    return _ctx().micro_farm.income_engine_v1_record_outcome(
        oid, profit_eur=profit, success=success
    )


@app.post("/api/owner/income-engine/stage")
def owner_income_engine_stage(body: dict) -> dict:
    """paper | propose | micro_spend — Alpha Hunter stages."""
    stage = str((body or {}).get("stage") or "").strip()
    return _ctx().micro_farm.income_engine_v1_set_stage(stage)


@app.post("/api/owner/income-engine/paper-day")
def owner_income_engine_paper_day(body: dict) -> dict:
    """Stage 1 — model opportunities, spend €0 on search."""
    bal = float((body or {}).get("balance_eur") or 20)
    target = int((body or {}).get("opportunities_target") or 100)
    return _ctx().micro_farm.income_engine_v1_paper_day(
        balance_eur=bal, opportunities_target=target
    )


@app.post("/api/owner/income-engine/propose-top")
def owner_income_engine_propose_top(body: dict) -> dict:
    """Stage 2 — top strategies + micro-test quote for Approve."""
    raw = (body or {}).get("balance_eur")
    bal = float(raw) if raw is not None else None
    n = int((body or {}).get("n") or 3)
    return _ctx().micro_farm.income_engine_v1_propose_top(balance_eur=bal, n=n)


@app.post("/api/owner/income-engine/approve-micro-test")
def owner_income_engine_approve_micro_test(body: dict) -> dict:
    """Approve one strategy micro-test (≤2% bank). Search remains €0."""
    sid = str((body or {}).get("strategy_id") or "").strip()
    if not sid:
        raise HTTPException(status_code=400, detail="strategy_id_required")
    raw = (body or {}).get("balance_eur")
    bal = float(raw) if raw is not None else None
    return _ctx().micro_farm.income_engine_v1_approve_micro_test(
        sid, balance_eur=bal
    )


@app.post("/api/owner/income-engine/director-thresholds")
def owner_income_engine_director_thresholds(body: dict) -> dict:
    """Investment director: min expected profit € and/or min ROI %."""
    mode = (body or {}).get("search_mode") or (body or {}).get("mode")
    if mode:
        return _ctx().micro_farm.income_engine_v1_set_search_mode(str(mode))
    profit = (body or {}).get("min_expected_profit_eur")
    roi = (body or {}).get("min_roi_pct")
    return _ctx().micro_farm.income_engine_v1_set_director_thresholds(
        min_expected_profit_eur=float(profit) if profit is not None else None,
        min_roi_pct=float(roi) if roi is not None else None,
    )


@app.post("/api/owner/income-engine/search-mode")
def owner_income_engine_search_mode(body: dict) -> dict:
    """Newbie / Explorer / Balanced / Conservative search style."""
    mode = str((body or {}).get("mode") or (body or {}).get("search_mode") or "").strip()
    if not mode:
        raise HTTPException(status_code=400, detail="mode_required")
    return _ctx().micro_farm.income_engine_v1_set_search_mode(mode)


@app.post("/api/owner/income-engine/withdraw")
def owner_income_engine_withdraw(body: dict) -> dict:
    """Payout desk — withdraw realized available to Stripe queue (confirm required)."""
    raw = (body or {}).get("amount_eur")
    amount = float(raw) if raw is not None else None
    confirm = bool((body or {}).get("confirm", True))
    return _ctx().micro_farm.income_engine_v1_withdraw(
        amount_eur=amount, confirm=confirm
    )


@app.post("/api/owner/income-engine/scan-interval")
def owner_income_engine_scan_interval(body: dict) -> dict:
    """Fast cadences: 2m / 5m / 10m / 15m / 30m."""
    sec = int((body or {}).get("interval_sec") or 300)
    return _ctx().micro_farm.income_engine_v1_set_scan_interval(sec)


@app.post("/api/owner/income-engine/go-live")
def owner_income_engine_go_live() -> dict:
    """After analysis ready — switch Income Lab to LIVE (then Approve)."""
    return _ctx().micro_farm.income_engine_v1_go_live()


@app.post("/api/owner/income-engine/income-sources/toggle")
def owner_income_engine_income_source_toggle(body: dict) -> dict:
    """Enable/disable a money platform in Income Sources catalog."""
    sid = str((body or {}).get("source_id") or "").strip()
    if not sid:
        raise HTTPException(status_code=400, detail="source_id_required")
    active = bool((body or {}).get("active", True))
    return _ctx().micro_farm.income_engine_v1_set_income_source(sid, active=active)


@app.post("/api/owner/income-engine/income-sources/scan")
def owner_income_engine_income_sources_scan(body: dict) -> dict:
    """Scan active Income Sources — where money lives (spend €0)."""
    raw = (body or {}).get("balance_eur")
    bal = float(raw) if raw is not None else None
    return _ctx().micro_farm.income_engine_v1_scan_income_sources(balance_eur=bal)


@app.get("/api/owner/public-launch", response_model=PublicLaunchChecklist)
def get_public_launch_checklist() -> PublicLaunchChecklist:
    return PublicLaunchChecklist(**_ctx().public_launch.run())


@app.get("/api/owner/features")
def owner_features_snapshot() -> dict:
    from app.integration.feature_flags_service import snapshot

    return snapshot()


@app.post("/api/owner/features/tiktok/activate")
def owner_tiktok_activate(body: dict) -> dict:
    from app.integration.feature_flags_service import activate_tiktok

    if not body.get("ceo_confirmed"):
        raise HTTPException(
            status_code=400,
            detail="Нужно ceo_confirmed=true — явное подтверждение CEO.",
        )
    try:
        return activate_tiktok(ceo_confirmed=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/owner/features/tiktok/deactivate")
def owner_tiktok_deactivate() -> dict:
    from app.integration.feature_flags_service import deactivate_tiktok

    return deactivate_tiktok()


def _video_factory():
    from app.integration.video_factory_service import VideoFactoryService

    return VideoFactoryService(_memory_dir())


@app.get("/api/owner/video-factory")
def owner_video_factory_dashboard() -> dict:
    return _video_factory().dashboard()


@app.get("/api/owner/video-factory/library")
def owner_video_factory_library() -> dict:
    return {"items": _video_factory().list_library()}


@app.post("/api/owner/video-factory/library")
def owner_video_factory_add_library(body: dict) -> dict:
    try:
        row = _video_factory().add_library_item(body or {})
    except ValueError as exc:
        code = str(exc)
        if code == "tiktok_disabled":
            raise HTTPException(status_code=403, detail="TikTok Horizon выключен (kill switch).") from exc
        raise HTTPException(status_code=400, detail=code) from exc
    return {"ok": True, "item": row}


@app.get("/api/owner/video-factory/drafts")
def owner_video_factory_drafts() -> dict:
    return {"items": _video_factory().list_drafts()}


@app.post("/api/owner/video-factory/drafts")
def owner_video_factory_create_draft(body: dict) -> dict:
    issues = body.get("pattern_issues") or []
    if isinstance(issues, str):
        issues = [x.strip() for x in issues.replace(";", "\n").splitlines() if x.strip()]
    try:
        row = _video_factory().create_draft_from_pattern(
            niche=str(body.get("niche") or "Handwerk"),
            city=str(body.get("city") or "Deutschland"),
            pattern_issues=list(issues),
            frequency_note=str(body.get("frequency_note") or ""),
            source=str(body.get("source") or "manual"),
        )
    except ValueError as exc:
        code = str(exc)
        if code == "tiktok_disabled":
            raise HTTPException(status_code=403, detail="TikTok Horizon выключен (kill switch).") from exc
        raise HTTPException(status_code=400, detail=code) from exc
    return {"ok": True, "draft": row}


@app.post("/api/owner/video-factory/drafts/{draft_id}/approve")
def owner_video_factory_approve_draft(draft_id: str) -> dict:
    try:
        row = _video_factory().approve_draft(draft_id)
    except ValueError as exc:
        code = str(exc)
        if code == "tiktok_disabled":
            raise HTTPException(status_code=403, detail="TikTok Horizon выключен (kill switch).") from exc
        if code == "draft_not_found":
            raise HTTPException(status_code=404, detail="Черновик не найден") from exc
        raise HTTPException(status_code=400, detail=code) from exc
    return {"ok": True, "draft": row}


@app.get("/api/owner/video-factory/queue")
def owner_video_factory_queue() -> dict:
    return {"items": _video_factory().list_queue()}


@app.post("/api/owner/video-factory/queue")
def owner_video_factory_enqueue(body: dict) -> dict:
    try:
        item = _video_factory().queue_for_channel(
            str(body.get("draft_id") or ""),
            str(body.get("channel") or "tiktok"),
        )
    except ValueError as exc:
        code = str(exc)
        if code == "tiktok_disabled":
            raise HTTPException(status_code=403, detail="TikTok Horizon выключен (kill switch).") from exc
        if code == "draft_not_found":
            raise HTTPException(status_code=404, detail="Черновик не найден") from exc
        raise HTTPException(status_code=400, detail=code) from exc
    return {"ok": True, "item": item}


@app.post("/api/owner/video-factory/channels/{channel}/stage")
def owner_video_factory_channel_stage(channel: str, body: dict) -> dict:
    try:
        snap = _video_factory().set_channel_stage(channel, str(body.get("stage") or ""))
    except ValueError as exc:
        code = str(exc)
        if code == "tiktok_disabled":
            raise HTTPException(status_code=403, detail="TikTok Horizon выключен (kill switch).") from exc
        raise HTTPException(status_code=400, detail=code) from exc
    return snap


@app.get("/api/owner/video-factory/earnings")
def owner_video_factory_earnings() -> dict:
    return _video_factory().earnings_snapshot()


def _tiktok_horizon():
    from modules.tiktok_horizon import HorizonService

    return HorizonService(_memory_dir())


def _horizon_http_error(exc: Exception) -> HTTPException:
    code = str(exc)
    if code == "tiktok_disabled":
        return HTTPException(status_code=403, detail="TikTok Horizon выключен (kill switch).")
    if code == "horizon_not_internal_owner":
        return HTTPException(
            status_code=403,
            detail="TikTok Horizon доступен только Owner (INTERNAL_OWNER).",
        )
    if code == "draft_not_found":
        return HTTPException(status_code=404, detail="Черновик не найден")
    if code == "account_not_found":
        return HTTPException(status_code=404, detail="TikTok-аккаунт не найден")
    if code == "account_not_connected":
        return HTTPException(status_code=400, detail="Аккаунт не подключён")
    if code == "tiktok_oauth_not_configured":
        return HTTPException(
            status_code=400,
            detail="Задайте TIKTOK_CLIENT_KEY и TIKTOK_CLIENT_SECRET в .env.local",
        )
    if code == "invalid_oauth_state":
        return HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    if code == "no_trends":
        return HTTPException(
            status_code=400,
            detail="Нет трендов — сначала ingest observations или refresh trends.",
        )
    if code == "draft_not_approved":
        return HTTPException(status_code=400, detail="Сначала Approve, потом Queue.")
    return HTTPException(status_code=400, detail=code)


@app.get("/api/owner/tiktok-horizon")
def owner_tiktok_horizon_dashboard() -> dict:
    return _tiktok_horizon().dashboard()


@app.get("/api/owner/horizon")
def owner_horizon_media_engine() -> dict:
    """Horizon Media Engine — Internal-only studio shell (no live video gen)."""
    from app.integration.horizon_studio import build_horizon_manifest

    return build_horizon_manifest()


@app.get("/api/owner/tiktok-horizon/trends")
def owner_tiktok_horizon_trends() -> dict:
    return {"items": _tiktok_horizon().list_trends()}


@app.post("/api/owner/tiktok-horizon/trends/refresh")
def owner_tiktok_horizon_trends_refresh() -> dict:
    try:
        return _tiktok_horizon().refresh_trends()
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc


@app.post("/api/owner/tiktok-horizon/observations")
def owner_tiktok_horizon_ingest(body: dict) -> dict:
    rows = body.get("observations") or body.get("items") or []
    if not isinstance(rows, list):
        raise HTTPException(status_code=400, detail="observations must be a list")
    try:
        return _tiktok_horizon().ingest_observations(rows)
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc


@app.get("/api/owner/tiktok-horizon/drafts")
def owner_tiktok_horizon_drafts() -> dict:
    return {"items": _tiktok_horizon().list_drafts()}


@app.post("/api/owner/tiktok-horizon/drafts/generate")
def owner_tiktok_horizon_generate(body: dict | None = None) -> dict:
    body = body or {}
    try:
        drafts = _tiktok_horizon().generate_drafts(
            limit=int(body.get("limit") or 3),
            language=str(body.get("language") or "ru"),
        )
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc
    return {"ok": True, "drafts": drafts}


@app.get("/api/owner/tiktok-horizon/drafts/{draft_id}/review")
def owner_tiktok_horizon_review(draft_id: str) -> dict:
    try:
        return _tiktok_horizon().review_checklist(draft_id)
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc


@app.post("/api/owner/tiktok-horizon/drafts/{draft_id}/review")
def owner_tiktok_horizon_apply_review(draft_id: str, body: dict) -> dict:
    try:
        draft = _tiktok_horizon().apply_review_edits(draft_id, body.get("edits") or body)
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc
    return {"ok": True, "draft": draft}


@app.post("/api/owner/tiktok-horizon/drafts/{draft_id}/approve")
def owner_tiktok_horizon_approve(draft_id: str) -> dict:
    try:
        draft = _tiktok_horizon().approve_draft(draft_id)
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc
    return {"ok": True, "draft": draft}


@app.get("/api/owner/tiktok-horizon/queue")
def owner_tiktok_horizon_queue() -> dict:
    return {"items": _tiktok_horizon().list_queue()}


@app.post("/api/owner/tiktok-horizon/queue")
def owner_tiktok_horizon_enqueue(body: dict) -> dict:
    try:
        item = _tiktok_horizon().enqueue_draft(str(body.get("draft_id") or ""))
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc
    return {"ok": True, "item": item}


@app.get("/api/owner/tiktok-horizon/accounts")
def owner_tiktok_horizon_accounts(request: Request) -> dict:
    svc = _tiktok_horizon()
    try:
        return svc.oauth_status(public_api_base=str(request.base_url).rstrip("/"))
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc


@app.post("/api/owner/tiktok-horizon/accounts/sandbox")
def owner_tiktok_horizon_sandbox_account() -> dict:
    """Bind a local sandbox TikTok profile so Stage 1 pipeline can run before OAuth keys."""
    try:
        return _tiktok_horizon().connect_sandbox_account()
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc


@app.get("/api/owner/tiktok-horizon/oauth/start")
def owner_tiktok_horizon_oauth_start(request: Request):
    from fastapi.responses import RedirectResponse

    try:
        started = _tiktok_horizon().begin_oauth(
            public_api_base=str(request.base_url).rstrip("/")
        )
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc
    return RedirectResponse(started["authorize_url"], status_code=302)


@app.get("/api/owner/tiktok-horizon/oauth/callback")
def owner_tiktok_horizon_oauth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
):
    import os
    from urllib.parse import quote

    from fastapi.responses import RedirectResponse

    frontend = (
        os.getenv("GENESIS_FRONTEND_URL", "").strip()
        or os.getenv("NEXT_PUBLIC_SITE_URL", "").strip()
        or "http://localhost:3000"
    ).rstrip("/")
    accounts_url = f"{frontend}/tiktok-horizon?tab=accounts"

    if error:
        msg = quote(error_description or error or "oauth_error")
        return RedirectResponse(f"{accounts_url}&oauth_error={msg}", status_code=302)
    if not code or not state:
        return RedirectResponse(
            f"{accounts_url}&oauth_error={quote('missing_code_or_state')}",
            status_code=302,
        )
    try:
        _tiktok_horizon().complete_oauth(
            code=code,
            state=state,
            public_api_base=str(request.base_url).rstrip("/"),
        )
    except ValueError as exc:
        return RedirectResponse(
            f"{accounts_url}&oauth_error={quote(str(exc))}",
            status_code=302,
        )
    return RedirectResponse(f"{accounts_url}&oauth=ok", status_code=302)


@app.post("/api/owner/tiktok-horizon/accounts/{account_id}/disconnect")
def owner_tiktok_horizon_disconnect(account_id: str) -> dict:
    try:
        account = _tiktok_horizon().disconnect_account(account_id)
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc
    return {"ok": True, "account": account}


@app.post("/api/owner/tiktok-horizon/accounts/{account_id}/sync")
def owner_tiktok_horizon_sync(account_id: str) -> dict:
    try:
        account = _tiktok_horizon().sync_account(account_id)
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc
    return {"ok": True, "account": account}


@app.post("/api/owner/tiktok-horizon/accounts/{account_id}/reconnect")
def owner_tiktok_horizon_reconnect(account_id: str, request: Request):
    """Reconnect = start OAuth again (multi-account upsert by open_id)."""
    from fastapi.responses import RedirectResponse

    _ = account_id  # reserved for future account-scoped state
    try:
        started = _tiktok_horizon().begin_oauth(
            public_api_base=str(request.base_url).rstrip("/")
        )
    except ValueError as exc:
        raise _horizon_http_error(exc) from exc
    return RedirectResponse(started["authorize_url"], status_code=302)


@app.get("/api/owner/growth", response_model=GrowthCenter)
def get_growth_center() -> GrowthCenter:
    data = _ctx().growth.center()
    return GrowthCenter(**data)


@app.get("/api/opportunities/sources", response_model=OpportunitySourcesResponse)
def list_opportunity_sources() -> OpportunitySourcesResponse:
    svc = _ctx().opportunity
    return OpportunitySourcesResponse(
        sources=[OpportunitySource(**s) for s in svc.list_sources()],
        types=[OpportunityType(**t) for t in svc.list_types()],
        statuses=[OpportunityStatusOption(**s) for s in svc.list_statuses()],
    )


@app.get("/api/opportunities/dashboard", response_model=OpportunityDashboard)
def opportunity_dashboard() -> OpportunityDashboard:
    data = _ctx().opportunity.morning_dashboard()
    return OpportunityDashboard(
        **{
            **data,
            "top_today": [OpportunityRecord(**o) for o in data["top_today"]],
        }
    )


@app.get("/api/opportunities", response_model=OpportunityListResponse)
def list_opportunities(
    source_id: str | None = None,
    status: str | None = None,
    today_only: bool = False,
    limit: int = 100,
) -> OpportunityListResponse:
    items = _ctx().opportunity.list_opportunities(
        source_id=source_id,
        status=status,
        today_only=today_only,
        limit=limit,
    )
    return OpportunityListResponse(
        opportunities=[OpportunityRecord(**o) for o in items]
    )


@app.post("/api/opportunities", response_model=OpportunityCreatedResponse)
def create_opportunity(request: OpportunityCreateRequest) -> OpportunityCreatedResponse:
    try:
        row = _ctx().opportunity.create(request.model_dump())
    except ValueError as e:
        code = str(e)
        if code == "source_disabled":
            raise HTTPException(status_code=400, detail="Источник выключен")
        if code == "company_required":
            raise HTTPException(status_code=400, detail="Укажите название компании")
        if code == "invalid_type":
            raise HTTPException(status_code=400, detail="Некорректный тип возможности")
        raise HTTPException(status_code=400, detail="Не удалось создать запись")
    return OpportunityCreatedResponse(
        ok=True,
        opportunity=OpportunityRecord(**row),
        message="Возможность добавлена в журнал.",
    )


@app.patch("/api/opportunities/{opportunity_id}", response_model=OpportunityUpdatedResponse)
def update_opportunity(
    opportunity_id: str, request: OpportunityUpdateRequest
) -> OpportunityUpdatedResponse:
    payload = {k: v for k, v in request.model_dump().items() if v is not None}
    try:
        row = _ctx().opportunity.update(opportunity_id, payload)
    except ValueError as e:
        code = str(e)
        if code == "not_found":
            raise HTTPException(status_code=404, detail="Возможность не найдена")
        if code == "invalid_status":
            raise HTTPException(status_code=400, detail="Некорректный статус")
        raise HTTPException(status_code=400, detail="Не удалось обновить")
    return OpportunityUpdatedResponse(
        ok=True,
        opportunity=OpportunityRecord(**row),
        message="Запись обновлена.",
    )


@app.post("/api/public/leads/intake", response_model=LeadIntakeResponse)
def public_lead_intake(request: LeadIntakeRequest) -> LeadIntakeResponse:
    result = _ctx().lead_intake.intake(
        niche=request.niche,
        known={k: str(v) for k, v in (request.known or {}).items()},
        visitor_id=request.visitor_id,
        transcript=request.transcript,
    )
    return LeadIntakeResponse(**result)


@app.get("/api/leads/inbox", response_model=LeadInboxResponse)
def lead_inbox(today_only: bool = True, limit: int = 50) -> LeadInboxResponse:
    items = _ctx().lead_intake.inbox(today_only=today_only, limit=limit)
    leads = [OpportunityRecord(**o) for o in items]
    return LeadInboxResponse(leads=leads, count=len(leads))


@app.get("/api/swarm/health")
def swarm_health() -> dict:
    """Worker pool heartbeat — laptop probes this before remote dispatch."""
    return {"ok": True, "role": "worker_pool", "node": "genesis"}


@app.post("/api/swarm/execute")
def swarm_execute(
    payload: dict,
    authorization: str | None = Header(default=None),
) -> dict:
    """Remote execution — VPS/cloud runs labeling; laptop receives report only."""
    import os

    token = os.getenv("FARM_WORKER_POOL_TOKEN", "").strip()
    if token:
        expected = f"Bearer {token}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Invalid worker pool token")
    workers = int(payload.get("workers") or 10)
    adapter_id = str(payload.get("adapter_id") or "ai_labeling")
    return _ctx().micro_farm.execute_labeling_batch(workers=workers, adapter_id=adapter_id)


@app.get("/api/farm/scale-ai/status")
def farm_scale_ai_status() -> dict:
    return _ctx().micro_farm._check_scale_adapter()


@app.get("/api/farm/platforms")
def farm_platforms() -> dict:
    return {"platforms": _ctx().micro_farm._platforms()}


@app.get("/api/farm/export/labels")
def farm_export_labels():
    from fastapi.responses import PlainTextResponse

    text = _ctx().micro_farm.labels_export_text()
    if not text.strip():
        return PlainTextResponse(
            "# Пока пусто — запустите ферму и дождитесь разметок\n",
            media_type="text/plain",
        )
    return PlainTextResponse(text, media_type="application/x-ndjson")


@app.get("/api/farm/dashboard")
def farm_dashboard() -> dict:
    load_local_env()
    owner_name = _ctx().owner.owner_name()
    return _ctx().micro_farm.dashboard(owner_name)


@app.get("/api/farm/dashboard/lite")
def farm_dashboard_lite() -> dict:
    """Journal-safe dashboard — no blocking Toloka live probe."""
    load_local_env()
    owner_name = _ctx().owner.owner_name()
    return _ctx().micro_farm.dashboard_lite(owner_name)


@app.post("/api/farm/start")
def farm_start(workers: int = 10) -> dict:
    return _ctx().micro_farm.start_swarm(workers=max(1, min(1000, workers)))


@app.post("/api/farm/stop")
def farm_stop() -> dict:
    return _ctx().micro_farm.stop_swarm()


@app.get("/api/farm/dry-run")
def farm_dry_run_status() -> dict:
    return _ctx().micro_farm.dry_run_status()


@app.get("/api/farm/vault")
def farm_vault() -> dict:
    return _ctx().micro_farm.platform_vault_status()


@app.get("/api/farm/prepare-live")
def farm_prepare_live() -> dict:
    return _ctx().micro_farm.prepare_live_mode()


@app.post("/api/farm/test-connection-live")
def farm_test_connection_live() -> dict:
    load_local_env()
    return _ctx().micro_farm.run_test_connection_live()


@app.get("/api/farm/payment-monitor")
def farm_payment_monitor() -> dict:
    return _ctx().micro_farm.payment_monitor_status()


@app.get("/api/farm/payout-manager")
def farm_payout_manager() -> dict:
    """Payout Manager — where REAL sits and official withdraw paths (not Earn)."""
    return _ctx().micro_farm.payout_manager_panel()


@app.get("/api/farm/engine/v1")
def farm_engine_v1() -> dict:
    """Farm Engine v1 — Opportunity Scanner · Legal · ROI · Queue · Ledger (not Path A)."""
    return _ctx().micro_farm.farm_engine_v1()


@app.post("/api/farm/engine/v1/decide")
def farm_engine_v1_decide(opportunity_id: str, decision: str, note: str = "") -> dict:
    """CEO: go | reject | hold | research on a scanned opportunity."""
    return _ctx().micro_farm.farm_engine_v1_decide(opportunity_id, decision, note=note)


@app.post("/api/farm/engine/v1/enqueue")
def farm_engine_v1_enqueue(opportunity_id: str, note: str = "") -> dict:
    """Enqueue CEO-GO opportunity into dry_run execution queue."""
    return _ctx().micro_farm.farm_engine_v1_enqueue(opportunity_id, note=note)


@app.post("/api/farm/engine/v1/register-platform")
def farm_engine_v1_register_platform(body: dict) -> dict:
    """Direction B — add Earn platform research passport (not Live Earn)."""
    return _ctx().micro_farm.farm_engine_v1_register_platform(
        body if isinstance(body, dict) else {}
    )


@app.post("/api/farm/engine/v1/run-plan")
def farm_engine_v1_run_plan(opportunity_id: str) -> dict:
    """Re-run Execution Plan (checklist + auto tasks) after CEO GO."""
    return _ctx().micro_farm.farm_engine_v1_run_plan(opportunity_id)


@app.get("/api/farm/engine/v1/market-monitor")
def farm_engine_v1_market_monitor_get() -> dict:
    """Latest Farm Market Scanner digest (cache OK)."""
    return _ctx().micro_farm.farm_engine_v1_market_monitor(force=False)


@app.post("/api/farm/engine/v1/market-monitor")
def farm_engine_v1_market_monitor_run() -> dict:
    """Run Farm Market Scanner now — Reject / Research / GO digest for CEO."""
    return _ctx().micro_farm.farm_engine_v1_market_monitor(force=True)


@app.get("/api/farm/opire")
def farm_opire_panel(force_scan: bool = False, enrich_top: int = 0) -> dict:
    """Opire Semi-Auto Farm — scan + confidence + Approve (Reward Protection).

    Default force_scan=False so opening /farm-engine stays fast and does not
    trigger Windows Git Credential Manager (Select an account / x-access-token).
    Pass force_scan=true only from «Обновить Scanner».
    """
    return _ctx().micro_farm.opire_farm_panel(
        force_scan=force_scan, enrich_top=max(0, min(12, enrich_top))
    )


@app.post("/api/farm/opire/decide")
def farm_opire_decide(reward_id: str, decision: str, note: str = "") -> dict:
    """CEO: approve | skip Opire bounty candidate."""
    return _ctx().micro_farm.opire_farm_decide(reward_id, decision, note=note)


@app.post("/api/farm/opire/advance")
def farm_opire_advance(
    reward_id: str,
    status: str,
    pr_id: str = "",
    pr_url: str = "",
    payment_confirmation_id: str = "",
    payout_usd: float | None = None,
    note: str = "",
) -> dict:
    """Advance bounty state machine. REAL requires payment_confirmation_id."""
    return _ctx().micro_farm.opire_farm_advance(
        reward_id,
        status,
        pr_id=pr_id or None,
        pr_url=pr_url or None,
        payment_confirmation_id=payment_confirmation_id or None,
        payout_usd=payout_usd,
        note=note,
    )


@app.post("/api/farm/opire/execute")
def farm_opire_execute(reward_id: str, clone: bool = True) -> dict:
    """CEO: start Execution Engine Stages 1–5 after Approve. Never submits PR."""
    return _ctx().micro_farm.opire_farm_start_execution(reward_id, clone=clone)


@app.post("/api/farm/opire/submit")
def farm_opire_submit(
    reward_id: str, pr_id: str = "", pr_url: str = "", note: str = ""
) -> dict:
    """CEO Submit — live GitHub Draft PR (IDs from API, not manual entry)."""
    return _ctx().micro_farm.opire_farm_ceo_submit(
        reward_id,
        pr_id=pr_id or None,
        pr_url=pr_url or None,
        note=note,
    )


@app.post("/api/farm/opire/tick")
def farm_opire_autonomous_tick(max_actions: int = 3) -> dict:
    """Durable AUTO-RUN pulse — bounty queue only (+ parallel API Farm step)."""
    opire = _ctx().micro_farm.opire_farm_autonomous_tick(
        max_actions=max(1, min(10, max_actions))
    )
    # Separate worker: never routed through bounty Execution Engine
    api_farm = _api_farm().autonomous_tick(max_steps=2)
    from swarm.farm_queues import build_farm_queues_status

    queues = build_farm_queues_status(_opire_engine())
    return {
        "ok": True,
        "opire": {**(opire if isinstance(opire, dict) else {"result": opire}), "queue_id": "BOUNTY_EXECUTION_QUEUE"},
        "api_farm": {**(api_farm if isinstance(api_farm, dict) else {}), "queue_id": "API_FARM_QUEUE"},
        "queues": queues,
    }


def _opire_engine():
    try:
        from pathlib import Path

        from swarm.opire_farm import OpireFarmEngine

        mem = getattr(_ctx().micro_farm, "_memory", None)
        if mem is None:
            return None
        return OpireFarmEngine(Path(mem))
    except Exception:
        return None


@app.get("/api/farm/queues")
def farm_queues_status() -> dict:
    """BOUNTY_EXECUTION_QUEUE · API_FARM_QUEUE · REVENUE_FARM_QUEUE (separated)."""
    from swarm.farm_queues import build_farm_queues_status

    return build_farm_queues_status(_opire_engine())


@app.get("/api/farm/money-hunter")
def farm_money_hunter_panel() -> dict:
    load_local_env()
    return _ctx().micro_farm.money_hunter()


@app.get("/api/farm/reality")
def farm_reality() -> dict:
    """REAL vs pipeline vs Toloka — never mixed."""
    load_local_env()
    return _ctx().micro_farm.money_hunter_reality()


@app.get("/api/farm/opportunities/top")
def farm_opportunities_top(limit: int = 20) -> dict:
    load_local_env()
    return _ctx().micro_farm.money_hunter_top(limit=max(1, min(100, limit)))


@app.post("/api/farm/opportunities/import")
def farm_opportunities_import(body: dict) -> dict:
    """Manual marketplace job import → analyze → profit → score."""
    load_local_env()
    return _ctx().micro_farm.money_hunter_import(body or {})


@app.post("/api/farm/opportunities/{opportunity_id}/approve")
def farm_opportunity_approve(
    opportunity_id: str, confirm: bool = False, note: str = ""
) -> dict:
    load_local_env()
    return _ctx().micro_farm.money_hunter_approve(
        opportunity_id, confirm=confirm, note=note
    )


@app.post("/api/farm/opportunities/{opportunity_id}/reject")
def farm_opportunity_reject(opportunity_id: str, note: str = "") -> dict:
    load_local_env()
    return _ctx().micro_farm.money_hunter_reject(opportunity_id, note=note)


@app.post("/api/farm/opportunities/{opportunity_id}/start")
def farm_opportunity_start(opportunity_id: str) -> dict:
    load_local_env()
    return _ctx().micro_farm.money_hunter_start(opportunity_id)


@app.post("/api/farm/opportunities/{opportunity_id}/delivery")
def farm_opportunity_delivery(opportunity_id: str) -> dict:
    load_local_env()
    return _ctx().micro_farm.money_hunter_delivery(opportunity_id)


def _api_farm():
    from app.integration.api_farm_service import ApiFarmService

    mem = getattr(_ctx().micro_farm, "_memory", None)
    return ApiFarmService(mem)


@app.get("/api/farm/rapidapi/status")
def farm_rapidapi_status() -> dict:
    return _api_farm().status()


@app.get("/api/farm/rapidapi/candidates")
def farm_rapidapi_candidates(top: int = 50) -> dict:
    return _api_farm().candidates(top=max(1, min(200, top)))


@app.get("/api/farm/rapidapi/jobs")
def farm_rapidapi_jobs(limit: int = 100) -> dict:
    return _api_farm().jobs(limit=max(1, min(500, limit)))


@app.get("/api/farm/rapidapi/revenue")
def farm_rapidapi_revenue() -> dict:
    return _api_farm().revenue()


@app.get("/api/farm/rapidapi/markets")
def farm_rapidapi_markets(wave_only: bool = False) -> dict:
    """Global Market Registry — ISO map; LIVE only with verified datasets."""
    from swarm.farm_channels.rapidapi.markets import (
        coverage_summary,
        list_markets,
        market_capabilities_matrix,
        products_catalog,
    )
    from swarm.farm_channels.rapidapi.markets.quality import wave_quality_table

    return {
        "ok": True,
        "coverage": coverage_summary(),
        "matrix": market_capabilities_matrix(wave_only=True),
        "quality": wave_quality_table(),
        "products": products_catalog(),
        "markets": list_markets(wave_only=wave_only) if wave_only else list_markets(),
        "honesty_rule": (
            "No fake LIVE. Postal endpoints only for LIVE markets with commercial-ok datasets."
        ),
        "money_rule": "REAL REVENUE = RapidAPI/payment settlement only",
    }


@app.post("/api/farm/rapidapi/run")
def farm_rapidapi_run(
    action: str = "discover",
    candidate_id: str = "",
    max_steps: int = 8,
) -> dict:
    return _api_farm().run(
        action=action,
        candidate_id=candidate_id,
        max_steps=max(1, min(20, max_steps)),
    )


@app.post("/api/farm/rapidapi/approve/{candidate_id}")
def farm_rapidapi_approve(candidate_id: str, note: str = "") -> dict:
    return _api_farm().approve(candidate_id, note=note)


@app.post("/api/farm/rapidapi/publish/{candidate_id}")
def farm_rapidapi_publish(candidate_id: str) -> dict:
    return _api_farm().publish(candidate_id)


@app.post("/api/farm/rapidapi/revenue/ingest")
def farm_rapidapi_revenue_ingest(body: dict) -> dict:
    """Ingest RapidAPI financial event. PAID_OUT + Hard REAL → Ledger only."""
    return _api_farm().ingest_revenue(body or {})


@app.get("/api/farm/runtime")
def farm_runtime_index() -> dict:
    from app.integration.api_farm_runtime_service import runtime_index

    return runtime_index()


@app.api_route(
    "/api/farm/runtime/{slug}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def farm_runtime_root(slug: str, request: Request):
    from app.integration.api_farm_runtime_service import dispatch_runtime

    return await dispatch_runtime(slug, request, "")


@app.api_route(
    "/api/farm/runtime/{slug}/{subpath:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def farm_runtime_sub(slug: str, subpath: str, request: Request):
    from app.integration.api_farm_runtime_service import dispatch_runtime

    return await dispatch_runtime(slug, request, subpath)


@app.post("/api/farm/opire/sync")
def farm_opire_sync(reward_id: str, confirm_real: bool = False) -> dict:
    """Sync merge/reward from GitHub+Opire. confirm_real → REAL without typed IDs."""
    return _ctx().micro_farm.opire_farm_sync(reward_id, confirm_real=confirm_real)


@app.post("/api/farm/real-payout")
def farm_real_payout(
    amount_eur: float,
    payout_id: str,
    platform: str = "toloka",
    task_id: str = "",
    balance_after_eur: float | None = None,
) -> dict:
    """Record a real exchange payout (webhook / manual proof). Rejects missing payout_id."""
    load_local_env()
    return _ctx().micro_farm.log_real_exchange_payout(
        amount_eur=amount_eur,
        payout_id=payout_id,
        platform=platform,
        task_id=task_id,
        balance_after_eur=balance_after_eur,
    )


@app.get("/api/farm/revenue-audit")
def farm_revenue_audit() -> dict:
    return _ctx().micro_farm.revenue_capability_audit()


@app.get("/api/farm/revenue-sources")
def farm_revenue_sources() -> dict:
    return _ctx().micro_farm.revenue_source_catalog()


@app.get("/api/farm/revenue-sources/center")
def farm_revenue_sources_center() -> dict:
    """Revenue Sources v0 — income control center (no web discovery)."""
    return _ctx().micro_farm.revenue_sources_center()


@app.get("/api/farm/revenue-lab/brief")
def farm_revenue_lab_brief() -> dict:
    """Revenue Lab CEO brief — local farm path (no Commercial Gateway owner gate)."""
    return {"ok": True, **_ctx().micro_farm.revenue_lab_brief()}


@app.post("/api/farm/revenue-lab/scan")
def farm_revenue_lab_scan() -> dict:
    """Research scan + live Country Desk / Digistore / Stripe / Recommendation paths."""
    from app.commercial_api.revenue_lab import RevenueLab

    return RevenueLab(_memory_dir()).research_scan(persist_alerts=True)


@app.get("/api/farm/finance-law")
def farm_finance_law() -> dict:
    """Finance Reality Law — Reality over Simulation (binding)."""
    from app.integration.swarm_bridge import ensure_swarm_importable

    ensure_swarm_importable()
    from swarm.finance_reality_law import law_manifest

    return law_manifest()


@app.get("/api/farm/unit-economics")
def farm_unit_economics() -> dict:
    return _ctx().micro_farm.unit_economics_report()


@app.get("/api/farm/finance-ledger")
def farm_finance_ledger(real_only: bool = False, limit: int = 100) -> dict:
    return _ctx().micro_farm.finance_ledger_snapshot(
        real_only=real_only,
        limit=max(1, min(500, limit)),
    )


@app.get("/api/farm/finance-ledger.csv")
def farm_finance_ledger_csv(real_only: bool = True):
    from fastapi.responses import PlainTextResponse

    body = _ctx().micro_farm.finance_ledger_export_csv(real_only=real_only)
    return PlainTextResponse(
        body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=virtus_finance_ledger.csv"},
    )


@app.get("/api/farm/forecast")
def farm_forecast(labeling_nodes: int = 50, passive_nodes: int = 0) -> dict:
    return _ctx().micro_farm.revenue_forecast(
        labeling_nodes=max(1, min(500, labeling_nodes)),
        passive_nodes=max(0, min(5000, passive_nodes)),
    )


@app.post("/api/farm/battle-test")
def farm_battle_test() -> dict:
    return _ctx().micro_farm.run_battle_test()


@app.post("/api/farm/tick")
def farm_tick(workers: int = 10) -> dict:
    out = _ctx().micro_farm.run_tick(workers=max(1, min(100, workers)))
    try:
        api_farm = _api_farm().autonomous_tick(max_steps=1)
    except Exception as exc:
        api_farm = {"ok": False, "error": str(exc), "queue_id": "API_FARM_QUEUE"}
    try:
        from swarm.farm_queues import build_farm_queues_status

        queues = build_farm_queues_status(_opire_engine())
    except Exception as exc:
        queues = {"ok": False, "error": str(exc)}
    if isinstance(out, dict):
        out = {
            **out,
            "api_farm": {**(api_farm if isinstance(api_farm, dict) else {}), "queue_id": "API_FARM_QUEUE"},
            "queues": queues,
        }
    return out


@app.get("/api/farm/toloka/status")
def farm_toloka_submit_status() -> dict:
    load_local_env()
    return _ctx().micro_farm.toloka_submit_status()


@app.post("/api/farm/toloka/submit")
def farm_toloka_submit(limit: int = 50, trigger_run: bool = True) -> dict:
    load_local_env()
    return _ctx().micro_farm.submit_toloka_labels(
        limit=max(1, min(50, limit)),
        trigger_run=trigger_run,
    )


@app.get("/api/farm/first-euro")
def farm_first_euro_gate() -> dict:
    load_local_env()
    return _ctx().micro_farm.first_euro_gate()


@app.get("/api/farm/verified-revenue")
def farm_verified_revenue_engine() -> dict:
    load_local_env()
    return _ctx().micro_farm.verified_revenue_engine()


@app.post("/api/farm/first-euro/confirm")
def farm_first_euro_confirm(step_id: str, done: bool = True) -> dict:
    load_local_env()
    return _ctx().micro_farm.confirm_first_euro_step(step_id, done=done)


@app.get("/api/farm/commercial-evidence")
def farm_commercial_evidence() -> dict:
    load_local_env()
    ev = _ctx().micro_farm.commercial_evidence()
    return ev or {"ok": False, "message": "Нет отчёта — запустите tick или submit"}


@app.get("/api/farm/program")
def farm_program() -> dict:
    """Unified Mission 1 program: VRE levels, Finance Guard, Evidence, pipeline."""
    load_local_env()
    return _ctx().micro_farm.farm_program()


@app.get("/api/farm/experiments")
def farm_commercial_experiments() -> dict:
    load_local_env()
    rows = _ctx().micro_farm.commercial_experiments()
    return {"ok": True, "experiments": rows}


@app.post("/api/farm/revenue-replay")
def farm_revenue_replay(workers: int = 10) -> dict:
    load_local_env()
    return _ctx().micro_farm.run_revenue_replay(workers=max(1, min(100, workers)))


@app.get("/api/farm/production-platform")
def farm_production_platform() -> dict:
    load_local_env()
    return _ctx().micro_farm.production_platform()


@app.get("/api/farm/quote")
def farm_auto_quote(service_id: str = "svc_data_qa", volume: float = 1000, workers: int = 10) -> dict:
    load_local_env()
    return _ctx().micro_farm.auto_quote(
        service_id=service_id,
        volume=volume,
        workers=max(1, min(100, workers)),
    )


@app.get("/api/farm/opportunity-discovery")
def farm_opportunity_discovery() -> dict:
    load_local_env()
    return _ctx().micro_farm.opportunity_discovery()


@app.post("/api/farm/opportunity-discovery/{opportunity_id}/prepare")
def farm_prepare_opportunity_proposal(opportunity_id: str) -> dict:
    load_local_env()
    return _ctx().micro_farm.prepare_opportunity_proposal(opportunity_id)


@app.post("/api/farm/opportunity-discovery/{opportunity_id}/lost")
def farm_record_opportunity_lost(opportunity_id: str, reason_code: str = "other", note_ru: str = "") -> dict:
    load_local_env()
    return _ctx().micro_farm.record_opportunity_lost(
        opportunity_id,
        reason_code=reason_code,
        note_ru=note_ru,
    )


@app.post("/api/farm/feed")
def farm_feed() -> dict:
    """Discover public URLs worldwide — fills combiner task queue."""
    spider = _ctx().monetization_engine.run_global_spider_scan(
        niche="local_service",
        batch_limit=200,
        tech_pattern_ids=None,
    )
    state = _ctx().micro_farm._load_state()
    state["last_spider_scan"] = {
        "scanned": spider.get("scanned"),
        "passed_gate": spider.get("passed_gate"),
        "message": spider.get("message"),
    }
    _ctx().micro_farm._save_state(state)
    tick = _ctx().micro_farm.run_tick(workers=20)
    spider_ok = bool(spider.get("passed_gate") or spider.get("scanned"))
    return {
        "ok": spider_ok or int(tick.get("tasks_done") or 0) > 0,
        "discovery": spider,
        "tick": tick,
        "message": f"{spider.get('message', 'Поиск завершён')} · {tick.get('message', '')}",
    }


@app.get("/api/engine/dashboard", response_model=EngineDashboard)
def engine_dashboard() -> EngineDashboard:
    dash = _ctx().owner.dashboard()
    owner_name = str(dash.get("owner_name") or "Ramiš")
    return EngineDashboard(**_ctx().monetization_engine.engine_dashboard(owner_name))


@app.post("/api/engine/sync-payments", response_model=PaymentSyncResponse)
def engine_sync_payments() -> PaymentSyncResponse:
    return PaymentSyncResponse(**_ctx().monetization_engine.sync_payment_providers())


@app.post("/api/engine/scan-mode", response_model=EngineScanModeResponse)
def engine_scan_mode(request: EngineScanModeRequest) -> EngineScanModeResponse:
    result = _ctx().monetization_engine.run_scan_mode(
        niche=request.niche,
        city=request.city,
        limit=min(50, max(1, request.limit)),
    )
    return EngineScanModeResponse(**result)


@app.post("/api/engine/network-scan", response_model=EngineNetworkScanResponse)
def engine_network_scan(request: EngineNetworkScanRequest) -> EngineNetworkScanResponse:
    result = _ctx().monetization_engine.run_network_scan(
        niche=request.niche,
        batch_limit=min(1000, max(1, request.batch_limit)),
        region=request.region,
    )
    return EngineNetworkScanResponse(**result)


@app.post("/api/engine/global-spider-scan")
def engine_global_spider_scan(request: EngineGlobalSpiderScanRequest) -> dict:
    return _ctx().monetization_engine.run_global_spider_scan(
        niche=request.niche,
        batch_limit=min(1000, max(1, request.batch_limit)),
        tech_pattern_ids=request.tech_pattern_ids or None,
    )


@app.get("/api/engine/lead-engine-v2/status")
def lead_engine_v2_status() -> dict:
    from app.integration.lead_engine_v2 import LeadEngineV2

    return LeadEngineV2(_memory_dir()).status()


@app.post("/api/engine/lead-engine-v2/reset")
def lead_engine_v2_reset() -> dict:
    """Archive old lead base and start Lead Engine v2 empty index."""
    from app.integration.lead_engine_v2 import LeadEngineV2

    return LeadEngineV2(_memory_dir()).reset_old_base(
        opportunity_service=_ctx().opportunity
    )


@app.post("/api/engine/lead-engine-v2/pause")
def lead_engine_v2_pause() -> dict:
    from app.integration.lead_engine_v2 import LeadEngineV2

    return LeadEngineV2(_memory_dir()).pause()


@app.post("/api/engine/lead-engine-v2/resume")
def lead_engine_v2_resume() -> dict:
    from app.integration.lead_engine_v2 import LeadEngineV2

    return LeadEngineV2(_memory_dir()).resume()


@app.post("/api/engine/lead-engine-v2/configure")
def lead_engine_v2_configure(body: dict) -> dict:
    from app.integration.lead_engine_v2 import LeadEngineV2

    return LeadEngineV2(_memory_dir()).configure(body or {})


@app.post("/api/engine/lead-engine-v2/countries/{code}/enable")
def lead_engine_v2_enable_country(code: str, body: dict | None = None) -> dict:
    from app.integration.lead_engine_v2 import LeadEngineV2

    enabled = True if body is None else bool((body or {}).get("enabled", True))
    return LeadEngineV2(_memory_dir()).set_country_enabled(code, enabled)


@app.get("/api/engine/lead-engine-v2/next-send-slot")
def lead_engine_v2_next_send_slot() -> dict:
    from app.integration.lead_engine_v2 import LeadEngineV2

    return LeadEngineV2(_memory_dir()).next_send_slot()


@app.post("/api/engine/lead-engine-v2/record-contact")
def lead_engine_v2_record_contact(body: dict) -> dict:
    from app.integration.lead_engine_v2 import LeadEngineV2

    return LeadEngineV2(_memory_dir()).record_contact(
        domain=str((body or {}).get("domain") or ""),
        email=str((body or {}).get("email") or ""),
        channel=str((body or {}).get("channel") or "email"),
        template=str((body or {}).get("template") or ""),
        country=str((body or {}).get("country") or ""),
        meta=(body or {}).get("meta") if isinstance((body or {}).get("meta"), dict) else None,
    )


@app.get("/api/engine/ai-brain-setup")
def engine_ai_brain_setup() -> dict:
    from app.integration.engine_ai_service import EngineAIService

    return EngineAIService().setup_status()


@app.get("/api/engine/stealth-mode")
def engine_stealth_mode() -> dict:
    from app.integration.stealth_http import stealth_status

    return stealth_status()


@app.get("/api/engine/places-setup")
def engine_places_setup() -> dict:
    from app.integration.google_places_service import GooglePlacesService

    return GooglePlacesService().setup_status()


@app.get("/api/engine/analytics/live")
def engine_analytics_live() -> dict:
    return _ctx().monetization_engine.live_analytics()


@app.get("/api/engine/digital-dust/dashboard")
def engine_digital_dust_dashboard() -> dict:
    return _ctx().monetization_engine._digital_dust.dashboard()  # noqa: SLF001


@app.get("/api/engine/logic-chain")
def engine_logic_chain() -> dict:
    from app.integration.digital_dust_service import DigitalDustService

    return {"steps": DigitalDustService.logic_chain()}


@app.get("/api/engine/smart-gate/dashboard")
def engine_smart_gate_dashboard() -> dict:
    return _ctx().monetization_engine._smart_gate.dashboard()  # noqa: SLF001


@app.post("/api/engine/junk-archive/run", response_model=EngineJunkArchiveResponse)
def engine_junk_archive_run() -> EngineJunkArchiveResponse:
    return EngineJunkArchiveResponse(**_ctx().monetization_engine.process_junk_archive_cycle())


@app.post("/api/engine/scan", response_model=EngineScanResponse)
def engine_scan(request: EngineScanRequest) -> EngineScanResponse:
    try:
        result = _ctx().monetization_engine.scan_and_gate(request.url, niche=request.niche, manual=request.manual)
    except ValueError as e:
        code = str(e)
        if code == "forbidden_target":
            raise HTTPException(status_code=403, detail="Запрещённая цель — только публичные URL")
        if code == "robots_txt_disallowed":
            raise HTTPException(status_code=403, detail="robots.txt запрещает доступ — Genesis проходит мимо")
        if code == "Unauthorized Operation":
            raise HTTPException(status_code=403, detail="Unauthorized Operation — Stealth Force-Read-Only")
        if code in ("url_required", "public_http_only"):
            raise HTTPException(status_code=400, detail="Укажите публичный http(s) URL")
        if code == "fetch_failed":
            raise HTTPException(status_code=502, detail="Не удалось проанализировать URL")
        raise HTTPException(status_code=400, detail="Сканирование не выполнено")
    return EngineScanResponse(
        ok=True,
        profit_score=result["profit_score"],
        shown_to_owner=result["shown_to_owner"],
        message=result["message"],
        target=OpportunityRecord(**result["target"]),
    )


@app.post("/api/engine/targets/{opportunity_id}/accept", response_model=AssetActionResponse)
def engine_accept_target(opportunity_id: str) -> AssetActionResponse:
    try:
        row = _ctx().monetization_engine.accept_asset(opportunity_id)
    except ValueError as e:
        if str(e) == "not_found":
            raise HTTPException(status_code=404, detail="Цель не найдена")
        raise HTTPException(status_code=400, detail="Не удалось принять")
    return AssetActionResponse(
        ok=True,
        target=OpportunityRecord(**row),
        message="Актив принят — монетизация в работе.",
    )


@app.post("/api/engine/wallets/connect")
def engine_connect_wallet(request: ConnectWalletRequest) -> dict:
    return _ctx().monetization_engine.connect_payout_wallet(
        request.wallet_id,
        request.account_label,
    )


@app.post("/api/engine/withdraw", response_model=WithdrawResponse)
def engine_withdraw(request: WithdrawRequest) -> WithdrawResponse:
    try:
        result = _ctx().monetization_engine.request_withdrawal(
            request.amount_eur,
            request.wallet_id,
        )
    except ValueError as e:
        if str(e) == "insufficient_balance":
            raise HTTPException(status_code=400, detail="Недостаточно средств на балансе добычи")
        if str(e) == "invalid_amount":
            raise HTTPException(status_code=400, detail="Некорректная сумма")
        if str(e) == "sandbox_mode_withdrawal_disabled":
            raise HTTPException(
                status_code=403,
                detail="Вывод недоступен в Sandbox Mode — активируйте бизнес (ACTIVATE BUSINESS)",
            )
        raise HTTPException(status_code=400, detail="Вывод не выполнен")
    return WithdrawResponse(**result)


@app.get("/api/engine/system-mode")
def engine_system_mode() -> dict:
    return _ctx().business_mode.status()


@app.post("/api/engine/activate-business")
def engine_activate_business(body: EngineActivateBusinessRequest) -> dict:
    try:
        return _ctx().business_mode.activate_business(
            confirmed=body.confirmed,
            phrase=body.phrase,
            owner_name=body.owner_name or "CEO",
        )
    except ValueError as e:
        code = str(e)
        if code == "confirmation_required":
            raise HTTPException(status_code=400, detail="Требуется подтверждение")
        if code == "invalid_confirm_phrase":
            raise HTTPException(status_code=400, detail="Неверная фраза подтверждения")
        raise HTTPException(status_code=400, detail="Активация не выполнена")


@app.get("/api/engine/accounting", response_model=EngineAccountingSummary)
def engine_accounting() -> EngineAccountingSummary:
    ctx = _ctx()
    summary = ctx.engine_accounting.accounting_summary()
    if ctx.business_mode.is_live():
        summary["export_summary"] = ctx.financial_export.export_summary()
    return EngineAccountingSummary(**summary)


@app.patch("/api/engine/accounting/settings", response_model=EngineTaxSettings)
def engine_accounting_settings(body: EngineTaxSettings) -> EngineTaxSettings:
    saved = _ctx().engine_accounting.save_tax_settings(body.model_dump())
    return EngineTaxSettings(
        vat_rate_percent=float(saved.get("vat_rate_percent") or 19),
        stripe_fee_percent=float(saved.get("stripe_fee_percent") or 1.4),
        stripe_fee_fixed_eur=float(saved.get("stripe_fee_fixed_eur") or 0.25),
        service_label=str(saved.get("service_label") or ""),
    )


@app.get("/api/engine/accounting/export.csv")
def engine_accounting_export_csv() -> PlainTextResponse:
    try:
        csv_text = _ctx().engine_accounting.export_csv()
    except ValueError as e:
        if str(e) == "sandbox_mode_financial_docs_disabled":
            raise HTTPException(status_code=403, detail="Sandbox: экспорт отключён до ACTIVATE BUSINESS")
        raise
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="harvest_report.csv"'},
    )


@app.get("/api/engine/accounting/export.datev.csv")
def engine_accounting_export_datev() -> PlainTextResponse:
    try:
        csv_text = _ctx().financial_export.export_datev_csv()
    except ValueError as e:
        if str(e) == "sandbox_mode_financial_docs_disabled":
            raise HTTPException(status_code=403, detail="Sandbox: DATEV отключён до ACTIVATE BUSINESS")
        raise
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="virtus_datev_export.csv"'},
    )


@app.get("/api/engine/hunter/dashboard")
def engine_hunter_dashboard() -> dict:
    return _ctx().monetization_engine._hunter.hunter_dashboard()  # noqa: SLF001


@app.get("/api/engine/hunter/dataset.csv")
def engine_hunter_dataset_csv() -> PlainTextResponse:
    csv_text = _ctx().monetization_engine._hunter.dataset_export_csv()  # noqa: SLF001
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="virtus_hunter_dataset.csv"'},
    )


@app.get("/api/engine/accounting/export-summary", response_model=EngineFinancialExportSummary)
def engine_accounting_export_summary() -> EngineFinancialExportSummary:
    try:
        return EngineFinancialExportSummary(**_ctx().financial_export.export_summary())
    except ValueError as e:
        if str(e) == "sandbox_mode_financial_docs_disabled":
            raise HTTPException(status_code=403, detail="Sandbox: экспорт отключён до ACTIVATE BUSINESS")
        raise


@app.get("/api/engine/accounting/invoice/{opportunity_id}", response_class=HTMLResponse)
def engine_accounting_invoice(opportunity_id: str) -> HTMLResponse:
    try:
        html = _ctx().engine_accounting.generate_invoice_html(opportunity_id)
    except ValueError as e:
        if str(e) == "not_found":
            raise HTTPException(status_code=404, detail="Актив не найден")
        if str(e) == "no_revenue":
            raise HTTPException(status_code=400, detail="Нет дохода для счёта")
        if str(e) == "sandbox_mode_financial_docs_disabled":
            raise HTTPException(status_code=403, detail="Sandbox: Rechnungen отключены до ACTIVATE BUSINESS")
        raise HTTPException(status_code=400, detail="Счёт не сформирован")
    return HTMLResponse(content=html)


@app.get("/api/scanner/dashboard", response_model=AssetScannerDashboard)
def asset_scanner_dashboard() -> AssetScannerDashboard:
    return AssetScannerDashboard(**_ctx().asset_scanner.dashboard())


@app.get("/api/scanner/niches", response_model=AssetNichesResponse)
def asset_scanner_niches() -> AssetNichesResponse:
    return AssetNichesResponse(niches=_ctx().asset_scanner.niches())


@app.get("/api/scanner/targets", response_model=AssetTargetsResponse)
def asset_scanner_targets(limit: int = 50) -> AssetTargetsResponse:
    items = _ctx().asset_scanner.list_targets(limit=limit)
    targets = [OpportunityRecord(**o) for o in items]
    return AssetTargetsResponse(targets=targets, count=len(targets))


@app.post("/api/scanner/scan", response_model=AssetScanResponse)
def asset_scanner_scan(request: AssetScanRequest) -> AssetScanResponse:
    try:
        row = _ctx().asset_scanner.scan_url(request.url, niche=request.niche)
    except ValueError as e:
        code = str(e)
        if code == "forbidden_target":
            raise HTTPException(
                status_code=403,
                detail="Запрещено: только публичные URL без ключей и закрытых систем.",
            )
        if code == "robots_txt_disallowed":
            raise HTTPException(status_code=403, detail="robots.txt запрещает доступ — Genesis проходит мимо")
        if code == "Unauthorized Operation":
            raise HTTPException(status_code=403, detail="Unauthorized Operation — Stealth Force-Read-Only")
        if code in ("url_required", "public_http_only"):
            raise HTTPException(status_code=400, detail="Укажите публичный http(s) URL")
        if code == "fetch_failed":
            raise HTTPException(status_code=502, detail="Не удалось проанализировать URL")
        raise HTTPException(status_code=400, detail="Сканирование не выполнено")
    return AssetScanResponse(
        ok=True,
        target=OpportunityRecord(**row),
        message="Цель добавлена в журнал возможностей.",
    )


@app.post("/api/scanner/targets/{opportunity_id}/analyze", response_model=AssetActionResponse)
def asset_analyze_target(opportunity_id: str) -> AssetActionResponse:
    try:
        row = _ctx().asset_scanner.analyze_target(opportunity_id)
    except ValueError as e:
        code = str(e)
        if code == "not_found":
            raise HTTPException(status_code=404, detail="Цель не найдена")
        if code == "forbidden_target":
            raise HTTPException(status_code=403, detail="Запрещённая цель")
        if code == "robots_txt_disallowed":
            raise HTTPException(status_code=403, detail="robots.txt запрещает доступ — Genesis проходит мимо")
        if code == "Unauthorized Operation":
            raise HTTPException(status_code=403, detail="Unauthorized Operation — Stealth Force-Read-Only")
        raise HTTPException(status_code=400, detail="Анализ не выполнен")
    return AssetActionResponse(
        ok=True,
        target=OpportunityRecord(**row),
        message="Потенциал дохода пересчитан.",
    )


@app.post("/api/scanner/targets/{opportunity_id}/accept", response_model=AssetActionResponse)
def asset_accept_target(opportunity_id: str) -> AssetActionResponse:
    try:
        row = _ctx().asset_scanner.accept_for_work(opportunity_id)
    except ValueError as e:
        if str(e) == "not_found":
            raise HTTPException(status_code=404, detail="Цель не найдена")
        raise HTTPException(status_code=400, detail="Не удалось принять в работу")
    return AssetActionResponse(
        ok=True,
        target=OpportunityRecord(**row),
        message="Принято в работу — монетизация запущена.",
    )


@app.get("/api/support/status")
def support_status() -> dict:
    from app.env_loader import load_local_env
    from app.integration.support_remote import remote_status_overlay

    load_local_env()
    return remote_status_overlay(_ctx().support.configuration_status())


@app.get("/api/support/threads")
def support_list_threads(status: str | None = None, limit: int = 80) -> dict:
    items = _ctx().support.list_threads(status=status, limit=max(1, min(200, limit)))
    return {"items": items, "count": len(items)}


@app.get("/api/support/threads/{thread_id}")
def support_get_thread(thread_id: str) -> dict:
    row = _ctx().support.get_thread(thread_id)
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    return row


@app.post("/api/support/threads/{thread_id}/reply")
def support_reply_thread(thread_id: str, body: dict | None = None) -> dict:
    body = body or {}
    try:
        return _ctx().support.reply(
            thread_id,
            text=str(body.get("text") or ""),
            save_as_template=bool(body.get("save_as_template")),
            template_name=str(body.get("template_name") or ""),
            create_auto_rule=bool(body.get("create_auto_rule")),
        )
    except ValueError as exc:
        code = str(exc)
        if code == "not_found":
            raise HTTPException(status_code=404, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc


@app.post("/api/support/threads/{thread_id}/status")
def support_set_thread_status(thread_id: str, body: dict | None = None) -> dict:
    body = body or {}
    try:
        return _ctx().support.set_status(thread_id, str(body.get("status") or ""))
    except ValueError as exc:
        code = str(exc)
        if code == "not_found":
            raise HTTPException(status_code=404, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc


@app.post("/api/support/threads/{thread_id}/unsubscribe")
def support_unsubscribe_thread(thread_id: str, body: dict | None = None) -> dict:
    """Mark sender Do Not Email, close thread, keep conversation history."""
    body = body or {}
    email_fallback = str(body.get("email") or "").strip()
    try:
        return _ctx().support.mark_unsubscribed(
            thread_id, email_fallback=email_fallback
        )
    except ValueError as exc:
        code = str(exc)
        # Thread may live only on Railway — still block local outreach by email
        if code == "not_found" and email_fallback:
            try:
                return _ctx().support.unsubscribe_email(
                    email_fallback,
                    thread_id=thread_id,
                    source="support_ui",
                )
            except ValueError as exc2:
                raise HTTPException(status_code=400, detail=str(exc2)) from exc2
        if code == "not_found":
            raise HTTPException(status_code=404, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc


@app.post("/api/support/do-not-email")
def support_do_not_email(body: dict | None = None) -> dict:
    """Block an address without requiring a local thread id."""
    body = body or {}
    email = str(body.get("email") or "").strip()
    try:
        return _ctx().support.unsubscribe_email(
            email,
            thread_id=str(body.get("thread_id") or ""),
            source=str(body.get("source") or "support_ui"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/support/threads/{thread_id}")
def support_delete_thread(thread_id: str) -> dict:
    ok = _ctx().support.delete_thread(thread_id)
    if not ok:
        raise HTTPException(status_code=404, detail="not_found")
    return {"ok": True, "deleted": thread_id}


@app.get("/api/support/templates")
def support_list_templates() -> dict:
    items = _ctx().support.list_templates()
    return {"items": items, "count": len(items)}


@app.post("/api/support/templates")
def support_create_template(body: dict | None = None) -> dict:
    body = body or {}
    return _ctx().support.create_template(
        name=str(body.get("name") or "Template"),
        subject=str(body.get("subject") or ""),
        body=str(body.get("body") or ""),
        source_fingerprint=str(body.get("source_fingerprint") or ""),
    )


@app.get("/api/support/auto-rules")
def support_list_auto_rules() -> dict:
    items = _ctx().support.list_auto_rules()
    return {"items": items, "count": len(items)}


@app.post("/api/support/auto-rules")
def support_create_auto_rule(body: dict | None = None) -> dict:
    body = body or {}
    try:
        return _ctx().support.create_auto_rule(
            fingerprint=str(body.get("fingerprint") or ""),
            template_id=str(body.get("template_id") or ""),
            enabled=bool(body.get("enabled", True)),
            label=str(body.get("label") or ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/support/auto-rules/{rule_id}/enabled")
def support_set_auto_rule_enabled(rule_id: str, body: dict | None = None) -> dict:
    body = body or {}
    try:
        return _ctx().support.set_auto_rule_enabled(rule_id, bool(body.get("enabled", True)))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/support/auto-rules/{rule_id}")
def support_delete_auto_rule(rule_id: str) -> dict:
    ok = _ctx().support.delete_auto_rule(rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="not_found")
    return {"ok": True}


@app.get("/api/acquisition/status", response_model=AcquisitionStudioStatus)
def acquisition_studio_status() -> AcquisitionStudioStatus:
    return AcquisitionStudioStatus(**_ctx().acquisition.studio_status())


@app.get("/api/acquisition/live-monitor")
def acquisition_live_monitor(window_minutes: int = 10) -> dict:
    """Live Activity Monitor — runner + funnel facts (not capability cards)."""
    return _ctx().acquisition.live_monitor(
        window_minutes=max(1, min(120, int(window_minutes or 10)))
    )


@app.get("/api/farm/live-monitor")
def farm_live_monitor(window_minutes: int = 10) -> dict:
    """Same Live Monitor for Доход desk (no owner gate)."""
    return _ctx().acquisition.live_monitor(
        window_minutes=max(1, min(120, int(window_minutes or 10)))
    )


@app.get("/api/earn-marketplace/today")
def earn_marketplace_today() -> dict:
    """Marketplace of earning opportunities — not Toloka farm, not lead CRM list."""
    from app.integration.earn_opportunity_marketplace import build_earn_marketplace_board

    return build_earn_marketplace_board(_memory_dir())


@app.get("/api/earn-marketplace/status")
def earn_marketplace_status() -> dict:
    from app.integration.earn_opportunity_marketplace import build_earn_marketplace_board

    board = build_earn_marketplace_board(_memory_dir())
    return {
        "ok": True,
        "version": board.get("version"),
        "headline_ru": board.get("headline_ru"),
        "farms": len(board.get("farms") or []),
        "opportunities": len(board.get("opportunities") or []),
        "external_task_marketplace": False,
    }


@app.get("/api/worker-research/board")
def worker_research_board() -> dict:
    """Worker Research Lab — platforms with official get-task → pay cycle."""
    return _ctx().worker_research.board()


@app.post("/api/worker-research/scan")
def worker_research_scan(force: bool = True) -> dict:
    """Manual or due scan. Never registers accounts or accepts ToS."""
    return _ctx().worker_research.maybe_scan(force=bool(force))


@app.post("/api/worker-research/platforms/{platform_id}/approve")
def worker_research_approve(platform_id: str, note: str = "") -> dict:
    """CEO queues platform for Worker Adapter — keys/ToS stay manual."""
    result = _ctx().worker_research.ceo_approve(platform_id, note=note)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "approve_failed")
    return result


@app.post("/api/worker-research/platforms/{platform_id}/payout-proof")
def worker_research_payout_proof(
    platform_id: str,
    amount_eur: float = 0,
    reference: str = "",
    note: str = "",
) -> dict:
    """Record one CONFIRMED payout — L4; Working only via Adapter Builder promote."""
    result = _ctx().worker_research.record_payout_proof(
        platform_id,
        amount_eur=amount_eur,
        reference=reference,
        note=note,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "proof_failed")
    maturity = _ctx().worker_adapters.on_payout_recorded(platform_id)
    result["maturity"] = maturity
    return result


@app.get("/api/worker-adapters/board")
def worker_adapters_board() -> dict:
    """Adapter Builder — maturity L0–L6 and Work Farm allowlist."""
    return _ctx().worker_adapters.board()


def _adapter_http_detail(result: dict) -> str:
    return str(
        result.get("detail_ru")
        or result.get("message_ru")
        or result.get("error")
        or "adapter_failed"
    )


@app.post("/api/worker-adapters/{platform_id}/create")
def worker_adapters_create(platform_id: str, note: str = "") -> dict:
    result = _ctx().worker_adapters.create_adapter(platform_id, note=note)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=_adapter_http_detail(result))
    return result


@app.post("/api/worker-adapters/{platform_id}/sandbox")
def worker_adapters_sandbox(platform_id: str) -> dict:
    result = _ctx().worker_adapters.run_sandbox(platform_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=_adapter_http_detail(result))
    return result


@app.post("/api/worker-adapters/{platform_id}/promote-working")
def worker_adapters_promote(platform_id: str) -> dict:
    result = _ctx().worker_adapters.promote_working(platform_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=_adapter_http_detail(result))
    return result


@app.post("/api/worker-adapters/{platform_id}/mark-scaled")
def worker_adapters_scaled(platform_id: str, jobs_done: int = 0) -> dict:
    result = _ctx().worker_adapters.mark_scaled(platform_id, jobs_done=jobs_done)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=_adapter_http_detail(result))
    return result


@app.get("/api/work-farm/status")
def work_farm_status() -> dict:
    """Work Farm v0 board — own paid orders only (no marketplace)."""
    return _ctx().work_farm.status_board()


@app.get("/api/work-farm/stats")
def work_farm_stats(work_type: str = "landing_page") -> dict:
    """Landing (or other) job aggregates — real files only."""
    return {
        "ok": True,
        "stats": _ctx().work_farm.stats(work_type=str(work_type or "landing_page")),
    }


@app.get("/api/work-farm/catalog")
def work_farm_catalog() -> dict:
    return _ctx().work_farm.catalog()


@app.get("/api/work-farm/replay/{job_id}")
def work_farm_replay(job_id: str) -> dict:
    """Replay Job — timeline + economics (read-only)."""
    result = _ctx().work_farm.replay(job_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "job_not_found")
    return result


@app.get("/api/work-farm/jobs/{order_id}")
def work_farm_job_for_order(order_id: str) -> dict:
    job = _ctx().work_farm.find_job_for_order(order_id)
    if not job:
        raise HTTPException(status_code=404, detail="job_not_found")
    return {"ok": True, "job": job}


@app.post("/api/work-farm/run/{order_id}")
def work_farm_run(order_id: str, force: bool = False) -> dict:
    """Manual / retry: run Work Farm for an existing paid order."""
    return _ctx().work_farm.run_for_order(order_id, force=force)


@app.get("/api/acquisition/gate-funnel")
def acquisition_gate_funnel() -> dict:
    return _ctx().acquisition.gate_funnel()


@app.get("/api/acquisition/pipeline")
def acquisition_pipeline(limit: int = 50) -> dict:
    items = _ctx().acquisition.pipeline_leads(limit=max(1, min(100, limit)))
    return {"items": items, "count": len(items)}


@app.get("/api/acquisition/history")
def acquisition_history(limit: int = 50) -> dict:
    """Sent / Won / Lost — separate from Ready working queue."""
    items = _ctx().acquisition.history_leads(limit=max(1, min(100, limit)))
    return {"items": items, "count": len(items)}


@app.post("/api/acquisition/refresh-leads")
def acquisition_refresh_leads(body: dict | None = None) -> dict:
    body = body or {}
    return _ctx().acquisition.refresh_country_desk_leads(
        limit=max(1, min(20, int(body.get("limit") or 8))),
        query=str(body.get("query") or "").strip() or None,
        city=str(body.get("city") or "").strip() or None,
        market=str(body.get("market") or "").strip().upper() or None,
        auto_confirm=bool(body.get("auto_confirm", True)),
    )


@app.post("/api/acquisition/rebuild-quotes")
def acquisition_rebuild_quotes(body: dict | None = None) -> dict:
    """CEO: rewrite every active lead letter + local-currency price (no Places hunt)."""
    body = body or {}
    return _ctx().acquisition.rebuild_pipeline_quotes(
        limit=max(1, min(200, int(body.get("limit") or 80))),
    )


@app.post("/api/acquisition/reset-desk")
def acquisition_reset_desk(body: dict | None = None) -> dict:
    """CEO: zero send counters + finance wallet/ledger display."""
    _ = body or {}
    return _ctx().acquisition.reset_desk_counters_and_wallet()


@app.post("/api/acquisition/auto-confirm-high-win")
def acquisition_auto_confirm_high_win(body: dict | None = None) -> dict:
    body = body or {}
    min_win = int(body.get("min_win_pct") or 75)
    return _ctx().acquisition.auto_confirm_high_probability(min_win_pct=max(55, min(95, min_win)))


@app.get("/api/acquisition/catalog", response_model=AcquisitionCatalogResponse)
def acquisition_catalog(public_only: bool = True) -> AcquisitionCatalogResponse:
    return AcquisitionCatalogResponse(**_ctx().acquisition.catalog(public_only=public_only))


@app.get("/api/acquisition/worklist", response_model=AcquisitionDailyWorklist)
def acquisition_daily_worklist() -> AcquisitionDailyWorklist:
    return AcquisitionDailyWorklist(**_ctx().acquisition.daily_worklist())


@app.get("/api/acquisition/markets")
def acquisition_markets_dashboard() -> dict:
    """CEO: per-country caps / sent / replies / orders (config-driven)."""
    return _ctx().acquisition.markets_dashboard()


@app.get("/api/acquisition/adaptive")
def acquisition_adaptive_dashboard() -> dict:
    """Adaptive Outreach Intelligence — health, scaling, history, graphs."""
    return _ctx().acquisition.adaptive_dashboard(auto_review=True)


@app.post("/api/acquisition/adaptive/review")
def acquisition_adaptive_review(body: dict | None = None) -> dict:
    payload = body or {}
    force = bool(payload.get("force", True))
    apply = bool(payload.get("apply", True))
    return _ctx().acquisition.run_adaptive_review(force=force, apply=apply)


@app.get("/api/acquisition/runner")
def acquisition_runner_status() -> dict:
    """Country Desk Start/Stop status (ticks, log)."""
    return _ctx().acquisition.runner_status()


@app.get("/api/acquisition/sending-health")
def acquisition_sending_health() -> dict:
    """CEO: lamps + human blocker for lead delivery (Resend/Gmail/quota)."""
    status = _ctx().acquisition.studio_status()
    health = status.get("lead_sending_health")
    if isinstance(health, dict) and health.get("ok"):
        return health
    return {"ok": False, "error": "health_unavailable"}


@app.get("/api/acquisition/email-providers")
def acquisition_email_providers() -> dict:
    """CEO Health Dashboard — Email Provider Pool lamps + last errors + quota."""
    status = _ctx().acquisition.studio_status()
    board = status.get("email_providers")
    if isinstance(board, dict) and board.get("ok"):
        return board
    from pathlib import Path

    from app.integration.email_provider_pool import email_providers_health

    quota = status.get("outreach_quota") if isinstance(status.get("outreach_quota"), dict) else None
    return email_providers_health(
        Path(_ctx().acquisition._memory_dir),  # noqa: SLF001
        domain_quota=quota,
    )


@app.post("/api/acquisition/provider-cooldown/clear")
def acquisition_clear_provider_cooldown(body: dict | None = None) -> dict:
    """CEO: clear Resend / pool cooldowns (including leftover diagnostic tests)."""
    from pathlib import Path

    from app.integration.email_provider_pool import clear_provider_cooldown
    from app.integration.outreach_provider_cooldown import clear_resend_cooldown

    body = body or {}
    reason = str(body.get("reason") or "cleared_by_ceo_api")[:120]
    provider = str(body.get("provider") or "").strip().lower() or None
    mem = Path(_ctx().acquisition._memory_dir)  # noqa: SLF001
    pool = clear_provider_cooldown(mem, provider=provider)
    legacy = clear_resend_cooldown(mem, cleared_reason=reason)
    return {"ok": True, "pool": pool, "legacy_resend": legacy}


@app.post("/api/acquisition/runner/start")
def acquisition_runner_start() -> dict:
    return _ctx().acquisition.runner_start()


@app.post("/api/acquisition/ceo-prefs")
def acquisition_ceo_prefs(body: dict | None = None) -> dict:
    """Toggle auto-refresh / auto-send for Country Desk."""
    body = body or {}
    auto_refresh = body.get("auto_refresh")
    auto_send = body.get("auto_send")
    return _ctx().acquisition.set_ceo_prefs(
        auto_refresh=None if auto_refresh is None else bool(auto_refresh),
        auto_send=None if auto_send is None else bool(auto_send),
    )


@app.post("/api/acquisition/do-not-email")
def acquisition_do_not_email(body: dict | None = None) -> dict:
    """Suppress outreach locally — bypasses Railway Support proxy (no more Not Found)."""
    body = body or {}
    email = str(body.get("email") or "").strip()
    thread_id = str(body.get("thread_id") or "").strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="email_required")
    try:
        out = _ctx().support.unsubscribe_email(
            email,
            thread_id=thread_id,
            source=str(body.get("source") or "support_ui"),
            note=str(body.get("note") or "Do not send marketing / outreach emails"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "unsubscribed": True,
        "message": "Unsubscribed successfully",
        "email": out.get("email"),
        "contact": out.get("contact"),
        "leads_suppressed": out.get("leads_suppressed"),
        "thread": out.get("thread"),
    }


@app.post("/api/acquisition/runner/stop")
def acquisition_runner_stop() -> dict:
    return _ctx().acquisition.runner_stop()


@app.post("/api/acquisition/runner/tick")
def acquisition_runner_tick() -> dict:
    """One hunt/draft (+ optional send) tick — used by CEO UI poll while running."""
    return _ctx().acquisition.runner_tick()


@app.get("/api/acquisition/website-markets")
def acquisition_website_markets() -> dict:
    """Country Website Localization profiles from outreach_markets.json."""
    from app.integration.outreach_market_config import list_website_markets, outreach_markets_config

    cfg = outreach_markets_config()
    return {
        "ok": True,
        "allocation_mode": cfg.get("allocation_mode"),
        "markets": list_website_markets(enabled_only=True),
    }


@app.get("/api/acquisition/outreach-templates")
def acquisition_outreach_templates() -> dict:
    """CEO review: Path A sniper drafts by market (DE / US / RU / UA)."""
    from app.integration.outreach_language_service import preview_market_templates

    samples = preview_market_templates()
    return {
        "ok": True,
        "kpi_ru": "Ответы → разговоры → оплаченные заказы (не число писем).",
        "phase1_ru": "Глобальный потолок ~120/день · интервал ≥90с · Approve вручную.",
        "samples": samples,
    }


@app.get("/api/acquisition/approval-queue", response_model=AcquisitionApprovalQueueResponse)
def acquisition_approval_queue() -> AcquisitionApprovalQueueResponse:
    items = _ctx().acquisition.approval_queue()
    return AcquisitionApprovalQueueResponse(
        items=[AcquisitionApprovalItem(**i) for i in items]
    )


@app.get("/api/acquisition/manual-review-queue")
def acquisition_manual_review_queue() -> dict:
    items = _ctx().acquisition.manual_review_queue()
    return {"items": items, "auto_draft_max_eur": 50.0}


@app.post("/api/acquisition/opportunities/{opportunity_id}/promote-review")
def acquisition_promote_review(opportunity_id: str) -> dict:
    try:
        row = _ctx().acquisition.promote_manual_review(opportunity_id)
        return {"ok": True, "opportunity": row, "message": "В очереди Approve"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/acquisition/evidence", response_model=AcquisitionEvidenceReport)
def acquisition_evidence() -> AcquisitionEvidenceReport:
    return AcquisitionEvidenceReport(**_ctx().acquisition.evidence_report())


@app.post("/api/acquisition/generate-drafts")
def acquisition_generate_drafts(body: dict) -> dict:
    try:
        city = str(body.get("city") or "").strip()
        query = str(body.get("query") or "").strip()
        limit = int(body.get("limit") or 10)
        language = str(body.get("language") or "").strip()
        if not language:
            from app.integration.locale_service import resolve_generation_language

            language = resolve_generation_language(
                body.get("locale"),
                body.get("ui_lang"),
                market_code=str(body.get("market") or body.get("market_code") or "") or None,
            )
        throttle_ms = int(body.get("throttle_ms") or 250)
        force_skip_check = bool(body.get("force_skip_check"))
        result = _ctx().acquisition.generate_drafts_from_places(
            city=city,
            query=query,
            limit=limit,
            language=language,
            throttle_ms=throttle_ms,
            force_skip_check=force_skip_check,
        )
        return {
            "ok": True,
            "leads_found": int(result.get("leads_found") or 0),
            "created": int(result.get("created") or 0),
            "drafted": int(result.get("drafted") or 0),
            "skipped_has_site": int(result.get("skipped_has_site") or 0),
            "skipped_already_queued": int(result.get("skipped_already_queued") or 0),
            "force_skip_check": force_skip_check,
            "message": "Drafts generated",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/acquisition/analyze-site", response_model=SiteAnalysisResult)
def acquisition_analyze_site(body: dict) -> SiteAnalysisResult:
    url = str(body.get("url") or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="Укажите URL сайта")
    return SiteAnalysisResult(**_ctx().acquisition.analyze_site(url))


@app.post(
    "/api/acquisition/opportunities/{opportunity_id}/prepare",
    response_model=AcquisitionPrepareResponse,
)
def acquisition_prepare(
    opportunity_id: str, request: AcquisitionPrepareRequest
) -> AcquisitionPrepareResponse:
    try:
        row = _ctx().acquisition.prepare_opportunity(
            opportunity_id, website_url=request.website_url
        )
    except ValueError as e:
        if str(e) == "not_found":
            raise HTTPException(status_code=404, detail="Возможность не найдена")
        raise HTTPException(status_code=400, detail="Не удалось подготовить КП")
    return AcquisitionPrepareResponse(
        ok=True,
        opportunity=OpportunityRecord(**row),
        message="Анализ и черновик письма готовы — ожидают Approve CEO.",
    )


@app.post(
    "/api/acquisition/opportunities/{opportunity_id}/approve",
    response_model=AcquisitionApproveResponse,
)
def acquisition_approve(
    opportunity_id: str, request: AcquisitionInteractionRequest
) -> AcquisitionApproveResponse:
    try:
        _ctx().acquisition.record_interaction(
            opportunity_id, event=request.event, note=request.note
        )
        result = _ctx().acquisition.approve_outreach(opportunity_id)
    except ValueError as e:
        code = str(e)
        if code == "not_found":
            raise HTTPException(status_code=404, detail="Возможность не найдена")
        if code == "not_pending":
            raise HTTPException(status_code=400, detail="Нет черновика на одобрение")
        raise HTTPException(status_code=400, detail="Не удалось одобрить")
    return AcquisitionApproveResponse(
        ok=True,
        opportunity=OpportunityRecord(**result["opportunity"]),
        message=result["message"],
        send_result=result.get("send_result"),
    )


@app.post(
    "/api/acquisition/opportunities/{opportunity_id}/reject",
    response_model=AcquisitionPrepareResponse,
)
def acquisition_reject(
    opportunity_id: str, request: AcquisitionInteractionRequest
) -> AcquisitionPrepareResponse:
    try:
        row = _ctx().acquisition.reject_outreach(opportunity_id, note=request.note)
    except ValueError as e:
        if str(e) == "not_found":
            raise HTTPException(status_code=404, detail="Возможность не найдена")
        raise HTTPException(status_code=400, detail="Не удалось отклонить")
    return AcquisitionPrepareResponse(
        ok=True,
        opportunity=OpportunityRecord(**row),
        message="Черновик отклонён.",
    )


@app.post(
    "/api/acquisition/opportunities/{opportunity_id}/mark-sent",
    response_model=AcquisitionPrepareResponse,
)
def acquisition_mark_sent(
    opportunity_id: str, request: AcquisitionInteractionRequest
) -> AcquisitionPrepareResponse:
    try:
        row = _ctx().acquisition.mark_sent_manual(opportunity_id, note=request.note)
    except ValueError as e:
        if str(e) == "not_found":
            raise HTTPException(status_code=404, detail="Возможность не найдена")
        raise HTTPException(status_code=400, detail="Не удалось обновить")
    return AcquisitionPrepareResponse(
        ok=True,
        opportunity=OpportunityRecord(**row),
        message="Отмечено: письмо отправлено вручную.",
    )


@app.post(
    "/api/acquisition/opportunities/{opportunity_id}/interaction",
    response_model=AcquisitionPrepareResponse,
)
def acquisition_record_interaction(
    opportunity_id: str, request: AcquisitionInteractionRequest
) -> AcquisitionPrepareResponse:
    try:
        row = _ctx().acquisition.record_interaction(
            opportunity_id,
            request.event,
            request.note,
            market_lesson=request.market_lesson,
            market_reason=request.market_reason,
        )
    except ValueError as e:
        if str(e) == "not_found":
            raise HTTPException(status_code=404, detail="Возможность не найдена")
        if str(e) == "market_reason_required":
            raise HTTPException(
                status_code=400,
                detail="Выберите причину из списка — иначе исход не сохраняем (Evidence First).",
            )
        if str(e) == "market_lesson_required":
            raise HTTPException(
                status_code=400,
                detail="Для «Другое» нужен короткий комментарий CEO.",
            )
        raise HTTPException(status_code=400, detail="Не удалось записать событие")
    return AcquisitionPrepareResponse(
        ok=True,
        opportunity=OpportunityRecord(**row),
        message="Событие и урок рынка записаны.",
    )


@app.get("/api/owner/mission-control", response_model=MissionControl)
def get_mission_control() -> MissionControl:
    data = _ctx().mission_control.snapshot()
    return MissionControl(**data)


@app.get("/api/owner/execution/capabilities")
def owner_execution_capabilities() -> dict:
    from app.execution.bridge import list_user_capabilities
    from app.execution.service import ExecutionLayerService

    svc = ExecutionLayerService(_memory_dir())
    snap = svc.capabilities_snapshot()
    snap["user_ready"] = list_user_capabilities(_memory_dir())
    from app.execution.capability_graph import graph_snapshot

    snap["capability_graph"] = graph_snapshot()
    return snap


@app.get("/api/owner/external-capabilities")
def owner_external_capabilities() -> dict:
    """Free-tier ExternalCapability catalog — disabled by default; Mission1 Freeze metadata."""
    from app.integration.external_capabilities import snapshot

    return snapshot(mission1_freeze=True)


@app.get("/api/owner/foundation-capabilities")
def owner_foundation_capabilities() -> dict:
    """Foundation F1 capability registry (includes external_api domain)."""
    from app.integration.capability_registry import CapabilityRegistry

    return CapabilityRegistry(memory_dir=_memory_dir()).snapshot()


@app.post("/api/owner/execution/plan-preview")
def owner_execution_plan_preview(body: dict) -> dict:
    from app.execution.service import ExecutionLayerService

    goal = str(body.get("goal") or "").strip()
    if not goal:
        raise HTTPException(status_code=400, detail="goal required")
    workspace_id = str(body.get("workspace_id") or "").strip()
    return ExecutionLayerService(_memory_dir()).plan_preview(goal, workspace_id=workspace_id)


@app.post("/api/owner/demo-mode", response_model=DemoModeResponse)
def set_demo_mode(request: DemoModeRequest) -> DemoModeResponse:
    result = _ctx().mission_control.set_demo_mode(request.enabled)
    return DemoModeResponse(**result)


@app.get("/api/owner/timeline", response_model=TimelineResponse)
def get_timeline() -> TimelineResponse:
    data = _ctx().timeline.snapshot()
    return TimelineResponse(**data)


@app.post("/api/assistant/ask", response_model=AssistantResponse)
def ask_assistant(request: AssistantRequest) -> AssistantResponse:
    svc = AssistantService(_ctx())
    result = svc.ask(request.question, locale=request.locale)
    return AssistantResponse(**result)


def _genesis_dev_mode_allowed(http_request: Request) -> bool:
    """Thinking Brief / debug only on localhost or when GENESIS_DEV_MODE=1 (never production)."""
    return dev_mode_allowed(http_request)


def _genesis_service(packages: list | None = None) -> GenesisAIService:
    """Reload secrets each request — setup wizard / llm.key works without restart."""
    load_local_env()
    return GenesisAIService(packages or [], memory_dir=_memory_dir())


@app.post("/api/public/concierge", response_model=ConciergeResponse)
@app.post("/api/public/genesis-ai", response_model=ConciergeResponse)
def ask_concierge(
    request: ConciergeRequest,
    http_request: Request,
    debug: bool = False,
) -> ConciergeResponse:
    ctx = _ctx()
    packages = ctx.sales.packages()
    mem = _memory_dir()
    intake_svc = KnowledgeIntakeService(mem)
    attachment_files = intake_svc.resolve_for_execution(
        attachment_ids=request.attachment_ids or [],
        visitor_id=request.visitor_id,
        session_id=request.session_id,
    )
    use_debug = debug and _genesis_dev_mode_allowed(http_request)
    merged_context = dict(request.context or {})
    if request.ui_locale:
        merged_context["ui_locale"] = request.ui_locale
    if request.assistant_locale:
        merged_context["assistant_locale"] = request.assistant_locale
    elif request.locale:
        merged_context["assistant_locale"] = request.locale
    if request.communication_style:
        merged_context["communication_style"] = request.communication_style
    result = _genesis_service(packages).chat(
        request.question,
        history=[m.model_dump() for m in (request.history or [])],
        context=merged_context,
        attachment_note="",
        attachment_files=attachment_files,
        attachment_ids=request.attachment_ids or [],
        visitor_id=request.visitor_id,
        session_id=request.session_id,
        debug=use_debug,
    )
    return ConciergeResponse(**result)


@app.get("/api/public/genesis-ai/sessions", response_model=ChatSessionListResponse)
def list_chat_sessions(visitor_id: str) -> ChatSessionListResponse:
    vid = (visitor_id or "anonymous").strip()[:64]
    svc = _genesis_service(_ctx().sales.packages())
    rows = svc.sessions.list_for_visitor(vid)
    return ChatSessionListResponse(
        sessions=[ChatSessionSummary(**r) for r in rows]
    )


@app.post("/api/public/genesis-ai/sessions", response_model=ChatSessionCreateResponse)
def create_chat_session(body: ChatSessionCreateRequest) -> ChatSessionCreateResponse:
    vid = body.visitor_id.strip()[:64]
    row = _genesis_service(_ctx().sales.packages()).sessions.create(
        vid, title=body.title.strip() or "Новое поручение"
    )
    return ChatSessionCreateResponse(
        session_id=row["session_id"],
        title=row["title"],
        created_at=row["created_at"],
    )


@app.get(
    "/api/public/genesis-ai/sessions/{session_id}",
    response_model=ChatSessionDetailResponse,
)
def get_chat_session(session_id: str, visitor_id: str) -> ChatSessionDetailResponse:
    vid = (visitor_id or "anonymous").strip()[:64]
    row = _genesis_service(_ctx().sales.packages()).sessions.get(session_id)
    if not row or row.get("visitor_id") != vid:
        raise HTTPException(status_code=404, detail="session not found")
    msgs = [
        {"role": m.get("role", "user"), "content": m.get("content", "")}
        for m in (row.get("messages") or [])
        if m.get("role") in ("user", "assistant")
    ]
    return ChatSessionDetailResponse(
        session_id=row["session_id"],
        visitor_id=vid,
        title=row.get("title") or "Новое поручение",
        created_at=row.get("created_at") or "",
        updated_at=row.get("updated_at") or "",
        pinned=bool(row.get("pinned")),
        messages=msgs,
    )


@app.patch(
    "/api/public/genesis-ai/sessions/{session_id}",
    response_model=ChatSessionDetailResponse,
)
def rename_chat_session(
    session_id: str, body: ChatSessionRenameRequest
) -> ChatSessionDetailResponse:
    vid = body.visitor_id.strip()[:64]
    row = _genesis_service(_ctx().sales.packages()).sessions.rename(
        session_id, vid, body.title
    )
    if not row:
        raise HTTPException(status_code=404, detail="session not found")
    return get_chat_session(session_id, vid)


@app.post(
    "/api/public/genesis-ai/sessions/{session_id}/pin",
    response_model=ChatSessionDetailResponse,
)
def pin_chat_session(
    session_id: str, body: ChatSessionPinRequest
) -> ChatSessionDetailResponse:
    vid = body.visitor_id.strip()[:64]
    row = _genesis_service(_ctx().sales.packages()).sessions.set_pinned(
        session_id, vid, body.pinned
    )
    if not row:
        raise HTTPException(status_code=404, detail="session not found")
    return get_chat_session(session_id, vid)


@app.delete("/api/public/genesis-ai/sessions/{session_id}")
def delete_chat_session(session_id: str, visitor_id: str) -> dict:
    vid = (visitor_id or "anonymous").strip()[:64]
    ok = _genesis_service(_ctx().sales.packages()).sessions.delete(session_id, vid)
    if not ok:
        raise HTTPException(status_code=404, detail="session not found")
    return {"ok": True}


@app.get("/api/public/genesis-ai/attachments/policy")
def genesis_attachment_policy(visitor_id: str = "anonymous") -> dict:
    from app.integration.knowledge_intake_transparency import upload_policy_snapshot

    vid = (visitor_id or "anonymous").strip()[:64]
    return upload_policy_snapshot(_memory_dir(), visitor_id=vid)


@app.post("/api/public/genesis-ai/attachments", response_model=ChatAttachmentResponse)
async def upload_genesis_chat_attachment(
    file: UploadFile = File(...),
    visitor_id: str = "anonymous",
    files_in_message: int = 1,
) -> ChatAttachmentResponse:
    vid = (visitor_id or "anonymous").strip()[:64]
    svc = PublicChatAttachmentService(_memory_dir())
    try:
        row = svc.save(file, visitor_id=vid, files_in_message=max(1, files_in_message))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ChatAttachmentResponse(**row)


@app.get("/api/public/platform-version")
def public_platform_version() -> dict:
    """Foundation F5 — read-only manifest for update channel / compatibility checks."""
    from app.integration.platform_version import build_platform_version_payload

    return build_platform_version_payload(brain_version=BRAIN_VERSION)


@app.get("/api/public/genesis-ai/greeting")
def genesis_ai_greeting(visitor_id: str = "anonymous") -> dict:
    packages = _ctx().sales.packages()
    svc = _genesis_service(packages)
    return {"greeting": svc.greeting(visitor_id=visitor_id[:64])}


@app.get("/api/public/execution/preview/{workspace_id}")
@app.get("/api/public/execution/preview/{workspace_id}/{asset_path:path}")
def public_execution_preview(
    workspace_id: str,
    asset_path: str = "",
    visitor_id: str = "",
) -> FileResponse:
    """Product Truth — site preview openable from /site chat CTA."""
    from app.execution.preview import serve_preview

    return serve_preview(_memory_dir(), workspace_id, visitor_id[:64], asset_path)


@app.get("/api/public/execution/workspace/{workspace_id}/files/{file_path:path}")
def public_execution_workspace_file(
    workspace_id: str,
    file_path: str,
    visitor_id: str = "",
) -> FileResponse:
    """Product Truth — reports and summaries from document analysis."""
    from app.execution.preview import serve_workspace_file

    return serve_workspace_file(_memory_dir(), workspace_id, visitor_id[:64], file_path)


@app.get("/api/public/genesis-ai/status")
def genesis_ai_status() -> dict:
    """Lightweight status — AI Workforce, not OpenAI-only."""
    load_local_env()
    st = GenesisAISetupService().status()
    payload = {
        "name": "Vector",
        "genesis_ready": st["genesis_ready"],
        "workforce_tier": st["workforce_tier"],
        "workforce": {
            "tier": st["workforce_tier"],
            "cloud_employees_ready": st["cloud_employees_ready"],
            "employees": st["employees"],
        },
        "llm_configured": st["llm_configured"],
        "intelligence_tier": st["workforce_tier"],
        "intelligence_active": st["intelligence_active"],
        "mode": "genesis",
        "setup_wizard_available": st["setup_wizard_available"],
        "hi_build": BRAIN_VERSION,
        "brain_version": BRAIN_VERSION,
        "frontend_build_expected": BRAIN_VERSION,
        "voice_build": VOICE_BUILD,
        "tts": GenesisTtsService().status_payload(),
    }
    if is_production():
        payload["setup_wizard_available"] = False
        payload["workforce"] = {
            "tier": st["workforce_tier"],
            "cloud_employees_ready": st["cloud_employees_ready"],
        }
    return payload


@app.get("/api/public/genesis-ai/tts/status")
def genesis_tts_status() -> dict:
    return GenesisTtsService().status_payload()


@app.post("/api/public/genesis-ai/tts")
def genesis_tts_synthesize(request: TtsRequest):
    svc = GenesisTtsService()
    result = svc.synthesize(request.text, speed=request.speed, locale=request.locale)
    if not result:
        raise HTTPException(
            status_code=503,
            detail="Cloud TTS unavailable — use browser fallback",
        )
    return StreamingResponse(
        io.BytesIO(result.audio),
        media_type=result.content_type,
        headers={
            "X-Genesis-TTS-Provider": result.provider_id,
            "Cache-Control": "no-store",
        },
    )


@app.get("/api/owner/genesis-ai/setup", response_model=GenesisAISetupStatus)
def owner_genesis_ai_setup_status() -> GenesisAISetupStatus:
    return GenesisAISetupStatus(**GenesisAISetupService().status())


@app.post("/api/owner/genesis-ai/setup", response_model=GenesisAISetupResponse)
def owner_genesis_ai_setup(body: GenesisAISetupRequest) -> GenesisAISetupResponse:
    try:
        result = GenesisAISetupService().configure(
            provider=body.provider,
            api_key=body.api_key,
            model=body.model,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GenesisAISetupResponse(**result)


@app.get("/api/modules", response_model=ModulesResponse)
def get_modules() -> ModulesResponse:
    raw = _ctx().modules.list_modules()
    return ModulesResponse(modules=[ModuleStatus(**m) for m in raw])


@app.get("/api/queue", response_model=QueueStats)
def get_queue() -> QueueStats:
    return _ctx().tasks.queue_stats()


@app.get("/api/activity", response_model=ActivityResponse)
def get_activity(limit: int = 20) -> ActivityResponse:
    events = _ctx().tasks.recent_activity(limit=limit)
    return ActivityResponse(events=events)


@app.get("/api/tasks", response_model=TasksResponse)
def list_tasks() -> TasksResponse:
    tasks = _ctx().tasks.list_tasks()
    return TasksResponse(tasks=tasks)


@app.post("/api/tasks", response_model=TaskCreatedResponse)
def create_task(request: CreateTaskRequest) -> TaskCreatedResponse:
    task_id = _ctx().tasks.create_task(request)
    return TaskCreatedResponse(task_id=task_id)


@app.post("/api/tasks/run-next", response_model=TaskItem | None)
def run_next_task():
    return _ctx().tasks.run_next()


@app.post("/api/tasks/{task_id}/cancel", response_model=ControlResponse)
def cancel_task(task_id: str) -> ControlResponse:
    ok = _ctx().tasks.cancel(task_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Task not found or not cancellable")
    return ControlResponse(ok=True, action="cancel", message=f"Task {task_id} cancelled")


@app.post("/api/control/pause", response_model=ControlResponse)
def control_pause() -> ControlResponse:
    _ctx().adapter.pause()
    set_brain_paused(True)
    return ControlResponse(ok=True, action="pause", message="Brain paused — run_next disabled")


@app.post("/api/control/resume", response_model=ControlResponse)
def control_resume() -> ControlResponse:
    _ctx().adapter.resume()
    set_brain_paused(False)
    return ControlResponse(ok=True, action="resume", message="Brain resumed")


@app.get("/api/factory/intents", response_model=FactoryIntentsResponse)
def list_factory_intents() -> FactoryIntentsResponse:
    items = _ctx().factory_intent.list_intents()
    return FactoryIntentsResponse(intents=items)


@app.post("/api/factory/intent", response_model=FactoryIntentResponse)
def submit_factory_intent(request: FactoryIntentRequest) -> FactoryIntentResponse:
    if request.product_type != "landing-page":
        raise HTTPException(
            status_code=400,
            detail="Пока доступен только Landing Page. Остальные типы — скоро.",
        )
    result = _ctx().factory_intent.submit(request)
    return FactoryIntentResponse(**result)


@app.get("/api/sales/packages", response_model=SalesPackagesResponse)
def list_sales_packages(
    market: str | None = None,
    visitor_id: str | None = None,
    city: str | None = None,
    text: str | None = None,
) -> SalesPackagesResponse:
    checkout = _ctx().sales.checkout_packages(
        market_code=market,
        visitor_id=visitor_id,
        city=city,
        extra_text=text,
    )
    return SalesPackagesResponse(
        packages=[SalesPackage(**p) for p in checkout["packages"]],
        currency=checkout.get("currency"),
        symbol=checkout.get("symbol"),
        market_code=checkout.get("market_code"),
        delivery_support=checkout.get("delivery_support"),
    )


@app.get("/api/sales/brand-styles")
def list_brand_styles(lang: str | None = None) -> dict:
    """Path A Brand Style brief — additive to niche defaults (auto = keep niche)."""
    from app.factory.brand_style import list_brand_styles as _list

    code = (lang or "en").strip().lower()[:2] or "en"
    return {"ok": True, "styles": _list(lang=code)}


@app.get("/api/sales/delivery-matrix", response_model=PathADeliveryMatrixResponse)
def path_a_delivery_matrix() -> PathADeliveryMatrixResponse:
    """Path A market support matrix: currency / UI / legal / Production|Beta."""
    from app.factory.market_delivery import list_path_a_delivery_matrix

    return PathADeliveryMatrixResponse(markets=list_path_a_delivery_matrix())


@app.get("/api/public/pricing")
def public_pricing(market: str | None = None) -> dict:
    return _ctx().pricing_display.get_display(market_code=market)


@app.get("/api/public/bots/pricing")
def public_bots_pricing(market: str | None = None) -> dict:
    """AI Business Bots catalog — market-local setup + monthly (separate from Landing)."""
    from app.integration.pricing_engine import list_bot_packages

    return list_bot_packages(market or "DE")


def _legal():
    from app.legal.service import LegalFoundationService

    return LegalFoundationService(_memory_dir())


@app.get("/api/public/legal/status")
def public_legal_status() -> dict:
    return _legal().status()


@app.get("/api/public/legal/operator")
def public_legal_operator() -> dict:
    """Seller identity for checkout trust (Impressum preview) — no secrets."""
    return _legal().operator_preview()


@app.get("/api/public/legal/documents")
def public_legal_documents() -> dict:
    return {"documents": _legal().documents_catalog()}


@app.get("/api/public/legal/documents/{doc_id}")
def public_legal_document(doc_id: str, locale: str = "de") -> dict:
    normalized = doc_id.replace("-", "_")
    doc = _legal().document(normalized, locale=locale)
    if not doc:
        raise HTTPException(status_code=404, detail="document_not_found")
    return doc


@app.get("/api/public/trust")
def public_trust() -> dict:
    return _legal().trust()


@app.get("/api/public/legal/handoff/one-time")
def public_handoff_one_time() -> dict:
    return _legal().handoff_one_time()


@app.get("/api/public/legal/handoff/subscription")
def public_handoff_subscription() -> dict:
    return _legal().handoff_subscription()


@app.get("/api/public/delivery")
def public_delivery(visitor_id: str, locale: str = "ru") -> dict:
    from app.integration.delivery_engine.gate import delivery_engine_enabled

    if not delivery_engine_enabled(_memory_dir()):
        raise HTTPException(status_code=404, detail="delivery_engine_disabled")
    from app.integration.delivery_engine import DeliveryEngine

    return DeliveryEngine(_memory_dir()).get_public_state(visitor_id, locale=locale)


@app.get("/api/public/project")
def public_project(visitor_id: str, locale: str = "ru") -> dict:
    from app.integration.project_platform.service import ProjectPlatformService

    return ProjectPlatformService(_memory_dir()).get_for_visitor(visitor_id, locale=locale)


@app.post("/api/public/project/activate")
def public_project_activate(body: dict) -> dict:
    from app.integration.project_platform.service import ProjectPlatformService

    visitor_id = str(body.get("visitor_id") or "").strip()[:64]
    title = str(body.get("title") or "Мой проект").strip()[:120]
    service_id = str(body.get("service_id") or "website").strip()[:64]
    if not visitor_id:
        raise HTTPException(status_code=400, detail="visitor_id_required")
    return ProjectPlatformService(_memory_dir()).activate_project(
        visitor_id,
        title=title,
        service_id=service_id,
    )


@app.get("/api/public/legal/locale-registry")
def public_legal_locale_registry() -> dict:
    from app.legal.locale_registry import localization_horizon_payload

    return localization_horizon_payload()


@app.post("/api/public/pricing-event", response_model=PricingEventResponse)
def public_pricing_event(body: PricingEventRequest) -> PricingEventResponse:
    _ctx().pricing_display.log_event(
        event=body.event,
        tier_id=body.tier_id,
        page=body.page,
        meta=body.meta,
    )
    return PricingEventResponse()


@app.get("/api/public/path-a-funnel", response_model=PathAFunnelDashboard)
def public_path_a_funnel() -> PathAFunnelDashboard:
    """CEO / diagnostics: Path A storefront conversion funnel aggregates."""
    return PathAFunnelDashboard(**_ctx().pricing_display.path_a_funnel_summary())


@app.get("/api/public/visual-experience", response_model=VisualExperiencePreviewResponse)
def public_visual_experience(
    niche: str | None = None,
    specialization: str | None = None,
    tier: str = "business",
    locale: str = "en",
) -> VisualExperiencePreviewResponse:
    """Adaptive VXP preview for Path A order wizard (still / motion — never empty)."""
    from app.integration.path_a_visual_preview import resolve_path_a_visual_preview
    from app.integration.locale_service import resolve_generation_language

    exp = resolve_path_a_visual_preview(
        niche_id=niche,
        tier=tier,
        specialization=specialization,
        locale=resolve_generation_language(locale),
    )
    return VisualExperiencePreviewResponse(
        ok=bool(exp.get("ok", True)),
        engine=str(exp.get("engine") or "visual_experience"),
        mode=str(exp.get("mode") or "none"),
        tier=str(exp.get("tier") or tier),
        niche_id=exp.get("niche_id"),
        product_id=exp.get("product_id"),
        specialization_id=exp.get("specialization_id"),
        label=exp.get("label"),
        preview=exp.get("preview"),
        preview_url=exp.get("preview_url"),
        reason=exp.get("reason"),
        cta=exp.get("cta") if isinstance(exp.get("cta"), dict) else None,
        hotspots=list(exp.get("hotspots") or []) if isinstance(exp.get("hotspots"), list) else [],
        never_empty=bool(exp.get("never_empty", True)),
    )


@app.get("/api/public/niches")
def public_niches() -> dict:
    """Known Path A niches + specialization ids for the order wizard."""
    from app.factory.niche_profiles import known_niche_ids, resolve_niche_profile
    from app.factory.research_3d.visual_experience_registry import load_specialization_map

    # Family Care / Familienpsychologie — removed from public order UI (not a sellable demo).
    _PUBLIC_NICHE_BLOCKLIST = frozenset(
        {
            "family_psychology",
            "family_care",
            "familienpsychologie",
            "psychology",
        }
    )

    niches = []
    for nid in known_niche_ids():
        if nid in _PUBLIC_NICHE_BLOCKLIST or "family" in nid:
            continue
        profile = resolve_niche_profile(nid)
        niches.append({"id": nid, "label_de": profile.label_de})
    specs = []
    data = load_specialization_map()
    for sid, row in (data.get("specializations") or {}).items():
        if not isinstance(row, dict):
            continue
        specs.append(
            {
                "id": sid,
                "niche": row.get("niche"),
                "label": sid.replace("_", " "),
            }
        )
    return {"niches": niches, "specializations": specs}


@app.get("/api/public/solution-catalog")
def public_solution_catalog(locale: str = "de") -> dict:
    """Digital Business Creator catalog — solutions by business, not templates."""
    from app.factory.commerce_model import public_commerce_packages
    from app.factory.solution_catalog import catalog_payload

    payload = catalog_payload(locale=locale)
    payload["commerce_packages"] = public_commerce_packages()
    return payload


@app.post("/api/public/business-interview/parse")
def public_business_interview_parse(body: dict) -> dict:
    """Parse dialogue/form → Interview + clarifying questions + Intelligence preview."""
    from app.factory.business_intelligence import resolve_business_intelligence
    from app.factory.business_interview import interview_from_payload, interview_to_contacts
    from app.factory.interview_clarify import (
        DREAM_PROMPT,
        DREAM_PROMPT_DE,
        build_clarify_session,
    )

    payload = body if isinstance(body, dict) else {}
    iv = interview_from_payload(payload)
    contacts = interview_to_contacts(iv, {})
    niche = str(iv.niche_hint or payload.get("niche") or "")
    session = build_clarify_session(
        niche_id=niche,
        answered=iv.clarify_answers,
        free_text=iv.free_text or iv.about,
        team=iv.team,
        dream=iv.dream_vision or str(payload.get("dream_vision") or ""),
        site_jobs=iv.site_jobs,
    )
    bi = resolve_business_intelligence(
        niche_id=niche,
        company_name=iv.company_name,
        city=iv.city,
        interview=iv.as_dict(),
        contacts=contacts,
    )
    return {
        "interview": iv.as_dict(),
        "intelligence": bi.as_dict(),
        "recommended_components": [c.as_dict() for c in bi.components],
        "clarifying_questions": [q.as_dict() for q in session.questions],
        "clarify_session": session.as_dict(),
        "dream_prompt": DREAM_PROMPT,
        "dream_prompt_de": DREAM_PROMPT_DE,
        "technical_decisions": bi.technical_decisions or session.technical,
        "law": (
            "Factory does not ask technical questions. "
            "It asks about the business — then designs the digital solution."
        ),
        "canon": "Digital Business Creator",
    }


# --- M2 Universal Identity (client API — human-facing responses, plain language) ---


def _customer_identity():
    from app.integration.customer_identity import CustomerIdentityService

    return CustomerIdentityService(_memory_dir())


@app.post("/api/client/register")
def client_register(body: ClientRegisterRequest) -> dict:
    """Start registration — sends email verification code. Does not create session yet."""
    return _customer_identity().start_registration(
        name=body.name,
        email=body.email,
        password=body.password,
        locale=body.locale,
        country=body.country,
        prior_visitor_id=body.visitor_id,
    )


@app.post("/api/client/register/confirm")
def client_register_confirm(body: ClientRegisterConfirmRequest) -> dict:
    """Confirm email code → create personal office account + token."""
    return _customer_identity().confirm_registration(
        email=body.email,
        code=body.code,
    )


@app.post("/api/client/login")
def client_login(body: ClientLoginRequest) -> dict:
    return _customer_identity().login(email=body.email, password=body.password)


@app.get("/api/client/me")
def client_me(request: Request) -> dict:
    from app.integration.customer_identity.auth import require_client

    payload = require_client(request)
    return _customer_identity().me(str(payload["sub"]))


@app.get("/api/client/vector-coaching")
def client_vector_coaching(request: Request) -> dict:
    """Ephemeral Vector coaching notifications — not a chat."""
    from app.integration.customer_identity.auth import require_client
    from app.integration.vector.coaching_notifications import coaching_payload_for_me

    payload = require_client(request)
    customer_id = str(payload["sub"])
    me = _customer_identity().me(customer_id)
    email = str(payload.get("email") or me.get("email") or "").strip()
    orders = _ctx().sales.list_orders_for_customer(
        customer_id=customer_id, email=email or None, limit=50
    )
    return {"ok": True, **coaching_payload_for_me(me, orders)}


@app.get("/api/client/orders")
def client_orders_list(request: Request) -> dict:
    """Cabinet: orders owned by the logged-in customer (by customer_id / email)."""
    from app.integration.customer_identity.auth import require_client

    payload = require_client(request)
    customer_id = str(payload["sub"])
    email = str(payload.get("email") or "").strip()
    if not email:
        try:
            me = _customer_identity().me(customer_id)
            email = str((me.get("account") or {}).get("email") or "")
        except Exception:
            email = ""
    orders = _ctx().sales.list_orders_for_customer(
        customer_id=customer_id, email=email or None, limit=50
    )
    return {"ok": True, "orders": orders}


@app.get("/api/client/welcome")
def client_welcome(request: Request) -> dict:
    from app.integration.customer_identity.auth import require_client

    payload = require_client(request)
    return _customer_identity().get_welcome(str(payload["sub"]))


@app.post("/api/client/welcome/advance")
def client_welcome_advance(request: Request) -> dict:
    from app.integration.customer_identity.auth import require_client

    payload = require_client(request)
    return _customer_identity().advance_welcome(str(payload["sub"]))


@app.post("/api/client/welcome/answer")
def client_welcome_answer(request: Request, body: ClientWelcomeAnswerRequest) -> dict:
    from app.integration.customer_identity.auth import require_client

    payload = require_client(request)
    return _customer_identity().answer_welcome(
        str(payload["sub"]),
        answer=body.answer,
        skip=body.skip,
    )


@app.post("/api/client/merge-visitor")
def client_merge_visitor(request: Request, body: ClientMergeVisitorRequest) -> dict:
    from app.integration.customer_identity.auth import require_client

    payload = require_client(request)
    return _customer_identity().merge_visitor(str(payload["sub"]), visitor_id=body.visitor_id)


@app.get("/api/client/bots")
def client_bots_list(request: Request) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_ai_bots as wab
    from app.integration import workspace_channel_credentials as wcc
    from app.integration.meta_oauth_client import meta_oauth_configured

    payload = require_client(request)
    cid = str(payload["sub"])
    mem = _memory_dir()
    from app.integration.channel_engine.whatsapp_cloud import whatsapp_foundation_status

    return {
        "ok": True,
        "entitlements": wab.get_entitlements(mem, cid),
        "bots": wab.list_bots(mem, cid),
        "connections": wcc.list_connections(mem, cid),
        "meta_oauth_configured": meta_oauth_configured(),
        "whatsapp_foundation": whatsapp_foundation_status(),
    }


@app.post("/api/client/bots")
def client_bots_create(request: Request, body: ClientBotCreateRequest) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_ai_bots as wab

    payload = require_client(request)
    result = wab.create_bot(
        _memory_dir(),
        str(payload["sub"]),
        display_name=body.display_name,
        bot_config=body.bot_config,
        channels=body.channels,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("reason") or "create_failed")
    return result


@app.patch("/api/client/bots/{bot_id}")
def client_bots_update(request: Request, bot_id: str, body: ClientBotUpdateRequest) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_ai_bots as wab

    payload = require_client(request)
    patch = body.model_dump(exclude_none=True)
    result = wab.update_bot(_memory_dir(), str(payload["sub"]), bot_id, patch)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("reason") or "update_failed")
    return result


@app.get("/api/client/bots/order-draft")
def client_bots_order_draft_get(request: Request) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_ai_bots as wab

    payload = require_client(request)
    return wab.get_order_draft(_memory_dir(), str(payload["sub"]))


@app.put("/api/client/bots/order-draft")
def client_bots_order_draft_put(request: Request, body: ClientBotOrderDraftRequest) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_ai_bots as wab

    payload = require_client(request)
    return wab.save_order_draft(_memory_dir(), str(payload["sub"]), body.draft)


@app.post("/api/webhooks/telegram/{bot_id}")
async def telegram_bot_webhook(bot_id: str, request: Request) -> dict:
    """Inbound Telegram updates for paid AI Business Bots (Channel Engine → TelegramProvider)."""
    from app.integration.channel_engine import get_provider

    try:
        update = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_json") from None
    if not isinstance(update, dict):
        raise HTTPException(status_code=400, detail="invalid_update")
    provider = get_provider("telegram")
    if provider is None:
        raise HTTPException(status_code=503, detail="telegram_provider_unavailable")
    result = provider.receive(_memory_dir(), bot_id, update)
    if result.get("reason") == "bot_not_found":
        raise HTTPException(status_code=404, detail="bot_not_found")
    # Always 200 to Telegram when bot exists but message ignored
    safe = {
        k: v
        for k, v in result.items()
        if k not in ("reply_text", "normalized")
    }
    return {"ok": True, **safe}


@app.get("/api/webhooks/whatsapp")
async def whatsapp_webhook_verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
) -> PlainTextResponse:
    """Meta WhatsApp Cloud API subscription handshake (GET hub.verify_token)."""
    from app.integration.channel_engine import whatsapp_cloud as wa

    challenge = wa.verify_webhook_subscribe(
        mode=hub_mode,
        token=hub_verify_token,
        challenge=hub_challenge,
    )
    if challenge is None:
        raise HTTPException(status_code=403, detail="whatsapp_verify_failed")
    return PlainTextResponse(content=challenge)


@app.post("/api/webhooks/whatsapp")
async def whatsapp_webhook_receive(request: Request) -> dict:
    """WhatsApp Cloud API inbound — foundation ack only (no AI Employee Live)."""
    import json

    from app.integration.channel_engine import get_provider
    from app.integration.channel_engine import whatsapp_cloud as wa

    secret = wa.meta_app_secret()
    if not secret:
        raise HTTPException(status_code=503, detail="whatsapp_setup_required")
    raw = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not wa.verify_meta_signature(
        app_secret=secret, raw_body=raw, header_value=signature
    ):
        raise HTTPException(status_code=403, detail="invalid_signature")
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_json") from None
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid_json")
    provider = get_provider("whatsapp")
    if provider is None:
        raise HTTPException(status_code=503, detail="whatsapp_provider_unavailable")
    result = provider.receive(_memory_dir(), "", payload)
    return {
        "ok": True,
        "channel_type": "whatsapp",
        "live": False,
        "delivery": result.get("delivery") or "foundation_ack_only",
        "status": result.get("status"),
        "events": result.get("events"),
    }


@app.post("/api/client/bots/{bot_id}/chat")
def client_bot_chat_preview(request: Request, bot_id: str, body: dict | None = None) -> dict:
    """Cabinet test chat — same reply core as Telegram (no channel send)."""
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_ai_bots as wab
    from app.integration.workspace_bot_runtime import generate_bot_reply

    payload = require_client(request)
    cid = str(payload["sub"])
    bot = wab.get_bot(_memory_dir(), cid, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="bot_not_found")
    data = body if isinstance(body, dict) else {}
    message = str(data.get("message") or data.get("text") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message_required")
    reply = generate_bot_reply(
        bot,
        message,
        memory_dir=_memory_dir(),
        customer_id=cid,
        session_key=f"cabinet:{cid}:{bot_id}",
    )
    return {
        "ok": True,
        "bot_id": bot_id,
        "reply": reply.get("text"),
        "source": reply.get("source"),
        "intent": reply.get("intent"),
    }


@app.post("/api/client/bots/telegram/connect")
def client_bots_telegram_connect(
    request: Request, body: ClientBotTelegramConnectRequest
) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_ai_bots as wab
    from app.integration import workspace_channel_credentials as wcc

    payload = require_client(request)
    cid = str(payload["sub"])
    mem = _memory_dir()
    result = wcc.save_telegram_token(
        mem,
        cid,
        bot_id=body.bot_id,
        token=body.token,
        connection_id=body.connection_id,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("reason") or "connect_failed")
    wab.update_bot(mem, cid, body.bot_id, {"status": "online"})
    return result


@app.get("/api/client/bots/website-chat/status")
def client_website_chat_status(request: Request) -> dict:
    """Website Chat channel status — commercial Live when COMMERCIAL_LIVE=True."""
    from app.integration.customer_identity.auth import require_client
    from app.integration import website_chat_connector as wch

    require_client(request)
    return wch.commercial_status()


@app.post("/api/client/bots/{bot_id}/website-chat/connect")
def client_website_chat_connect(request: Request, bot_id: str, body: dict | None = None) -> dict:
    """Create Website Chat connection for owned bot (Live channel)."""
    from app.integration.customer_identity.auth import require_client
    from app.integration import website_chat_connector as wch
    from app.integration.workspace_bot_runtime import public_api_base

    payload = require_client(request)
    data = body if isinstance(body, dict) else {}
    result = wch.create_website_channel(
        _memory_dir(),
        str(payload["sub"]),
        bot_id=bot_id,
        site_ref=str(data.get("site_ref") or "") or None,
        site_label=str(data.get("site_label") or "") or None,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("reason") or "connect_failed")
    embed = result.get("embed") or {}
    result["embed"] = wch.generate_embed_snippet(
        str((result.get("connection") or {}).get("public_key") or ""),
        api_base=public_api_base(),
    ) or embed
    return result


@app.get("/api/client/bots/website-chat/connections")
def client_website_chat_list(request: Request) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import website_chat_connector as wch

    payload = require_client(request)
    return {
        "ok": True,
        "commercial": wch.commercial_status(),
        "connections": wch.list_connections(_memory_dir(), str(payload["sub"])),
    }


@app.post("/api/client/bots/website-chat/{connection_id}/disconnect")
def client_website_chat_disconnect(request: Request, connection_id: str) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import website_chat_connector as wch

    payload = require_client(request)
    result = wch.disconnect_website_channel(
        _memory_dir(), str(payload["sub"]), connection_id
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("reason") or "disconnect_failed")
    return result


@app.post("/api/client/bots/website-chat/{connection_id}/reconnect")
def client_website_chat_reconnect(request: Request, connection_id: str) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import website_chat_connector as wch
    from app.integration.workspace_bot_runtime import public_api_base

    payload = require_client(request)
    result = wch.reconnect_website_channel(
        _memory_dir(), str(payload["sub"]), connection_id
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("reason") or "reconnect_failed")
    key = str((result.get("connection") or {}).get("public_key") or "")
    result["embed"] = wch.generate_embed_snippet(key, api_base=public_api_base())
    return result


@app.post("/api/public/website-chat/{public_key}/message")
def public_website_chat_message(public_key: str, body: dict | None = None) -> dict:
    """Public Website Chat widget inbound — Live when COMMERCIAL_LIVE=True."""
    from app.integration import website_chat_connector as wch

    data = body if isinstance(body, dict) else {}
    result = wch.handle_website_chat_message(
        _memory_dir(),
        public_key,
        str(data.get("message") or data.get("text") or ""),
        visitor_id=str(data.get("visitor_id") or "") or None,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("reason") or "chat_failed")
    return {
        "ok": True,
        "reply": result.get("reply"),
        "source": result.get("source"),
        "commercial_live": result.get("commercial_live"),
    }


@app.get("/api/public/website-chat/widget.js")
def public_website_chat_widget_js():
    """Serve spike widget JS from frontend public (or embedded fallback)."""
    from fastapi.responses import FileResponse, Response

    candidates = [
        _Path(__file__).resolve().parents[2] / "frontend" / "public" / "widget" / "website-chat.js",
        _Path(__file__).resolve().parents[3] / "dashboard" / "frontend" / "public" / "widget" / "website-chat.js",
    ]
    for path in candidates:
        if path.is_file():
            return FileResponse(path, media_type="application/javascript; charset=utf-8")
    return Response(
        content="console.error('website-chat widget missing');",
        media_type="application/javascript",
        status_code=404,
    )


@app.get("/api/public/website-chat/harness")
def public_website_chat_harness(key: str = "", label: str = "Demo website", tenant: str = ""):
    """Browser E2E harness — not commercial Live."""
    from fastapi.responses import HTMLResponse
    from html import escape

    key_safe = escape(str(key or "").strip())
    label_safe = escape(str(label or "Demo website"))
    tenant_safe = escape(str(tenant or ""))
    html = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Website Chat Live · {label_safe}</title>
  <style>
    body{{margin:0;font-family:system-ui,Segoe UI,sans-serif;background:#071018;color:#e2e8f0}}
    main{{max-width:720px;margin:0 auto;padding:48px 24px}}
    .card{{border:1px solid rgba(255,255,255,.1);border-radius:24px;padding:24px;background:rgba(255,255,255,.03)}}
    .muted{{color:#94a3b8;font-size:14px}}
    .ok{{color:#a7f3d0;font-size:12px}}
    code{{font-size:12px;color:#64748b}}
  </style>
</head>
<body>
  <main>
    <p class="muted">Virtus Website Chat · Live preview</p>
    <h1>{label_safe}</h1>
    <p class="muted">Open Chat and send a message. Telegram + Website Chat are Live.</p>
    {"<p class='muted' data-testid='tenant-label'>Tenant: " + tenant_safe + "</p>" if tenant_safe else ""}
    <div class="card">
      <p class="ok">Commercial status: Live — WhatsApp / Instagram / Messenger remain Coming Soon.</p>
      <p><code data-testid="public-key">{key_safe or "(missing key)"}</code></p>
    </div>
  </main>
  {"<script src='/api/public/website-chat/widget.js' data-virtus-key='" + key_safe + "' data-endpoint='/api/public/website-chat/" + key_safe + "/message' async></script>" if key_safe else ""}
</body>
</html>"""
    return HTMLResponse(html)


@app.post("/api/client/bots/connections/{connection_id}/test")
def client_bots_connection_test(request: Request, connection_id: str) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_channel_credentials as wcc

    payload = require_client(request)
    return wcc.test_connection(_memory_dir(), str(payload["sub"]), connection_id)


@app.post("/api/client/bots/connections/disconnect")
def client_bots_connection_disconnect(
    request: Request, body: ClientBotDisconnectRequest
) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_channel_credentials as wcc

    payload = require_client(request)
    result = wcc.disconnect(_memory_dir(), str(payload["sub"]), body.connection_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("reason") or "disconnect_failed")
    return result


@app.get("/api/client/inbox/threads")
def client_inbox_threads(
    request: Request,
    channel: str | None = None,
    unread: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Unified Inbox list — Telegram + Website Chat sessions for this workspace."""
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_inbox_service as inbox

    payload = require_client(request)
    return inbox.list_threads(
        _memory_dir(),
        str(payload["sub"]),
        channel=channel,
        unread_only=str(unread or "").strip().lower() in ("1", "true", "yes"),
        q=q,
        limit=limit,
        offset=offset,
    )


@app.get("/api/client/inbox/threads/{thread_id}")
def client_inbox_thread_get(request: Request, thread_id: str) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_inbox_service as inbox

    payload = require_client(request)
    result = inbox.get_thread(_memory_dir(), str(payload["sub"]), thread_id)
    if not result.get("ok"):
        reason = str(result.get("reason") or "not_found")
        status = 403 if reason == "forbidden" else 404
        raise HTTPException(status_code=status, detail=reason)
    return result


@app.post("/api/client/inbox/threads/{thread_id}/read")
def client_inbox_thread_read(request: Request, thread_id: str) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_inbox_service as inbox

    payload = require_client(request)
    result = inbox.mark_read(_memory_dir(), str(payload["sub"]), thread_id)
    if not result.get("ok"):
        reason = str(result.get("reason") or "not_found")
        status = 403 if reason == "forbidden" else 404
        raise HTTPException(status_code=status, detail=reason)
    return result


@app.post("/api/client/inbox/threads/{thread_id}/messages")
async def client_inbox_thread_send(request: Request, thread_id: str) -> dict:
    """Human reply via Channel Engine (Telegram). Website Chat push not supported yet."""
    from app.integration.customer_identity.auth import require_client
    from app.integration import workspace_inbox_service as inbox

    payload = require_client(request)
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    text = str(body.get("text") or body.get("message") or "")
    result = inbox.send_reply(_memory_dir(), str(payload["sub"]), thread_id, text)
    if not result.get("ok"):
        reason = str(result.get("reason") or "send_failed")
        if reason in ("forbidden",):
            raise HTTPException(status_code=403, detail=reason)
        if reason in ("not_found", "invalid_thread"):
            raise HTTPException(status_code=404, detail=reason)
        if reason == "CHANNEL_SEND_UNSUPPORTED":
            raise HTTPException(status_code=409, detail=reason)
        raise HTTPException(status_code=400, detail=reason)
    return result


@app.post("/api/client/bots/meta/oauth/start")
def client_bots_meta_oauth_start(
    request: Request, body: ClientBotMetaOAuthStartRequest
) -> dict:
    from app.integration.customer_identity.auth import require_client
    from app.integration.meta_oauth_client import start_meta_oauth

    payload = require_client(request)
    result = start_meta_oauth(
        customer_id=str(payload["sub"]),
        bot_id=body.bot_id,
        channel=body.channel,
    )
    if not result.get("ok"):
        status = 503 if result.get("reason") == "meta_not_configured" else 400
        raise HTTPException(status_code=status, detail=result.get("reason") or "oauth_failed")
    return result


@app.get("/api/client/bots/meta/oauth/callback")
def client_bots_meta_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> Response:
    from fastapi.responses import RedirectResponse
    from app.integration.meta_oauth_client import complete_meta_oauth_callback

    frontend = (
        os.getenv("GENESIS_PUBLIC_URL", "").strip().rstrip("/")
        or "http://127.0.0.1:3000"
    )
    dash = f"{frontend}/client/bots"
    if error:
        return RedirectResponse(f"{dash}?meta=error&reason={error}", status_code=302)
    if not code or not state:
        return RedirectResponse(f"{dash}?meta=error&reason=missing_code", status_code=302)
    result = complete_meta_oauth_callback(_memory_dir(), code=code, state=state)
    if not result.get("ok"):
        reason = str(result.get("reason") or "oauth_failed")
        return RedirectResponse(f"{dash}?meta=error&reason={reason}", status_code=302)
    bot_id = str(result.get("bot_id") or "")
    return RedirectResponse(
        f"{dash}?meta=ok&bot={bot_id}&channel={result.get('channel') or ''}",
        status_code=302,
    )


@app.post("/api/sales/orders", response_model=SalesOrderCreatedResponse)
def create_sales_order(request: Request, body: SalesOrderCreateRequest) -> SalesOrderCreatedResponse:
    from app.integration.receipt_email_service import ReceiptEmailService

    data = body.model_dump()
    package_id = str(data.get("package_id") or "")
    product_kind = str(data.get("product_kind") or "")
    if product_kind == "bot" or package_id.startswith("bot_"):
        from app.integration.customer_identity.auth import require_client

        payload = require_client(request)
        data["customer_id"] = str(payload["sub"])
        data["workspace_id"] = str(data.get("workspace_id") or payload["sub"])
        data["product_kind"] = "bot"
    if product_kind == "shop" or package_id == "ecommerce_shop":
        from app.integration.customer_identity.auth import require_client

        payload = require_client(request)
        data["customer_id"] = str(payload["sub"])
        data["workspace_id"] = str(data.get("workspace_id") or payload["sub"])
        data["product_kind"] = "shop"
        data["package_id"] = "ecommerce_shop"
    try:
        result = _ctx().sales.create_order(data)
    except ValueError as exc:
        msg = str(exc)
        if msg in ("customer_id_required_for_bot", "customer_id_required_for_shop"):
            raise HTTPException(status_code=401, detail=msg) from exc
        if msg == "demo_payment_disabled":
            raise HTTPException(
                status_code=403,
                detail="Demo Payment Bridge отключён в Production",
            ) from exc
        if msg in ("cinematic_product_unavailable", "cinematic_product_misconfigured"):
            raise HTTPException(status_code=400, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc
    order = _ctx().sales.get_order(result["order_id"])
    if order and order.get("email"):
        ReceiptEmailService().send_order_received(order=order)
    return SalesOrderCreatedResponse(**result)


@app.get("/api/commerce/cinematic-experience")
def commerce_cinematic_experience(lang: str = "de") -> dict:
    """Client-facing Cinematic AI Experience card — no internal budget / provider costs."""
    from app.integration.cinematic_media import public_catalog

    return public_catalog(lang=lang)


@app.get("/api/sales/orders/{order_id}/media-budget")
def sales_order_media_budget(order_id: str, dry_run: bool = False) -> dict:
    """Owner/admin view of cinematic media budget (internal numbers OK here)."""
    from app.integration.cinematic_media import admin_media_view, dry_run_scene_budget, provider_board

    order = _ctx().sales.get_order(order_id)
    view = admin_media_view(order)
    view["providers"] = provider_board()
    if dry_run and order:
        view["dry_run"] = dry_run_scene_budget(
            {
                "niche": order.get("niche"),
                "business_name": order.get("business_name"),
                "city": order.get("city"),
                "description": order.get("description"),
                "product_kind": order.get("product_kind"),
                "brand_style": order.get("brand_style"),
                "cinematic_enabled": order.get("cinematic_enabled"),
                "style": order.get("brand_style") or "cinematic_realistic",
            },
            order=order,
        )
    return view


@app.post("/api/commerce/cinematic-dry-run")
def commerce_cinematic_dry_run(body: dict | None = None) -> dict:
    """Form → Scene Director → cost estimate → ALLOW/BLOCK. Never submits live jobs."""
    from app.integration.cinematic_media import dry_run_scene_budget

    payload = body or {}
    order = None
    order_id = str(payload.get("order_id") or "").strip()
    if order_id:
        order = _ctx().sales.get_order(order_id)
    return dry_run_scene_budget(payload, order=order, provider_id=payload.get("provider_id"))


@app.post("/api/sales/orders/{order_id}/media-generation/request")
def sales_order_media_generation_request(order_id: str, body: dict | None = None) -> dict:
    """Future generation entry — budget gate + disabled providers (no live network)."""
    from app.integration.cinematic_media import request_generation

    order = _ctx().sales.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")
    payload = body or {}
    mem = _memory_dir()
    result = request_generation(
        order,
        mem,
        provider_id=str(payload.get("provider_id") or "kie"),
        capability=str(payload.get("capability") or "IMAGE_TO_VIDEO"),
        estimated_cost_eur=(
            float(payload["estimated_cost_eur"])
            if payload.get("estimated_cost_eur") is not None
            else None
        ),
        prompt=str(payload.get("prompt") or ""),
    )
    _ctx().sales._save_order(order)
    return result


def _client_store_identity(request: Request) -> tuple[str, str | None]:
    from app.integration.customer_identity.auth import require_client

    payload = require_client(request)
    customer_id = str(payload["sub"])
    email = str(payload.get("email") or "").strip()
    if not email:
        try:
            me = _customer_identity().me(customer_id)
            email = str((me.get("account") or {}).get("email") or "")
        except Exception:
            email = ""
    return customer_id, email or None


def _client_store_http_error(exc: ValueError) -> HTTPException:
    msg = str(exc)
    if msg in ("forbidden", "not_a_website_order"):
        return HTTPException(status_code=403, detail=msg)
    if msg in (
        "order_not_found",
        "product_not_found",
        "version_not_found",
        "catalog_product_not_found",
        "image_not_found",
    ):
        return HTTPException(status_code=404, detail=msg)
    return HTTPException(status_code=400, detail=msg)


def _store_catalog():
    from app.integration.store_admin import StoreCatalogService

    return StoreCatalogService(_memory_dir())


def _store_design():
    from app.integration.store_admin import StoreDesignService

    return StoreDesignService(_memory_dir())


def _assert_store_admin_access(request: Request, order_id: str) -> dict:
    customer_id, email = _client_store_identity(request)
    return _ctx().sales.get_store_for_customer(
        order_id, customer_id=customer_id, email=email
    )


@app.get("/api/client/stores/{order_id}")
def client_store_get(request: Request, order_id: str) -> dict:
    """AI Store cabinet shell — brief + pipeline + publish metadata."""
    customer_id, email = _client_store_identity(request)
    try:
        return _ctx().sales.get_store_for_customer(
            order_id, customer_id=customer_id, email=email
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/status")
def client_store_status(request: Request, order_id: str) -> dict:
    customer_id, email = _client_store_identity(request)
    try:
        return _ctx().sales.get_store_status_for_customer(
            order_id, customer_id=customer_id, email=email
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/log")
def client_store_log(request: Request, order_id: str) -> dict:
    customer_id, email = _client_store_identity(request)
    try:
        return _ctx().sales.get_store_log_for_customer(
            order_id, customer_id=customer_id, email=email
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/regenerate")
def client_store_regenerate(request: Request, order_id: str) -> dict:
    customer_id, email = _client_store_identity(request)
    try:
        return _ctx().sales.regenerate_shop_store(
            order_id, customer_id=customer_id, email=email
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/publish")
def client_store_publish(request: Request, order_id: str) -> dict:
    customer_id, email = _client_store_identity(request)
    try:
        return _ctx().sales.publish_shop_store(
            order_id, customer_id=customer_id, email=email
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/rollback")
async def client_store_rollback(request: Request, order_id: str) -> dict:
    customer_id, email = _client_store_identity(request)
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    try:
        version = int(payload.get("version"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="version_required") from exc
    try:
        return _ctx().sales.rollback_shop_store(
            order_id, version=version, customer_id=customer_id, email=email
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/live")
@app.get("/api/client/stores/{order_id}/live/{asset_path:path}")
def client_store_live(order_id: str, asset_path: str = "index.html"):
    """Public Open Store — published HTML + assets (no CMS)."""
    from app.factory.store_factory import StoreFactoryService

    try:
        order = _ctx().sales.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if str(order.get("package_id") or "").strip().lower() != "ecommerce_shop":
            raise ValueError("not_a_shop_order")
        product_id = str(order.get("product_id") or "").strip()
        if not product_id:
            raise ValueError("product_not_found")
        factory = StoreFactoryService(_memory_dir())
        rel = (asset_path or "index.html").strip() or "index.html"
        path = factory.resolve_live_file(product_id, rel)
        if path.suffix.lower() in (".html", ".htm"):
            html = factory.rewrite_live_html(
                path.read_text(encoding="utf-8"), order_id
            )
            return HTMLResponse(content=html)
        if path.suffix.lower() == ".css":
            from pathlib import PurePosixPath

            rel_dir = str(PurePosixPath(rel).parent)
            if rel_dir == ".":
                rel_dir = ""
            css = path.read_text(encoding="utf-8", errors="replace")
            css = factory.rewrite_live_urls(
                css, order_id=order_id, relative_dir=rel_dir
            )
            return Response(content=css, media_type="text/css; charset=utf-8")
        media = {
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".ico": "image/x-icon",
        }.get(path.suffix.lower(), "application/octet-stream")
        return FileResponse(path, media_type=media)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/enqueue-factory")
def client_store_enqueue_factory(request: Request, order_id: str) -> dict:
    """Run / re-check AI Store factory pipeline (idempotent when published)."""
    customer_id, email = _client_store_identity(request)
    try:
        _ctx().sales.get_store_for_customer(
            order_id, customer_id=customer_id, email=email
        )
        return _ctx().sales.enqueue_shop_factory(order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


# --- Store Admin R3.1.2 — Product Management (merchant catalog) ---


@app.get("/api/client/stores/{order_id}/admin/products")
def store_admin_list_products(
    request: Request, order_id: str, status: str | None = None, q: str | None = None
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        return _store_catalog().list_products(order_id, status=status, q=q)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/products")
async def store_admin_create_product(request: Request, order_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        result = _store_catalog().create_product(order_id, payload)
        sync = _live_sync_shop_catalog(order_id)
        if isinstance(result, dict):
            result["live_sync"] = sync
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/products/{product_id}")
def store_admin_get_product(request: Request, order_id: str, product_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        return _store_catalog().get_product(order_id, product_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


def _shop_product_dir_for_order(order_id: str):
    from app.factory.store_factory.service import StoreFactoryService

    order = _ctx().sales.get_order(order_id) or {}
    product_id = str(order.get("product_id") or "").strip()
    if not product_id:
        return None, order
    return StoreFactoryService(_memory_dir()).product_dir(product_id), order


def _live_sync_shop_catalog(order_id: str) -> dict:
    """Push catalog SSOT into published storefront HTML (honest Live Sync)."""
    from app.integration.store_admin.shop_live_sync import sync_catalog_to_storefront

    product_dir, _order = _shop_product_dir_for_order(order_id)
    if product_dir is None or not product_dir.is_dir():
        return {"ok": False, "live_sync": False, "reason": "product_dir_missing"}
    catalog = _store_catalog()
    products = catalog._load(order_id)  # noqa: SLF001
    media_root = catalog._media._media  # noqa: SLF001
    sync = sync_catalog_to_storefront(
        product_dir, products, media_root=media_root
    )
    # Persist storefront_path back into catalog SSOT when materialize ran
    updated = sync.get("catalog") if isinstance(sync, dict) else None
    if isinstance(updated, list):
        catalog._save(order_id, updated)  # noqa: SLF001
    return {k: v for k, v in sync.items() if k != "catalog"}


@app.patch("/api/client/stores/{order_id}/admin/products/{product_id}")
async def store_admin_update_product(
    request: Request, order_id: str, product_id: str
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        result = _store_catalog().update_product(order_id, product_id, payload)
        sync = _live_sync_shop_catalog(order_id)
        if isinstance(result, dict):
            result["live_sync"] = sync
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.delete("/api/client/stores/{order_id}/admin/products/{product_id}")
def store_admin_delete_product(
    request: Request, order_id: str, product_id: str
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        result = _store_catalog().delete_product(order_id, product_id)
        sync = _live_sync_shop_catalog(order_id)
        if isinstance(result, dict):
            result["live_sync"] = sync
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/products/bulk")
async def store_admin_bulk_products(request: Request, order_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        return _store_catalog().bulk(order_id, payload)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/products/ai-generate")
async def store_admin_ai_generate(request: Request, order_id: str) -> dict:
    try:
        store = _assert_store_admin_access(request, order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        brief = store.get("shop_brief") if isinstance(store.get("shop_brief"), dict) else {}
        return _store_catalog().ai_generate(
            order_id,
            payload,
            store_name=str(store.get("store_name") or brief.get("store_name") or ""),
            store_category=str(brief.get("category") or ""),
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/products/{product_id}/media")
async def store_admin_upload_media(
    request: Request,
    order_id: str,
    product_id: str,
    files: list[UploadFile] = File(...),
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        if not files:
            raise ValueError("files_required")
        result = _store_catalog().add_images(order_id, product_id, list(files))
        sync = _live_sync_shop_catalog(order_id)
        if isinstance(result, dict):
            result["live_sync"] = sync
            # Refresh product with storefront_path after materialize
            try:
                refreshed = _store_catalog().get_product(order_id, product_id)
                if isinstance(refreshed, dict) and refreshed.get("product"):
                    result["product"] = refreshed["product"]
            except ValueError:
                pass
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.patch("/api/client/stores/{order_id}/admin/products/{product_id}/media")
async def store_admin_update_media(
    request: Request, order_id: str, product_id: str
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        result = _store_catalog().update_images(order_id, product_id, payload)
        sync = _live_sync_shop_catalog(order_id)
        if isinstance(result, dict):
            result["live_sync"] = sync
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.delete(
    "/api/client/stores/{order_id}/admin/products/{product_id}/media/{image_id}"
)
def store_admin_delete_media(
    request: Request, order_id: str, product_id: str, image_id: str
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        result = _store_catalog().delete_image(order_id, product_id, image_id)
        sync = _live_sync_shop_catalog(order_id)
        if isinstance(result, dict):
            result["live_sync"] = sync
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/media/{image_id}")
def store_admin_serve_media(
    request: Request,
    order_id: str,
    image_id: str,
    access_token: str | None = None,
):
    """Serve catalog image. Auth via Bearer header or access_token query (for <img>)."""
    try:
        if access_token:
            from app.integration.customer_identity.auth import decode_client_token

            payload = decode_client_token(access_token)
            if not payload or not payload.get("sub"):
                raise HTTPException(status_code=401, detail="client_auth_required")
            customer_id = str(payload["sub"])
            email = str(payload.get("email") or "").strip() or None
            _ctx().sales.get_store_for_customer(
                order_id, customer_id=customer_id, email=email
            )
        else:
            _assert_store_admin_access(request, order_id)
        path = _store_catalog().resolve_media(order_id, image_id)
        media = {
            ".webp": "image/webp",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
        }.get(path.suffix.lower(), "application/octet-stream")
        return FileResponse(path, media_type=media)
    except HTTPException:
        raise
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


def _reapply_design_to_live(order_id: str, store: dict) -> None:
    """Push owner design into sandbox/published HTML after Design save."""
    product_id = str(store.get("product_id") or "").strip()
    if not product_id:
        return
    try:
        from app.factory.store_factory import StoreFactoryService
        from app.integration.store_admin.design_apply import apply_design_to_product_dir

        factory = StoreFactoryService(_memory_dir())
        apply_design_to_product_dir(
            _memory_dir(),
            order_id,
            factory.product_dir(product_id),
            store_name=str(store.get("store_name") or ""),
        )
        # Keep published copy in sync when already live
        if store.get("shop_pipeline") == "published" or store.get("published_url"):
            factory.publish(product_id, order_id=order_id)
    except Exception:
        pass


@app.get("/api/client/stores/{order_id}/admin/design")
def store_admin_get_design(request: Request, order_id: str) -> dict:
    try:
        store = _assert_store_admin_access(request, order_id)
        return _store_design().get_design(
            order_id, store_name=str(store.get("store_name") or "")
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.put("/api/client/stores/{order_id}/admin/design")
@app.patch("/api/client/stores/{order_id}/admin/design")
async def store_admin_update_design(request: Request, order_id: str) -> dict:
    try:
        store = _assert_store_admin_access(request, order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        result = _store_design().update_design(
            order_id,
            payload,
            store_name=str(store.get("store_name") or ""),
        )
        _reapply_design_to_live(order_id, store)
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/design/undo")
def store_admin_design_undo(request: Request, order_id: str) -> dict:
    try:
        store = _assert_store_admin_access(request, order_id)
        result = _store_design().undo(
            order_id, store_name=str(store.get("store_name") or "")
        )
        _reapply_design_to_live(order_id, store)
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/design/redo")
def store_admin_design_redo(request: Request, order_id: str) -> dict:
    try:
        store = _assert_store_admin_access(request, order_id)
        result = _store_design().redo(
            order_id, store_name=str(store.get("store_name") or "")
        )
        _reapply_design_to_live(order_id, store)
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/design/restore-defaults")
def store_admin_design_restore(request: Request, order_id: str) -> dict:
    try:
        store = _assert_store_admin_access(request, order_id)
        result = _store_design().restore_defaults(
            order_id, store_name=str(store.get("store_name") or "")
        )
        _reapply_design_to_live(order_id, store)
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/design/assets")
async def store_admin_design_upload_asset(
    request: Request,
    order_id: str,
    kind: str = "logo",
    file: UploadFile = File(...),
) -> dict:
    try:
        store = _assert_store_admin_access(request, order_id)
        result = _store_design().upload_asset(
            order_id,
            file,
            kind=kind,
            store_name=str(store.get("store_name") or ""),
        )
        _reapply_design_to_live(order_id, store)
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/design/media/{image_id}")
def store_admin_design_serve_media(
    request: Request,
    order_id: str,
    image_id: str,
    access_token: str | None = None,
):
    try:
        if access_token:
            from app.integration.customer_identity.auth import decode_client_token

            payload = decode_client_token(access_token)
            if not payload or not payload.get("sub"):
                raise HTTPException(status_code=401, detail="client_auth_required")
            customer_id = str(payload["sub"])
            email = str(payload.get("email") or "").strip() or None
            _ctx().sales.get_store_for_customer(
                order_id, customer_id=customer_id, email=email
            )
        else:
            _assert_store_admin_access(request, order_id)
        path = _store_design().resolve_media(order_id, image_id)
        media = {
            ".webp": "image/webp",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".ico": "image/x-icon",
        }.get(path.suffix.lower(), "application/octet-stream")
        return FileResponse(path, media_type=media)
    except HTTPException:
        raise
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


def _store_customers():
    from app.integration.store_customer import StoreCustomerService

    return StoreCustomerService(_memory_dir())


def _assert_shop_order_public(order_id: str) -> dict:
    order = _ctx().sales.get_order(order_id)
    if not order:
        raise ValueError("order_not_found")
    if str(order.get("package_id") or "").strip().lower() != "ecommerce_shop":
        raise ValueError("not_a_shop_order")
    return order


def _store_buyer_http_error(exc: ValueError) -> HTTPException:
    msg = str(exc)
    if msg in ("buyer_not_found", "order_not_found"):
        return HTTPException(status_code=404, detail=msg)
    if msg == "wrong_store":
        return HTTPException(status_code=403, detail=msg)
    return HTTPException(status_code=400, detail=msg)


@app.post("/api/store/{order_id}/account/register")
async def store_buyer_register(request: Request, order_id: str) -> dict:
    try:
        _assert_shop_order_public(order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        return _store_customers().register(order_id, payload)
    except ValueError as exc:
        raise _store_buyer_http_error(exc) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/store/{order_id}/account/login")
async def store_buyer_login(request: Request, order_id: str) -> dict:
    try:
        _assert_shop_order_public(order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        return _store_customers().login(order_id, payload)
    except ValueError as exc:
        raise _store_buyer_http_error(exc) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/store/{order_id}/account/forgot-password")
async def store_buyer_forgot(request: Request, order_id: str) -> dict:
    try:
        _assert_shop_order_public(order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        return _store_customers().request_password_reset(order_id, payload)
    except ValueError as exc:
        raise _store_buyer_http_error(exc) from exc


@app.post("/api/store/{order_id}/account/reset-password")
async def store_buyer_reset(request: Request, order_id: str) -> dict:
    try:
        _assert_shop_order_public(order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        return _store_customers().reset_password(order_id, payload)
    except ValueError as exc:
        raise _store_buyer_http_error(exc) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/store/{order_id}/account/me")
def store_buyer_me(request: Request, order_id: str) -> dict:
    from app.integration.store_customer.auth import require_store_buyer

    buyer = require_store_buyer(request, order_id)
    try:
        return _store_customers().me(order_id, str(buyer["sub"]))
    except ValueError as exc:
        raise _store_buyer_http_error(exc) from exc


@app.patch("/api/store/{order_id}/account/me")
async def store_buyer_update_me(request: Request, order_id: str) -> dict:
    from app.integration.store_customer.auth import require_store_buyer

    buyer = require_store_buyer(request, order_id)
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        return _store_customers().update_profile(
            order_id, str(buyer["sub"]), payload
        )
    except ValueError as exc:
        raise _store_buyer_http_error(exc) from exc


@app.get("/api/store/{order_id}/account/addresses")
def store_buyer_list_addresses(request: Request, order_id: str) -> dict:
    from app.integration.store_customer.auth import require_store_buyer

    buyer = require_store_buyer(request, order_id)
    try:
        return _store_customers().list_addresses(order_id, str(buyer["sub"]))
    except ValueError as exc:
        raise _store_buyer_http_error(exc) from exc


@app.post("/api/store/{order_id}/account/addresses")
async def store_buyer_save_address(request: Request, order_id: str) -> dict:
    from app.integration.store_customer.auth import require_store_buyer

    buyer = require_store_buyer(request, order_id)
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        return _store_customers().save_address(
            order_id, str(buyer["sub"]), payload
        )
    except ValueError as exc:
        raise _store_buyer_http_error(exc) from exc


@app.delete("/api/store/{order_id}/account/addresses/{address_id}")
def store_buyer_delete_address(
    request: Request, order_id: str, address_id: str
) -> dict:
    from app.integration.store_customer.auth import require_store_buyer

    buyer = require_store_buyer(request, order_id)
    try:
        return _store_customers().delete_address(
            order_id, str(buyer["sub"]), address_id
        )
    except ValueError as exc:
        raise _store_buyer_http_error(exc) from exc


@app.get("/api/store/{order_id}/account/wishlist")
def store_buyer_get_wishlist(request: Request, order_id: str) -> dict:
    from app.integration.store_customer.auth import require_store_buyer

    buyer = require_store_buyer(request, order_id)
    try:
        return _store_customers().get_wishlist(order_id, str(buyer["sub"]))
    except ValueError as exc:
        raise _store_buyer_http_error(exc) from exc


@app.put("/api/store/{order_id}/account/wishlist")
async def store_buyer_set_wishlist(request: Request, order_id: str) -> dict:
    from app.integration.store_customer.auth import require_store_buyer

    buyer = require_store_buyer(request, order_id)
    try:
        payload = await request.json()
        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            raise ValueError("items_required")
        return _store_customers().set_wishlist(
            order_id, str(buyer["sub"]), items
        )
    except ValueError as exc:
        raise _store_buyer_http_error(exc) from exc


@app.get("/api/store/{order_id}/account/orders")
def store_buyer_orders(request: Request, order_id: str) -> dict:
    from app.integration.store_customer.auth import require_store_buyer

    buyer = require_store_buyer(request, order_id)
    try:
        return _store_customers().get_orders(order_id, str(buyer["sub"]))
    except ValueError as exc:
        raise _store_buyer_http_error(exc) from exc


@app.get("/api/store/{order_id}/checkout/options")
def store_checkout_options(order_id: str) -> dict:
    """Checkout 1.0 — shipping + payment methods from merchant commerce settings."""
    from app.integration.store_checkout import StoreCheckoutService

    return StoreCheckoutService(_memory_dir()).checkout_options(order_id)


@app.post("/api/store/{order_id}/checkout/place")
def store_checkout_place(
    request: Request, order_id: str, body: dict | None = None
) -> dict:
    """Checkout 1.0 — place order (no live PSP charge)."""
    from app.integration.store_customer.auth import require_store_buyer
    from app.integration.store_checkout import StoreCheckoutService

    buyer = require_store_buyer(request, order_id)
    try:
        return StoreCheckoutService(_memory_dir()).place_order(
            order_id, str(buyer["sub"]), body or {}
        )
    except ValueError as exc:
        msg = str(exc)
        if msg in {
            "cart_empty",
            "shipping_required",
            "payment_required",
            "address_incomplete",
            "below_min_order",
            "buyer_not_found",
        }:
            raise HTTPException(status_code=400, detail=msg) from exc
        raise _store_buyer_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/orders")
def store_admin_orders(request: Request, order_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_checkout import StoreCheckoutService

        return StoreCheckoutService(_memory_dir()).list_shop_orders(order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/customers")
def store_admin_list_customers(request: Request, order_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        return _store_customers().admin_list_customers(order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/commerce")
def store_admin_commerce_settings(request: Request, order_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        return StoreCommerceSettingsService(_memory_dir()).ensure_saved(order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/integrations")
def store_admin_integrations(request: Request, order_id: str) -> dict:
    """Integrations hub — Payments, Shipping, Email, … unified cards."""
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        return StoreCommerceSettingsService(_memory_dir()).integrations_hub(order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/integrations/{provider_id}/connect")
def store_admin_integration_connect(
    request: Request, order_id: str, provider_id: str, body: dict | None = None
) -> dict:
    """R3.3.1+ — merchant connects their own provider account."""
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        account = str((body or {}).get("account") or "").strip() or None
        return StoreCommerceSettingsService(_memory_dir()).connect(
            order_id, provider_id, account=account
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "oauth_required":
            raise HTTPException(
                status_code=400,
                detail="Use Stripe Connect OAuth — GET .../integrations/stripe/oauth/start",
            ) from exc
        if msg == "smtp_form_required":
            raise HTTPException(
                status_code=400,
                detail="Use POST .../integrations/{gmail|outlook|microsoft365|smtp}/smtp-connect",
            ) from exc
        if msg == "shipping_api_required":
            raise HTTPException(
                status_code=400,
                detail="Use POST .../integrations/{dhl|dpd|gls|hermes|ups|fedex}/shipping-connect",
            ) from exc
        if msg == "account_required":
            raise HTTPException(status_code=400, detail=msg) from exc
        if msg == "provider_not_connectable":
            raise HTTPException(status_code=400, detail=msg) from exc
        if msg == "provider_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/integrations/{provider_id}/smtp-connect")
def store_admin_smtp_connect(
    request: Request, order_id: str, provider_id: str, body: dict | None = None
) -> dict:
    """Gen1 SMTP — Gmail / Outlook / M365 / custom SMTP credentials."""
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        return StoreCommerceSettingsService(_memory_dir()).connect_email_smtp(
            order_id, provider_id, body or {}
        )
    except ValueError as exc:
        msg = str(exc)
        if msg in {
            "provider_not_found",
            "smtp_host_required",
            "smtp_port_invalid",
            "smtp_username_required",
            "smtp_password_required",
            "smtp_from_invalid",
            "smtp_encryption_invalid",
        }:
            raise HTTPException(
                status_code=404 if msg == "provider_not_found" else 400, detail=msg
            ) from exc
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/integrations/{provider_id}/shipping-connect")
def store_admin_shipping_connect(
    request: Request, order_id: str, provider_id: str, body: dict | None = None
) -> dict:
    """Gen1 Shipping API — DHL / DPD / GLS / Hermes / UPS / FedEx credentials + test."""
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreShippingApiService

        return StoreShippingApiService(_memory_dir()).connect_carrier(
            order_id, provider_id, body or {}
        )
    except ValueError as exc:
        msg = str(exc)
        if msg in {
            "carrier_not_supported",
            "provider_not_found",
            "api_credentials_required",
            "connection_failed",
            "API Authentication failed",
        } or msg.startswith("Missing"):
            raise HTTPException(
                status_code=404 if msg == "provider_not_found" else 400, detail=msg
            ) from exc
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/shipping/{carrier}/test")
def store_admin_shipping_test(
    request: Request, order_id: str, carrier: str, body: dict | None = None
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreShippingApiService

        return StoreShippingApiService(_memory_dir()).test_connection(
            order_id, carrier, body or {}
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/shipping/quotes")
def store_admin_shipping_quotes(
    request: Request,
    order_id: str,
    carrier: str | None = None,
    weight_kg: float = 1.0,
    country: str = "DE",
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreShippingApiService

        return StoreShippingApiService(_memory_dir()).quote_rates(
            order_id, carrier=carrier, weight_kg=weight_kg, country=country
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/shipping/shipments")
def store_admin_shipping_list(request: Request, order_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreShippingApiService

        return StoreShippingApiService(_memory_dir()).list_shipments(order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/shipping/shipments")
def store_admin_shipping_create(
    request: Request, order_id: str, body: dict | None = None
) -> dict:
    """Create shipment for a shop order → tracking number."""
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreShippingApiService

        shop_order_id = str((body or {}).get("shop_order_id") or "").strip()
        if not shop_order_id:
            raise HTTPException(status_code=400, detail="shop_order_id_required")
        return StoreShippingApiService(_memory_dir()).create_shipment(
            order_id,
            shop_order_id=shop_order_id,
            carrier=str((body or {}).get("carrier") or "").strip() or None,
            service_id=str((body or {}).get("service_id") or "").strip() or None,
        )
    except ValueError as exc:
        msg = str(exc)
        if msg in {
            "order_not_found",
            "carrier_not_connected",
            "offline_carrier_no_shipment",
        }:
            raise HTTPException(
                status_code=404 if msg == "order_not_found" else 400, detail=msg
            ) from exc
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/shipping/track")
def store_admin_shipping_track(
    request: Request, order_id: str, body: dict | None = None
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreShippingApiService

        return StoreShippingApiService(_memory_dir()).track_shipment(
            order_id,
            tracking_number=str((body or {}).get("tracking_number") or "").strip()
            or None,
            shipment_id=str((body or {}).get("shipment_id") or "").strip() or None,
            advance=bool((body or {}).get("advance")),
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "shipment_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/email/test")
def store_admin_email_test(request: Request, order_id: str, body: dict | None = None) -> dict:
    """Send Test Email via merchant SMTP — required UX after Connect."""
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        to = str((body or {}).get("to") or "").strip() or None
        return StoreCommerceSettingsService(_memory_dir()).send_test_email(
            order_id, to=to
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "smtp_not_connected":
            raise HTTPException(status_code=400, detail=msg) from exc
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/business-profile")
def store_admin_business_profile_get(request: Request, order_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import BusinessProfileService

        return BusinessProfileService(_memory_dir()).get(order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.patch("/api/client/stores/{order_id}/admin/business-profile")
def store_admin_business_profile_patch(
    request: Request, order_id: str, body: dict | None = None
) -> dict:
    """Contact & Communication — single source of truth for the whole Virtus surface."""
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import BusinessProfileService

        return BusinessProfileService(_memory_dir()).update(order_id, body or {})
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/email-templates")
def store_admin_email_templates(request: Request, order_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import EmailTemplatesService

        return EmailTemplatesService(_memory_dir()).get(order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/integrations/stripe/oauth/start")
def store_admin_stripe_oauth_start(request: Request, order_id: str):
    """Stripe Connect OAuth — break out of iframe and send merchant to Stripe."""
    import html as html_lib
    import json as json_lib

    from app.integration import stripe_connect_oauth as stripe_oauth
    from app.integration.store_admin import StoreCommerceSettingsService

    try:
        _assert_store_admin_access(request, order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc

    if not stripe_oauth.oauth_client_ready():
        raise HTTPException(
            status_code=400,
            detail=(
                "Set STRIPE_CONNECT_CLIENT_ID (ca_…) and STRIPE_SECRET_KEY, "
                "or GENESIS_STRIPE_CONNECT_MOCK=1 for QA."
            ),
        )

    base = str(request.base_url).rstrip("/")
    redirect_uri = stripe_oauth.default_redirect_uri(base)
    frontend_base = (
        os.getenv("GENESIS_FRONTEND_URL", "").strip()
        or os.getenv("NEXT_PUBLIC_SITE_URL", "").strip()
        or ""
    )
    return_url = stripe_oauth.frontend_return_url(
        order_id, public_frontend_base=frontend_base
    )
    state = stripe_oauth.create_oauth_state(order_id=order_id, return_url=return_url)

    # Mock path: complete Connect without leaving Virtus (QA / demos).
    if stripe_oauth.mock_enabled():
        exchanged = stripe_oauth.exchange_code(code=f"mock-{order_id}", redirect_uri=redirect_uri)
        info = stripe_oauth.retrieve_account(str(exchanged.get("stripe_user_id") or ""))
        label = stripe_oauth.account_label_from_oauth(exchanged, account_info=info)
        StoreCommerceSettingsService(_memory_dir()).apply_stripe_oauth(
            order_id,
            stripe_user_id=str(exchanged["stripe_user_id"]),
            account_label=label,
            livemode=False,
            scope=str(exchanged.get("scope") or "read_write"),
            stripe_publishable_key=exchanged.get("stripe_publishable_key"),
            mock=True,
        )
        accept = (request.headers.get("accept") or "").lower()
        if "application/json" in accept and "text/html" not in accept:
            return {"ok": True, "mock": True, "redirect": return_url, "account": label}
        safe = html_lib.escape(return_url, quote=True)
        js_url = json_lib.dumps(return_url)
        return HTMLResponse(
            f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"/>
<meta http-equiv="refresh" content="0;url={safe}"/>
<title>Stripe Connected</title></head>
<body style="font-family:system-ui;padding:2rem;background:#111;color:#eee">
<p>Stripe Connected (mock). Returning to Store Admin…</p>
<p><a href="{safe}" target="_top" style="color:#8cf">Continue</a></p>
<script>
try {{ window.top.location.href = {js_url}; }}
catch (e) {{ window.location.href = {js_url}; }}
</script>
</body></html>"""
        )

    url = stripe_oauth.authorization_url(redirect_uri=redirect_uri, state=state)
    accept = (request.headers.get("accept") or "").lower()
    if "application/json" in accept and "text/html" not in accept:
        return {"ok": True, "url": url, "redirect_uri": redirect_uri}
    safe = html_lib.escape(url, quote=True)
    js_url = json_lib.dumps(url)
    return HTMLResponse(
        f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"/>
<meta http-equiv="refresh" content="0;url={safe}"/>
<title>Connect Stripe…</title></head>
<body style="font-family:system-ui;padding:2rem;background:#111;color:#eee">
<p>Redirecting to Stripe… If this screen stays blank, open the link:</p>
<p><a href="{safe}" target="_top" style="color:#8cf">Continue to Stripe</a></p>
<script>
try {{ window.top.location.href = {js_url}; }}
catch (e) {{ window.location.href = {js_url}; }}
</script>
</body></html>"""
    )


@app.get("/api/client/stores/stripe/oauth/callback", response_class=HTMLResponse)
def store_admin_stripe_oauth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> str:
    """Stripe Connect OAuth callback — save acct_… and return merchant to Store Admin."""
    import html as html_lib
    import json as json_lib

    from app.integration import stripe_connect_oauth as stripe_oauth
    from app.integration.store_admin import StoreCommerceSettingsService

    def _fail(msg: str) -> str:
        safe = html_lib.escape(msg)
        return (
            "<!DOCTYPE html><html><body style='font-family:system-ui;padding:2rem'>"
            f"<h1>Stripe Connect error</h1><pre>{safe}</pre>"
            "<p>Close this tab and try Connect again from Store Admin → Payments.</p>"
            "</body></html>"
        )

    if error:
        return _fail(error_description or error)
    payload = stripe_oauth.consume_oauth_state(state or "")
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    order_id = str(payload.get("order_id") or "").strip()
    return_url = str(payload.get("return_url") or "").strip() or stripe_oauth.frontend_return_url(
        order_id
    )
    if not code:
        return _fail("Missing authorization code")
    base = str(request.base_url).rstrip("/")
    redirect_uri = stripe_oauth.default_redirect_uri(base)
    exchanged = stripe_oauth.exchange_code(code=code, redirect_uri=redirect_uri)
    if not exchanged.get("ok"):
        return _fail(str(exchanged.get("detail") or exchanged.get("reason") or "token_exchange_failed"))
    info = stripe_oauth.retrieve_account(str(exchanged.get("stripe_user_id") or ""))
    label = stripe_oauth.account_label_from_oauth(exchanged, account_info=info if info.get("ok") else None)
    try:
        StoreCommerceSettingsService(_memory_dir()).apply_stripe_oauth(
            order_id,
            stripe_user_id=str(exchanged["stripe_user_id"]),
            account_label=label,
            livemode=bool(exchanged.get("livemode")),
            scope=str(exchanged.get("scope") or "read_write"),
            stripe_publishable_key=exchanged.get("stripe_publishable_key"),
            mock=bool(exchanged.get("mock")),
        )
    except ValueError as exc:
        return _fail(str(exc))

    # Prefer top-level redirect back into the client app.
    safe = html_lib.escape(return_url, quote=True)
    js_url = json_lib.dumps(return_url)
    return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"/>
<meta http-equiv="refresh" content="0;url={safe}"/>
<title>Stripe Connected</title></head>
<body style="font-family:system-ui;padding:2rem;background:#111;color:#eee">
<p>Stripe Connected. Returning to Virtus Core…</p>
<p><a href="{safe}" target="_top" style="color:#8cf">Continue to Store Admin</a></p>
<script>
try {{ window.top.location.href = {js_url}; }}
catch (e) {{ window.location.href = {js_url}; }}
</script>
</body></html>"""


@app.post("/api/client/stores/{order_id}/admin/integrations/{provider_id}/disconnect")
def store_admin_integration_disconnect(
    request: Request, order_id: str, provider_id: str
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        return StoreCommerceSettingsService(_memory_dir()).disconnect(
            order_id, provider_id
        )
    except ValueError as exc:
        msg = str(exc)
        if msg in {"provider_not_connectable", "provider_not_found"}:
            raise HTTPException(
                status_code=404 if "not_found" in msg else 400, detail=msg
            ) from exc
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/integrations/{provider_id}/reconnect")
def store_admin_integration_reconnect(
    request: Request, order_id: str, provider_id: str, body: dict | None = None
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        account = str((body or {}).get("account") or "").strip() or None
        return StoreCommerceSettingsService(_memory_dir()).reconnect(
            order_id, provider_id, account=account
        )
    except ValueError as exc:
        msg = str(exc)
        if msg in {
            "account_required",
            "oauth_required",
            "smtp_form_required",
            "shipping_api_required",
            "provider_not_connectable",
            "provider_not_found",
        }:
            raise HTTPException(
                status_code=404 if "not_found" in msg else 400, detail=msg
            ) from exc
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/integrations/{provider_id}/sync")
def store_admin_integration_sync(
    request: Request, order_id: str, provider_id: str
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        return StoreCommerceSettingsService(_memory_dir()).sync(order_id, provider_id)
    except ValueError as exc:
        msg = str(exc)
        if msg in {"provider_not_connected", "provider_not_found"}:
            raise HTTPException(
                status_code=404 if "not_found" in msg else 400, detail=msg
            ) from exc
        raise _client_store_http_error(exc) from exc


@app.patch("/api/client/stores/{order_id}/admin/shipping-config")
def store_admin_shipping_config(
    request: Request, order_id: str, body: dict | None = None
) -> dict:
    """R3.3.2 — general shipping settings, rates, methods."""
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        return StoreCommerceSettingsService(_memory_dir()).update_shipping_config(
            order_id, body or {}
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "invalid_rate_mode":
            raise HTTPException(status_code=400, detail=msg) from exc
        raise _client_store_http_error(exc) from exc


@app.patch("/api/client/stores/{order_id}/admin/tax-config")
def store_admin_tax_config(
    request: Request, order_id: str, body: dict | None = None
) -> dict:
    """R3.3.3 — MwSt / VAT profiles for DE & EU."""
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        return StoreCommerceSettingsService(_memory_dir()).update_tax_config(
            order_id, body or {}
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "invalid_tax_profile":
            raise HTTPException(status_code=400, detail=msg) from exc
        raise _client_store_http_error(exc) from exc


@app.patch("/api/client/stores/{order_id}/admin/invoice-config")
def store_admin_invoice_config(
    request: Request, order_id: str, body: dict | None = None
) -> dict:
    """R3.3.5 — invoice / credit note numbering."""
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        return StoreCommerceSettingsService(_memory_dir()).update_invoice_config(
            order_id, body or {}
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/invoices/allocate")
def store_admin_invoice_allocate(request: Request, order_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        return StoreCommerceSettingsService(_memory_dir()).allocate_invoice_number(
            order_id
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/credit-notes/allocate")
def store_admin_credit_allocate(request: Request, order_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreCommerceSettingsService

        return StoreCommerceSettingsService(_memory_dir()).allocate_credit_note(order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/documents")
def store_admin_documents_list(request: Request, order_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreInvoiceService

        return StoreInvoiceService(_memory_dir()).list_documents(order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/documents/invoice")
def store_admin_create_invoice(
    request: Request, order_id: str, body: dict | None = None
) -> dict:
    """Generate professional Invoice PDF from a shop order + Business Profile."""
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreInvoiceService

        shop_order_id = str((body or {}).get("shop_order_id") or "").strip()
        if not shop_order_id:
            raise HTTPException(status_code=400, detail="shop_order_id_required")
        language = str((body or {}).get("language") or "").strip() or None
        return StoreInvoiceService(_memory_dir()).create_invoice(
            order_id, shop_order_id=shop_order_id, language=language
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "order_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/documents/credit-note")
def store_admin_create_credit_note(
    request: Request, order_id: str, body: dict | None = None
) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreInvoiceService

        invoice_doc_id = str((body or {}).get("invoice_doc_id") or "").strip()
        if not invoice_doc_id:
            raise HTTPException(status_code=400, detail="invoice_doc_id_required")
        reason = str((body or {}).get("reason") or "").strip()
        refund_type = str((body or {}).get("refund_type") or "full").strip()
        amount = (body or {}).get("amount_eur")
        amount_eur = float(amount) if amount is not None else None
        language = str((body or {}).get("language") or "").strip() or None
        return StoreInvoiceService(_memory_dir()).create_credit_note(
            order_id,
            invoice_doc_id=invoice_doc_id,
            reason=reason,
            refund_type=refund_type,
            amount_eur=amount_eur,
            language=language,
        )
    except ValueError as exc:
        msg = str(exc)
        if msg in {"document_not_found", "invoice_required"}:
            raise HTTPException(
                status_code=404 if "not_found" in msg else 400, detail=msg
            ) from exc
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/documents/{doc_id}/pdf")
def store_admin_document_pdf(request: Request, order_id: str, doc_id: str):
    try:
        _assert_store_admin_access(request, order_id)
        from fastapi.responses import Response

        from app.integration.store_admin import StoreInvoiceService

        data, number = StoreInvoiceService(_memory_dir()).read_pdf_bytes(order_id, doc_id)
        filename = f"{number}.pdf".replace('"', "")
        return Response(
            content=data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "document_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/documents/{doc_id}/email")
def store_admin_document_email(
    request: Request, order_id: str, doc_id: str, body: dict | None = None
) -> dict:
    """Send / resend invoice PDF notice via merchant SMTP."""
    try:
        _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreInvoiceService

        to = str((body or {}).get("to") or "").strip() or None
        resend = bool((body or {}).get("resend"))
        return StoreInvoiceService(_memory_dir()).send_document_email(
            order_id, doc_id, to=to, resend=resend
        )
    except ValueError as exc:
        msg = str(exc)
        if msg in {"document_not_found", "smtp_not_connected", "recipient_required"}:
            raise HTTPException(
                status_code=404 if "not_found" in msg else 400, detail=msg
            ) from exc
        raise _client_store_http_error(exc) from exc


@app.get("/api/owner/global-analytics")
def owner_global_analytics() -> dict:
    """Mission Control — company-wide Global Analytics + Integrations Analytics."""
    from app.integration.platform_global_analytics import PlatformGlobalAnalyticsService

    finance_snap: dict = {}
    company_snap: dict = {}
    try:
        fin_svc = getattr(_ctx(), "finance", None)
        if fin_svc is not None:
            if hasattr(fin_svc, "revenue_summary"):
                finance_snap = dict(fin_svc.revenue_summary() or {})
            hist = getattr(fin_svc, "_load_snapshot", None)
            if callable(hist):
                snap = hist() or {}
                if isinstance(snap, dict):
                    finance_snap = {**snap, **finance_snap}
    except Exception:
        pass
    try:
        company_snap = _ctx().mission_control._company_history()  # noqa: SLF001
    except Exception:
        pass
    return PlatformGlobalAnalyticsService(_memory_dir()).global_snapshot(
        finance=finance_snap if isinstance(finance_snap, dict) else {},
        factory={},
        company=company_snap if isinstance(company_snap, dict) else {},
    )


@app.get("/api/owner/ceo-dashboard")
def owner_ceo_executive_dashboard(stage: str = "core") -> dict:
    """Mission Control — morning Executive Dashboard (Virtus + Farm + Today Focus).

    stage=core (default): Today Focus + Health + Virtus — fast first paint.
    stage=full: includes Farm panel + heavy company audits.
    """
    from app.integration.ceo_executive_dashboard import build_ceo_executive_dashboard

    finance_snap: dict = {}
    try:
        fin_svc = getattr(_ctx(), "finance", None)
        if fin_svc is not None:
            if hasattr(fin_svc, "revenue_summary"):
                finance_snap = dict(fin_svc.revenue_summary() or {})
            hist = getattr(fin_svc, "_load_snapshot", None)
            if callable(hist):
                snap = hist() or {}
                if isinstance(snap, dict):
                    finance_snap = {**snap, **finance_snap}
    except Exception:
        pass
    return build_ceo_executive_dashboard(
        _memory_dir(),
        finance=finance_snap if isinstance(finance_snap, dict) else {},
        include_deployment=False,
        stage=stage or "core",
    )


@app.get("/api/owner/ceo-dashboard/farm")
def owner_ceo_dashboard_farm() -> dict:
    """Lazy Farm KPIs — never block CEO first paint."""
    from app.integration.ceo_executive_dashboard import build_ceo_farm_section

    return build_ceo_farm_section(_memory_dir())


@app.get("/api/owner/deployment-manager")
def owner_deployment_manager() -> dict:
    """Live OVH/SSH deployment probe — lazy, never on CEO Dashboard critical path."""
    from app.integration.deployment_manager import build_deployment_manager

    return {"ok": True, **build_deployment_manager()}


@app.get("/api/owner/ai-providers")
def owner_ai_providers_gateway() -> dict:
    """CEO — Provider Gateway status (Creative Production Pipeline foundation)."""
    from app.integration.provider_gateway import ProviderGateway, pipeline_stages

    gw = ProviderGateway(_memory_dir())
    board = gw.status_board()
    board["pipeline"] = pipeline_stages()
    return board


@app.post("/api/owner/ai-providers/{provider_id}/connect")
async def owner_ai_provider_connect(provider_id: str, request: Request) -> dict:
    """Store API key via Gateway vault (not hand-edited .env as primary path)."""
    from app.integration.provider_gateway import ProviderGateway

    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    key = str(body.get("api_key") or body.get("key") or "").strip()
    gw = ProviderGateway(_memory_dir())
    return gw.connect(provider_id, key)


@app.post("/api/owner/ai-providers/{provider_id}/test")
def owner_ai_provider_test(provider_id: str) -> dict:
    from app.integration.provider_gateway import ProviderGateway

    return ProviderGateway(_memory_dir()).test_connection(provider_id)


def _support_center():
    from app.integration.customer_identity.support_center import SupportCenterService

    return SupportCenterService(_memory_dir())


@app.get("/api/public/service-marketplace")
def public_service_marketplace() -> dict:
    """Gen2 Stage 0 — Service Marketplace vitrine (catalog only)."""
    from app.integration.service_marketplace_stage0 import build_service_marketplace_catalog

    return build_service_marketplace_catalog()


@app.get("/api/owner/clients/lookup")
def owner_clients_lookup(q: str = "", limit: int = 20) -> dict:
    """Support Center — find clients by Business ID, email, name, phone, company."""
    svc = _support_center()
    svc.backfill_missing_ids(limit=200)
    hits = svc.lookup(q, limit=min(max(limit, 1), 50))
    return {"ok": True, "query": q, "results": hits, "count": len(hits)}


@app.get("/api/owner/clients/{customer_id}")
def owner_client_card(customer_id: str) -> dict:
    """Support Center — full Client Card."""
    card = _support_center().build_client_card(customer_id)
    if not card:
        raise HTTPException(status_code=404, detail="client_not_found")
    return card


@app.post("/api/owner/clients/{customer_id}/notes")
def owner_client_add_note(customer_id: str, body: dict) -> dict:
    text = str((body or {}).get("text") or "")
    author = str((body or {}).get("author") or "owner")
    note = _support_center().add_note(customer_id, text, author=author)
    if not note:
        raise HTTPException(status_code=400, detail="note_failed")
    return {"ok": True, "note": note}


@app.post("/api/owner/clients/{customer_id}/tickets")
def owner_client_create_ticket(customer_id: str, body: dict) -> dict:
    subject = str((body or {}).get("subject") or "Support")
    text = str((body or {}).get("body") or "")
    ticket = _support_center().create_ticket(customer_id, subject=subject, body=text)
    if not ticket:
        raise HTTPException(status_code=404, detail="client_not_found")
    return {"ok": True, "ticket": ticket}


@app.get("/api/owner/integrations-analytics")
def owner_integrations_analytics() -> dict:
    from app.integration.platform_global_analytics import PlatformGlobalAnalyticsService

    return PlatformGlobalAnalyticsService(_memory_dir()).integrations()


@app.get("/api/client/stores/{order_id}/admin/setup-status")
def store_admin_setup_status(request: Request, order_id: str) -> dict:
    """Vector Phase 1 — contextual store setup checklist + readiness %."""
    try:
        store = _assert_store_admin_access(request, order_id)
        from app.integration.store_admin import StoreSetupStatusService

        customer_count = 0
        try:
            listed = _store_customers().admin_list_customers(order_id)
            customer_count = int(listed.get("count") or len(listed.get("customers") or []))
        except Exception:
            customer_count = 0

        return StoreSetupStatusService(_memory_dir()).get(
            order_id,
            store_name=str(store.get("store_name") or ""),
            shop_pipeline=store.get("shop_pipeline"),
            customer_count=customer_count,
            order_count=0,
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/stores/{order_id}/admin/vector/dialog")
def store_admin_vector_dialog(
    request: Request,
    order_id: str,
    learning_mode: str | None = None,
    step_id: str | None = None,
) -> dict:
    """Vector Phase 2 — docked dialog wizard for Store Admin."""
    try:
        store = _assert_store_admin_access(request, order_id)
        from app.integration.vector import VectorContextService

        mode = (learning_mode or "").strip().lower() or None
        if mode not in (None, "skip", "show"):
            mode = None
        return VectorContextService(_memory_dir(), sales=_ctx().sales).store_dialog(
            order_id,
            store_name=str(store.get("store_name") or ""),
            shop_pipeline=store.get("shop_pipeline"),
            learning_mode=mode,
            step_id=(step_id or "").strip() or None,
            include_welcome=mode == "show" and not step_id,
        )
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/vector/dialog")
def client_vector_dialog(
    request: Request,
    surface: str = "platform",
    learning_mode: str | None = None,
    order_id: str | None = None,
) -> dict:
    """One Vector — platform / website_admin / customer surfaces."""
    customer_id, email = _client_store_identity(request)
    from app.integration.vector import VectorContextService

    mode = (learning_mode or "").strip().lower() or "skip"
    if mode not in ("skip", "show"):
        mode = "skip"
    return VectorContextService(_memory_dir(), sales=_ctx().sales).dialog_for_surface(
        surface,
        order_id=(order_id or "").strip() or None,
        customer_id=customer_id,
        email=email,
        learning_mode=mode,
    )


@app.get("/api/client/vector/business-setup")
def client_vector_business_setup(request: Request) -> dict:
    """Business Ready % across Website, Store, commerce stubs."""
    customer_id, email = _client_store_identity(request)
    from app.integration.vector import VectorContextService

    return VectorContextService(
        _memory_dir(), sales=_ctx().sales
    ).business_setup_for_customer(customer_id=customer_id, email=email)


@app.get("/api/client/vector/ai-health")
def client_vector_ai_health(request: Request) -> dict:
    customer_id, email = _client_store_identity(request)
    from app.integration.vector import VectorContextService

    return VectorContextService(
        _memory_dir(), sales=_ctx().sales
    ).ai_health_for_customer(customer_id=customer_id, email=email)


@app.get("/api/client/vector/business-bundle")
def client_vector_business_bundle(request: Request) -> dict:
    """Business Ready + AI Health in one payload."""
    customer_id, email = _client_store_identity(request)
    from app.integration.vector import VectorContextService

    return VectorContextService(
        _memory_dir(), sales=_ctx().sales
    ).business_bundle(customer_id=customer_id, email=email)


@app.post("/api/client/vector/progress")
def client_vector_progress(request: Request, body: dict) -> dict:
    """Persist Vector learning mode + wizard step (survives restart)."""
    customer_id, email = _client_store_identity(request)
    from app.integration.vector import VectorContextService

    scope = str((body or {}).get("scope") or "platform").strip()[:40]
    subject = str((body or {}).get("subject_id") or customer_id or "").strip()
    if not subject:
        raise HTTPException(status_code=400, detail="subject_id_required")
    svc = VectorContextService(_memory_dir(), sales=_ctx().sales)
    return {
        "ok": True,
        "progress": svc.save_progress(
            scope,
            subject,
            learning_mode=(body or {}).get("learning_mode"),
            step_id=(body or {}).get("step_id"),
            mark_completed=(body or {}).get("mark_completed"),
        ),
    }


@app.get("/api/client/workspace/nav")
def client_workspace_nav(request: Request, commerce_mode: str | None = None) -> dict:
    """Standalone vs Connected nav allowlist for Virtus AI Workspace."""
    customer_id, email = _client_store_identity(request)
    from app.factory.commerce_gates import workspace_nav_spec
    from app.integration.vector import VectorContextService

    products: list = []
    try:
        bundle = VectorContextService(
            _memory_dir(), sales=_ctx().sales
        ).business_setup_for_customer(customer_id=customer_id, email=email)
        # Infer products from setup flags
        if bundle.get("items"):
            for it in bundle["items"]:
                if it.get("id") == "website" and it.get("done"):
                    products.append({"product_type": "website"})
                if it.get("id") == "store" and it.get("done"):
                    products.append({"product_type": "store"})
    except Exception:
        products = [{"product_type": "website"}]
    mode = (commerce_mode or "").strip() or None
    return {
        "ok": True,
        **workspace_nav_spec(commerce_mode=mode, products=products),
        "customer_id": customer_id,
    }


@app.post("/api/client/virtus-ai/turn")
def client_virtus_ai_turn(request: Request, body: dict) -> dict:
    """Virtus AI orchestrator turn — ownership + plan + internal model_hint."""
    customer_id, email = _client_store_identity(request)
    from app.integration.virtus_ai import handle_turn

    msg = str((body or {}).get("message") or "").strip()
    mode = str((body or {}).get("mode") or "auto").strip().lower()
    commerce = str((body or {}).get("commerce_mode") or "").strip() or None
    ctx = dict((body or {}).get("context") or {})
    if email and not ctx.get("client_name"):
        ctx["client_name"] = str(email).split("@")[0]
    products = (body or {}).get("products") or [{"product_type": "website"}]
    out = handle_turn(
        msg or "__welcome__",
        client_id=str(customer_id or email or "anon"),
        products=products,
        commerce_mode=commerce,
        context=ctx,
        mode=mode if mode in ("auto", "confirm") else "auto",
    )
    return {"ok": True, **out}


@app.get("/api/client/orders/{order_id}/website-tips")
def client_website_tips(request: Request, order_id: str) -> dict:
    """Website Admin Tips — legal / SEO / performance / content."""
    customer_id, email = _client_store_identity(request)
    order = _ctx().sales.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")
    oid_cid = str(order.get("customer_id") or "")
    oid_email = str(order.get("email") or "").strip().lower()
    if customer_id and oid_cid and oid_cid != customer_id:
        if not email or oid_email != str(email).lower():
            raise HTTPException(status_code=403, detail="forbidden")
    from app.integration.vector import VectorContextService

    return VectorContextService(
        _memory_dir(), sales=_ctx().sales
    ).website_tips_for_order(order)


# —— Website Control v1 (Business Workspace) ——


def _website_content_svc():
    from app.integration.website_admin import WebsiteContentService

    return WebsiteContentService(_memory_dir())


def _website_design_svc():
    from app.integration.website_admin import WebsiteDesignService

    return WebsiteDesignService(_memory_dir())


def _assert_website_admin_access(request: Request, order_id: str) -> dict:
    """Ownership gate: customer owns order and it is a Website (not shop)."""
    from app.integration.website_admin import assert_website_order_access

    customer_id, email = _client_store_identity(request)
    order = _ctx().sales.get_order(order_id)
    return assert_website_order_access(
        order, customer_id=customer_id, email=email
    )


def _website_product_meta(order: dict) -> tuple[str | None, dict, _Path | None]:
    from pathlib import Path

    from app.integration.vector.website_tips import find_product_dir

    product_id = str(order.get("product_id") or "").strip() or None
    meta: dict = {}
    product_dir = find_product_dir(product_id) if product_id else None
    if product_dir and (product_dir / "meta.json").is_file():
        try:
            import json

            raw = json.loads((product_dir / "meta.json").read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                meta = raw
        except Exception:
            meta = {}
    return product_id, meta, product_dir


def _reapply_website_overlay(order_id: str, order: dict) -> bool:
    from app.integration.website_admin import apply_website_overlay_to_product_dir

    product_id, meta, product_dir = _website_product_meta(order)
    if not product_dir:
        return False
    name = str(
        meta.get("business_name")
        or order.get("company_name")
        or order.get("business_name")
        or ""
    )
    return apply_website_overlay_to_product_dir(
        _memory_dir(),
        order_id,
        product_dir,
        business_name=name,
        seed_meta=meta,
    )


@app.get("/api/client/websites/{order_id}/admin/preview-meta")
def website_admin_preview_meta(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc
    product_id, meta, product_dir = _website_product_meta(order)
    preview_url = None
    if product_id:
        preview_url = f"/api/factory/products/{product_id}/preview"
    return {
        "ok": True,
        "order_id": order_id,
        "product_id": product_id,
        "business_name": meta.get("business_name")
        or order.get("company_name")
        or order.get("business_name"),
        "niche": meta.get("niche") or order.get("niche"),
        "preview_url": preview_url,
        "has_product_dir": bool(product_dir),
        "commerce_mode": order.get("commerce_mode") or "standalone",
        "sections": {
            "website": True,
            "design": True,
            "media": True,
            "files": True,
            "support": True,
            "ai": True,
            "store": False,
            "crm": False,
            "automation": False,
            "marketing": False,
            "analytics": False,
        },
    }


@app.get("/api/client/websites/{order_id}/admin/content")
def website_admin_get_content(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc
    _pid, meta, _dir = _website_product_meta(order)
    return _website_content_svc().get_content(order_id, seed_meta=meta)


@app.put("/api/client/websites/{order_id}/admin/content")
@app.patch("/api/client/websites/{order_id}/admin/content")
async def website_admin_update_content(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc
    _pid, meta, _dir = _website_product_meta(order)
    result = _website_content_svc().update_content(
        order_id, payload, seed_meta=meta
    )
    _reapply_website_overlay(order_id, order)
    return result


@app.post("/api/client/websites/{order_id}/admin/content/undo")
def website_admin_content_undo(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        _pid, meta, _dir = _website_product_meta(order)
        result = _website_content_svc().undo(order_id, seed_meta=meta)
        _reapply_website_overlay(order_id, order)
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/websites/{order_id}/admin/content/redo")
def website_admin_content_redo(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        _pid, meta, _dir = _website_product_meta(order)
        result = _website_content_svc().redo(order_id, seed_meta=meta)
        _reapply_website_overlay(order_id, order)
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/websites/{order_id}/admin/design")
def website_admin_get_design(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc
    _pid, meta, _dir = _website_product_meta(order)
    name = str(meta.get("business_name") or order.get("company_name") or "")
    return _website_design_svc().get_design(order_id, business_name=name)


@app.put("/api/client/websites/{order_id}/admin/design")
@app.patch("/api/client/websites/{order_id}/admin/design")
async def website_admin_update_design(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc
    _pid, meta, _dir = _website_product_meta(order)
    name = str(meta.get("business_name") or order.get("company_name") or "")
    result = _website_design_svc().update_design(
        order_id, payload, business_name=name
    )
    _reapply_website_overlay(order_id, order)
    return result


@app.post("/api/client/websites/{order_id}/admin/design/undo")
def website_admin_design_undo(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        _pid, meta, _dir = _website_product_meta(order)
        name = str(meta.get("business_name") or order.get("company_name") or "")
        result = _website_design_svc().undo(order_id, business_name=name)
        _reapply_website_overlay(order_id, order)
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/websites/{order_id}/admin/design/redo")
def website_admin_design_redo(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        _pid, meta, _dir = _website_product_meta(order)
        name = str(meta.get("business_name") or order.get("company_name") or "")
        result = _website_design_svc().redo(order_id, business_name=name)
        _reapply_website_overlay(order_id, order)
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/websites/{order_id}/admin/media")
def website_admin_list_media(request: Request, order_id: str) -> dict:
    try:
        _assert_website_admin_access(request, order_id)
        rows = _website_content_svc().media.list_order_media(order_id)
        return {"ok": True, "media": rows}
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/websites/{order_id}/admin/media")
async def website_admin_upload_media(
    request: Request,
    order_id: str,
    file: UploadFile = File(...),
    role: str = "gallery",
) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        row = _website_content_svc().media.save_upload(
            file, order_id=order_id, role=role or "gallery"
        )
        row["url"] = f"/api/client/websites/{order_id}/admin/media/{row['id']}"
        return {"ok": True, "media": row, "order_id": order.get("order_id") or order_id}
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.delete("/api/client/websites/{order_id}/admin/media/{image_id}")
def website_admin_delete_media(
    request: Request, order_id: str, image_id: str
) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        _website_content_svc().media.delete_by_id(order_id, image_id)
        # Detach from content if referenced
        content_svc = _website_content_svc()
        _pid, meta, _dir = _website_product_meta(order)
        raw = content_svc.raw_content(order_id, seed_meta=meta)
        changed = False
        hero = raw.get("hero") if isinstance(raw.get("hero"), dict) else {}
        if isinstance(hero.get("image"), dict) and hero["image"].get("id") == image_id:
            raw["hero"] = {**hero, "image": None}
            changed = True
        for list_key in ("gallery", "team"):
            items = raw.get(list_key)
            if not isinstance(items, list):
                continue
            next_items = []
            list_changed = False
            for item in items:
                if not isinstance(item, dict):
                    continue
                img = item.get("image")
                if isinstance(img, dict) and img.get("id") == image_id:
                    list_changed = True
                    if list_key == "gallery":
                        continue
                    next_items.append({**item, "image": None})
                else:
                    next_items.append(item)
            if list_changed:
                raw[list_key] = next_items
                changed = True
        if changed:
            content_svc.update_content(
                order_id,
                {
                    "hero": raw.get("hero"),
                    "gallery": raw.get("gallery"),
                    "team": raw.get("team"),
                },
                seed_meta=meta,
            )
            _reapply_website_overlay(order_id, order)
        return {"ok": True, "deleted": image_id}
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc

@app.get("/api/client/websites/{order_id}/admin/media/{image_id}")
def website_admin_serve_media(
    request: Request,
    order_id: str,
    image_id: str,
    access_token: str | None = None,
) -> FileResponse:
    """Serve owner media. Auth via Bearer or access_token query (for <img>)."""
    try:
        if access_token:
            from app.integration.customer_identity.auth import decode_client_token

            payload = decode_client_token(access_token)
            if not payload or not payload.get("sub"):
                raise HTTPException(status_code=401, detail="client_auth_required")
            # Attach synthetic identity for ownership check via order fields
            customer_id = str(payload["sub"])
            email = str(payload.get("email") or "").strip() or None
            order = _ctx().sales.get_order(order_id)
            if not order:
                raise ValueError("order_not_found")
            oid_cid = str(order.get("customer_id") or "")
            oid_email = str(order.get("email") or "").strip().lower()
            if customer_id and oid_cid and oid_cid != customer_id:
                if not email or oid_email != str(email).lower():
                    raise ValueError("forbidden")
            kind = str(order.get("product_kind") or "").strip().lower()
            if kind == "shop" or str(order.get("package_id") or "").lower() == "ecommerce_shop":
                raise ValueError("not_a_website_order")
        else:
            _assert_website_admin_access(request, order_id)
        path = _website_content_svc().media.find_by_id(order_id, image_id)
        if path is None:
            raise ValueError("image_not_found")
        media = {
            ".webp": "image/webp",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
        }.get(path.suffix.lower(), "application/octet-stream")
        return FileResponse(path, media_type=media)
    except HTTPException:
        raise
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/control-capabilities")
def client_control_capabilities_api(request: Request) -> dict:
    """Honest Workspace capability map for Basic / Business / Premium (+ gift)."""
    from app.integration.client_control_contract import client_control_capabilities

    customer_id, _email = _client_store_identity(request)
    me = _customer_identity().me(customer_id) if customer_id else {}
    gift = bool(me.get("gift_unlimited") or me.get("unlimited"))
    return client_control_capabilities(
        "premium" if gift else None,
        gift_unlimited=gift,
    )


@app.get("/api/client/websites/{order_id}/admin/cinematic")
def website_admin_list_cinematic(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        _pid, _meta, product_dir = _website_product_meta(order)
        if not product_dir:
            raise ValueError("product_dir_missing")
        from app.integration.website_admin.cinematic_control import (
            ensure_control_point_original,
            list_cinematic_scenes,
        )

        ensure_control_point_original(product_dir)
        out = list_cinematic_scenes(product_dir)
        from app.integration.client_control_contract import client_control_capabilities

        caps = client_control_capabilities(
            str(order.get("package_id") or ""),
            gift_unlimited=False,
        )
        out["capabilities"] = caps.get("website")
        return out
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/websites/{order_id}/admin/cinematic/{scene}/replace")
async def website_admin_replace_cinematic(
    request: Request, order_id: str, scene: int, file: UploadFile = File(...)
) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        _pid, _meta, product_dir = _website_product_meta(order)
        if not product_dir:
            raise ValueError("product_dir_missing")
        from app.integration.website_admin.cinematic_control import replace_cinematic_scene

        data = await file.read()
        result = replace_cinematic_scene(
            product_dir, int(scene), data, filename=file.filename or "upload.jpg"
        )
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/websites/{order_id}/admin/cinematic/{scene}/restore")
def website_admin_restore_cinematic(
    request: Request, order_id: str, scene: int
) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        _pid, _meta, product_dir = _website_product_meta(order)
        if not product_dir:
            raise ValueError("product_dir_missing")
        from app.integration.website_admin.cinematic_control import restore_cinematic_scene

        return restore_cinematic_scene(product_dir, int(scene))
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.get("/api/client/websites/{order_id}/admin/versions")
def website_admin_list_versions(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        _pid, _meta, product_dir = _website_product_meta(order)
        if not product_dir:
            raise ValueError("product_dir_missing")
        from app.integration.website_admin.cinematic_control import list_website_versions

        return list_website_versions(product_dir)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/websites/{order_id}/admin/versions/restore-original")
def website_admin_restore_original(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        _pid, _meta, product_dir = _website_product_meta(order)
        if not product_dir:
            raise ValueError("product_dir_missing")
        from app.integration.website_admin.cinematic_control import restore_website_original

        result = restore_website_original(product_dir)
        _reapply_website_overlay(order_id, order)
        return result
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/stores/{order_id}/admin/restore-original")
def store_admin_restore_original(request: Request, order_id: str) -> dict:
    try:
        _assert_store_admin_access(request, order_id)
        product_dir, _order = _shop_product_dir_for_order(order_id)
        if product_dir is None:
            raise ValueError("product_dir_missing")
        from app.integration.store_admin.shop_live_sync import restore_shop_original

        return restore_shop_original(product_dir)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc


@app.post("/api/client/websites/{order_id}/admin/ai-edit")
async def website_admin_ai_edit(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_payload")
        prompt = str(payload.get("prompt") or "").strip()
        from app.integration.website_admin import (
            apply_content_intent,
            parse_ai_edit_prompt,
        )

        parsed = parse_ai_edit_prompt(prompt)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc

    _pid, meta, _dir = _website_product_meta(order)
    name = str(meta.get("business_name") or order.get("company_name") or "")
    content_svc = _website_content_svc()
    design_svc = _website_design_svc()
    current = content_svc.raw_content(order_id, seed_meta=meta)
    content_patch = apply_content_intent(
        current, parsed.get("content_patch") or {}
    )
    out_content = None
    out_design = None
    if content_patch:
        out_content = content_svc.update_content(
            order_id, content_patch, seed_meta=meta
        )
    design_patch = parsed.get("design_patch") or {}
    if design_patch:
        out_design = design_svc.update_design(
            order_id, design_patch, business_name=name
        )
    _reapply_website_overlay(order_id, order)
    return {
        "ok": True,
        "summary": parsed.get("summary") or "Updated",
        "content": (out_content or content_svc.get_content(order_id, seed_meta=meta)).get(
            "content"
        ),
        "design": (
            out_design or design_svc.get_design(order_id, business_name=name)
        ).get("design"),
    }


@app.post("/api/client/websites/{order_id}/admin/publish")
def website_admin_publish(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc
    product_id, meta, product_dir = _website_product_meta(order)
    content = _website_content_svc().raw_content(order_id, seed_meta=meta)
    from app.integration.website_admin.publish_safety import evaluate_publish_safety

    safety = evaluate_publish_safety(content, product_dir=product_dir)
    if not safety.get("ok"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "publish_blocked",
                "message": "Publish blocked — fix quality issues first.",
                "blockers": safety.get("blockers") or [],
                "warnings": safety.get("warnings") or [],
            },
        )
    applied = _reapply_website_overlay(order_id, order)
    published = False
    public_url = None
    if product_id and product_dir:
        try:
            # Soft publish marker for client preview (Path A delivery may skip CEO approve)
            meta = dict(meta)
            meta["owner_overlay_applied"] = True
            meta["publish_safety"] = safety
            meta["client_publish_requested_at"] = __import__(
                "datetime"
            ).datetime.now(__import__("datetime").timezone.utc).isoformat()
            (product_dir / "meta.json").write_text(
                __import__("json").dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            public_url = f"/api/factory/products/{product_id}/preview"
            published = True
        except Exception:
            published = False
    return {
        "ok": True,
        "applied": applied,
        "published": published,
        "preview_url": public_url,
        "product_id": product_id,
        "warnings": safety.get("warnings") or [],
    }


@app.get("/api/client/websites/{order_id}/admin/publish-check")
def website_admin_publish_check(request: Request, order_id: str) -> dict:
    try:
        order = _assert_website_admin_access(request, order_id)
    except ValueError as exc:
        raise _client_store_http_error(exc) from exc
    _pid, meta, product_dir = _website_product_meta(order)
    content = _website_content_svc().raw_content(order_id, seed_meta=meta)
    from app.integration.website_admin.publish_safety import evaluate_publish_safety

    safety = evaluate_publish_safety(content, product_dir=product_dir)
    return {"ok": True, **safety}

@app.post("/api/sales/order-materials", response_model=OrderMaterialUploadResponse)
async def upload_sales_order_material(
    file: UploadFile = File(...),
    session_id: str = "anon",
) -> OrderMaterialUploadResponse:
    from app.integration.order_materials_service import OrderMaterialsService
    from app.schemas import OrderMaterialUploadResponse as _Resp

    svc = OrderMaterialsService(_memory_dir())
    try:
        row = svc.save(file, session_id=(session_id or "anon")[:64])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _Resp(**row)


@app.post("/api/sales/order-insights-preview", response_model=OrderInsightsPreviewResponse)
def preview_sales_order_insights(body: OrderInsightsPreviewRequest) -> OrderInsightsPreviewResponse:
    from app.integration.order_materials_service import OrderMaterialsService
    from app.schemas import OrderInsightsPreviewResponse as _Resp

    website = (body.company_website or "").strip() or None
    site_analysis = None
    if website:
        try:
            site_analysis = _ctx().sales._analyze_company_website(  # noqa: SLF001
                _ctx().sales._normalize_company_website(website)  # noqa: SLF001
            )
        except Exception:
            site_analysis = None

    social = {
        "google_business": (body.google_business or "").strip(),
        "instagram": (body.instagram or "").strip(),
        "facebook": (body.facebook or "").strip(),
        "tiktok": (body.tiktok or "").strip(),
        "linkedin": (body.linkedin or "").strip(),
        "youtube": (body.youtube or "").strip(),
        "telegram": (body.telegram or "").strip(),
        "whatsapp": (body.whatsapp or "").strip(),
    }
    social = {k: v for k, v in social.items() if v}
    mats = OrderMaterialsService(_memory_dir())
    insights = mats.build_buyer_insights(
        company_website=_ctx().sales._normalize_company_website(website) if website else None,  # noqa: SLF001
        domain=(body.existing_domain or "").strip() or None,
        domain_status=(body.domain_status or "").strip() or None,
        social=social,
        material_ids=list(body.material_ids or []),
        site_analysis=site_analysis,
        niche=(body.niche or "").strip() or None,
        city=(body.city or "").strip() or None,
    )
    visual_experience = None
    try:
        from app.integration.path_a_visual_preview import resolve_path_a_visual_preview
        from app.integration.locale_service import resolve_generation_language

        visual_experience = resolve_path_a_visual_preview(
            niche_id=body.niche,
            tier=body.package_id or "business",
            specialization=body.specialization,
            locale=resolve_generation_language(
                getattr(body, "locale", None),
                getattr(body, "ui_lang", None),
                getattr(body, "language", None),
                market_code=str(
                    getattr(body, "market", None) or getattr(body, "market_code", None) or ""
                )
                or None,
            ),
        )
    except Exception:
        visual_experience = None
    return _Resp(
        ok=True,
        checks=list(insights.get("checks") or []),
        note_de=str(insights.get("note_de") or ""),
        site_analysis=insights.get("site_analysis") if isinstance(insights.get("site_analysis"), dict) else None,
        visual_experience=visual_experience,
    )


@app.get("/api/sales/orders", response_model=SalesOrdersListResponse)
def list_sales_orders() -> SalesOrdersListResponse:
    from app.schemas import SalesOrderSummary

    items = _ctx().sales.list_orders()
    return SalesOrdersListResponse(orders=[SalesOrderSummary(**o) for o in items])


@app.post("/api/sales/orders/{order_id}/confirm", response_model=SalesOrderActionResponse)
def confirm_sales_order(order_id: str) -> SalesOrderActionResponse:
    try:
        order = _ctx().sales.confirm_order(order_id)
    except ValueError as e:
        if str(e) == "order_not_found":
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        raise HTTPException(status_code=400, detail="Заявка уже обработана")
    from app.schemas import SalesOrderSummary

    return SalesOrderActionResponse(
        ok=True,
        message="Заявка подтверждена. Скопируйте КП и отправьте клиенту.",
        order=SalesOrderSummary(**order),
    )


@app.post("/api/sales/orders/{order_id}/start-production", response_model=SalesOrderActionResponse)
def start_sales_order_production(order_id: str) -> SalesOrderActionResponse:
    try:
        result = _ctx().sales.start_production(order_id)
    except ValueError as e:
        if str(e) == "order_not_found":
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        raise HTTPException(status_code=400, detail="Нельзя запустить производство для этой заявки")
    from app.schemas import SalesOrderSummary

    return SalesOrderActionResponse(
        ok=True,
        message=result["message"],
        order=SalesOrderSummary(**result["order"]),
        product_id=result.get("product_id"),
    )


@app.get("/api/sales/payment-status", response_model=PaymentStatusResponse)
def sales_payment_status() -> PaymentStatusResponse:
    data = _ctx().revenue.payment_status()
    return PaymentStatusResponse(**data)


@app.get("/api/sales/email-status", response_model=EmailStatusResponse)
def sales_email_status() -> EmailStatusResponse:
    data = _ctx().revenue.email_status()
    return EmailStatusResponse(**data)


@app.post("/api/sales/orders/{order_id}/checkout", response_model=SalesCheckoutResponse)
def sales_order_checkout(order_id: str, request: SalesCheckoutRequest) -> SalesCheckoutResponse:
    try:
        result = _ctx().revenue.begin_checkout(
            order_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )
    except ValueError as e:
        code = str(e)
        if code == "order_not_found":
            raise HTTPException(status_code=404, detail="Заказ не найден")
        if code == "payment_not_configured":
            raise HTTPException(status_code=400, detail="Платёжная система не настроена")
        if code == "invalid_status":
            raise HTTPException(status_code=400, detail="Заказ нельзя оплатить в текущем статусе")
        if code.startswith("stripe_error:"):
            stripe_detail = code.split(":", 1)[1].strip() or "Stripe отклонил оплату"
            raise HTTPException(
                status_code=400,
                detail=f"Stripe: {stripe_detail}",
            )
        raise HTTPException(status_code=400, detail="Нельзя оплатить этот заказ")
    return SalesCheckoutResponse(**result)


@app.get("/api/sales/orders/{order_id}/status", response_model=SalesOrderPublicStatus)
def sales_order_public_status(order_id: str) -> SalesOrderPublicStatus:
    try:
        data = _ctx().sales.public_status(order_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Bestellung nicht gefunden")
    return SalesOrderPublicStatus(**data)


@app.post(
    "/api/sales/orders/{order_id}/deployment-preference",
    response_model=SalesOrderPublicStatus,
)
def sales_order_deployment_preference(
    order_id: str, request: DeploymentPreferenceRequest
) -> SalesOrderPublicStatus:
    """Path A — ZIP Only vs Assisted Deployment (no host passwords stored)."""
    try:
        data = _ctx().sales.set_deployment_preference(
            order_id,
            preference=request.preference,
            hosting_provider=request.hosting_provider,
        )
    except ValueError as exc:
        code = str(exc)
        mapping = {
            "order_not_found": (404, "Bestellung nicht gefunden"),
            "download_not_ready": (
                400,
                "ZIP noch nicht bereit — Veröffentlichungswahl später",
            ),
            "invalid_preference": (400, "Ungültige Auswahl"),
            "invalid_provider": (400, "Ungültiger Hosting-Anbieter"),
        }
        status, detail = mapping.get(code, (400, "Auswahl fehlgeschlagen"))
        raise HTTPException(status_code=status, detail=detail)
    return SalesOrderPublicStatus(**data)


@app.post(
    "/api/sales/orders/{order_id}/publish-status",
    response_model=SalesOrderPublicStatus,
)
def sales_order_publish_status(
    order_id: str, request: PublishStatusRequest
) -> SalesOrderPublicStatus:
    """Mark ZIP downloaded or website online (client go-live completion)."""
    try:
        data = _ctx().sales.set_publish_status(
            order_id,
            state=request.state,
            published_url=request.published_url,
        )
    except ValueError as exc:
        code = str(exc)
        mapping = {
            "order_not_found": (404, "Bestellung nicht gefunden"),
            "download_not_ready": (400, "ZIP noch nicht bereit"),
            "url_required": (400, "Website-URL erforderlich"),
            "invalid_url": (400, "Ungültige URL"),
            "invalid_state": (400, "Ungültiger Status"),
        }
        status, detail = mapping.get(code, (400, "Status fehlgeschlagen"))
        raise HTTPException(status_code=status, detail=detail)
    return SalesOrderPublicStatus(**data)


@app.post(
    "/api/sales/orders/{order_id}/next-offer-interest",
    response_model=SalesOrderPublicStatus,
)
def sales_order_next_offer_interest(
    order_id: str, request: NextOfferInterestRequest
) -> SalesOrderPublicStatus:
    """Soft LTV interest (AI Business Assistant etc.) — no checkout yet."""
    try:
        data = _ctx().sales.log_next_offer_interest(
            order_id,
            offer_id=request.offer_id,
            note=request.note,
        )
    except ValueError as exc:
        code = str(exc)
        mapping = {
            "order_not_found": (404, "Bestellung nicht gefunden"),
            "not_paid": (400, "Bestellung nicht bezahlt"),
            "invalid_offer": (400, "Ungültiges Angebot"),
        }
        status, detail = mapping.get(code, (400, "Anfrage fehlgeschlagen"))
        raise HTTPException(status_code=status, detail=detail)
    return SalesOrderPublicStatus(**data)


@app.post(
    "/api/sales/orders/{order_id}/reviews",
    response_model=ClientReviewSubmitResponse,
)
def sales_order_submit_review(
    order_id: str, request: ClientReviewSubmitRequest
) -> ClientReviewSubmitResponse:
    try:
        result = _ctx().reviews.submit(
            order_id=order_id,
            token=request.token,
            stars=request.stars,
            text=request.text,
            show_company_name=request.show_company_name,
            show_logo=request.show_logo,
            company_display_name=request.company_display_name,
        )
    except ValueError as exc:
        code = str(exc)
        mapping = {
            "order_not_found": (404, "Bestellung nicht gefunden"),
            "not_eligible": (403, "Bewertung erst nach Übergabe möglich"),
            "bad_token": (403, "Ungültiger Bewertungstoken"),
            "already_submitted": (409, "Bewertung bereits gesendet"),
            "bad_stars": (400, "Sterne: 1–5"),
            "too_short": (400, "Text zu kurz (min. 20 Zeichen)"),
            "too_long": (400, "Text zu lang (max. 1000 Zeichen)"),
        }
        status, detail = mapping.get(code, (400, "Bewertung abgelehnt"))
        raise HTTPException(status_code=status, detail=detail) from None
    return ClientReviewSubmitResponse(**result)


@app.get("/api/public/reviews", response_model=ClientReviewsPublicResponse)
def public_client_reviews(lang: str = "de") -> ClientReviewsPublicResponse:
    data = _ctx().reviews.public_feed(lang=lang)
    return ClientReviewsPublicResponse(**data)


@app.post("/api/public/reviews/submit", response_model=ClientReviewSubmitResponse)
def public_guest_review_submit(
    request: ClientReviewGuestSubmitRequest,
    req: Request,
) -> ClientReviewSubmitResponse:
    """Open storefront guest review — pending until CEO approve."""
    ip = ""
    try:
        ip = (req.client.host if req.client else "") or ""
        forwarded = (req.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        if forwarded:
            ip = forwarded
    except Exception:
        ip = ""
    try:
        result = _ctx().reviews.submit_guest(
            author_name=request.author_name,
            company=request.company,
            email=request.email,
            stars=request.stars,
            text=request.text,
            honeypot=request.website,
            client_ip=ip,
        )
    except ValueError as exc:
        code = str(exc)
        mapping = {
            "spam": (400, "Anfrage abgelehnt"),
            "bad_name": (400, "Name erforderlich"),
            "bad_email": (400, "Gültige E-Mail erforderlich"),
            "bad_stars": (400, "Sterne: 1–5"),
            "too_short": (400, "Text zu kurz (min. 20 Zeichen)"),
            "too_long": (400, "Text zu lang (max. 1000 Zeichen)"),
            "rate_limited": (429, "Zu viele Anfragen — bitte später erneut versuchen"),
        }
        status, detail = mapping.get(code, (400, "Bewertung abgelehnt"))
        raise HTTPException(status_code=status, detail=detail) from None
    return ClientReviewSubmitResponse(**result)


def _review_moderation_item(r: dict) -> ClientReviewModerationItem:
    return ClientReviewModerationItem(
        review_id=str(r.get("review_id") or ""),
        order_id=str(r.get("order_id") or ""),
        stars=int(r.get("stars") or 0),
        text=str(r.get("text") or ""),
        status=str(r.get("status") or ""),
        flags=list(r.get("flags") or []),
        author_name=r.get("author_name"),
        author_email=r.get("author_email"),
        company_display_name=r.get("company_display_name"),
        created_at=r.get("created_at"),
        published_at=r.get("published_at"),
        show_company_name=bool(r.get("show_company_name")),
        show_logo=bool(r.get("show_logo")),
        verified_purchase=bool(r.get("verified_purchase", True)),
        source=r.get("source"),
    )


@app.get("/api/owner/reviews/pending", response_model=ClientReviewsPendingResponse)
def owner_reviews_pending() -> ClientReviewsPendingResponse:
    pending = _ctx().reviews.list_pending()
    items = [_review_moderation_item(r) for r in pending]
    return ClientReviewsPendingResponse(pending=items, count=len(items))


@app.get("/api/owner/reviews", response_model=ClientReviewsOwnerListResponse)
def owner_reviews_list(status: str | None = None) -> ClientReviewsOwnerListResponse:
    rows = _ctx().reviews.list_all(status=status)
    all_rows = _ctx().reviews.list_all()
    return ClientReviewsOwnerListResponse(
        reviews=[_review_moderation_item(r) for r in rows],
        count=len(rows),
        pending_count=sum(1 for r in all_rows if r.get("status") == "pending"),
        published_count=sum(1 for r in all_rows if r.get("status") == "published"),
        rejected_count=sum(1 for r in all_rows if r.get("status") == "rejected"),
    )


@app.post("/api/owner/reviews/{review_id}/moderate")
def owner_review_moderate(
    review_id: str, request: ClientReviewModerateRequest
) -> dict:
    try:
        row = _ctx().reviews.moderate(
            review_id, action=request.action, note=request.note
        )
    except ValueError as exc:
        code = str(exc)
        if code == "not_found":
            raise HTTPException(status_code=404, detail="Отзыв не найден") from None
        raise HTTPException(status_code=400, detail=code) from None
    return {"ok": True, "review": row}


@app.post("/api/owner/reviews/publish-direct")
def owner_review_publish_direct(request: ClientReviewOwnerPublishRequest) -> dict:
    """CEO publishes a review to /site without order token."""
    try:
        return _ctx().reviews.owner_publish_direct(
            stars=request.stars,
            text=request.text,
            company_display_name=request.company_display_name,
            service_label=request.service_label or "Landing",
            verified_purchase=bool(request.verified_purchase),
            publish=bool(request.publish),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.post("/api/owner/reviews/seed-display")
def owner_reviews_seed_display() -> dict:
    """Seed /site reviews if empty (CEO-requested visibility; not order-verified)."""
    return _ctx().reviews.ensure_display_reviews()


@app.get("/api/sales/orders/{order_id}/download")
def sales_order_client_download(order_id: str) -> StreamingResponse:
    """Path A — client downloads landing ZIP after payment/production."""
    try:
        data, filename = _ctx().sales.build_client_download(order_id)
    except ValueError as exc:
        code = str(exc)
        if code == "order_not_found":
            raise HTTPException(status_code=404, detail="Bestellung nicht gefunden") from None
        if code == "download_not_ready":
            raise HTTPException(
                status_code=409,
                detail="Download noch nicht bereit — Zahlung und Produktion abwarten.",
            ) from None
        if code == "factory_unavailable":
            raise HTTPException(status_code=503, detail="Factory nicht verfügbar") from None
        if code == "product_not_found":
            raise HTTPException(status_code=404, detail="Produkt nicht gefunden") from None
        if code.startswith("quality_gate_failed") or "Compliance" in type(exc).__name__:
            raise HTTPException(
                status_code=422,
                detail="Website-Archiv noch nicht freigegeben (Qualitätsprüfung). Produktion erneut starten.",
            ) from None
        raise HTTPException(
            status_code=422,
            detail="Website-Archiv konnte nicht erstellt werden. Bitte Support mit Bestellnummer kontaktieren.",
        ) from None
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/sales/orders/{order_id}/confirm-payment", response_model=RevenuePaymentResponse)
def sales_order_confirm_payment(order_id: str) -> RevenuePaymentResponse:
    try:
        result = _ctx().revenue.confirm_stripe_payment(order_id)
    except ValueError as e:
        code = str(e)
        if code == "order_not_found":
            raise HTTPException(status_code=404, detail="Заказ не найден")
        if code == "stripe_only":
            raise HTTPException(status_code=400, detail="Подтверждение доступно только для Stripe")
        if code == "no_checkout_session":
            raise HTTPException(status_code=400, detail="Сессия оплаты не найдена")
        if code == "payment_not_confirmed":
            raise HTTPException(status_code=409, detail="Оплата ещё не подтверждена Stripe")
        if code == "order_mismatch":
            raise HTTPException(status_code=400, detail="Заказ не совпадает с сессией")
        if code == "amount_mismatch":
            raise HTTPException(status_code=400, detail="Сумма не совпадает")
        raise HTTPException(status_code=400, detail="Оплата не подтверждена")
    return RevenuePaymentResponse(**result)


@app.post("/api/sales/orders/{order_id}/pay-sandbox", response_model=RevenuePaymentResponse)
def sales_order_pay_sandbox(order_id: str) -> RevenuePaymentResponse:
    try:
        result = _ctx().revenue.complete_sandbox_payment(order_id)
    except ValueError as e:
        code = str(e)
        if code == "order_not_found":
            raise HTTPException(status_code=404, detail="Заказ не найден")
        if code == "sandbox_only":
            raise HTTPException(status_code=400, detail="Sandbox недоступен")
        if code == "amount_mismatch":
            raise HTTPException(status_code=400, detail="Сумма не совпадает")
        raise HTTPException(status_code=400, detail="Оплата не прошла")
    return RevenuePaymentResponse(**result)


@app.post("/api/sales/orders/{order_id}/pay-demo", response_model=RevenuePaymentResponse)
def sales_order_pay_demo(order_id: str) -> RevenuePaymentResponse:
    """D0 Demo Payment Bridge — only tagged demo orders; never real money."""
    try:
        result = _ctx().revenue.complete_demo_payment(order_id)
    except ValueError as e:
        code = str(e)
        if code == "order_not_found":
            raise HTTPException(status_code=404, detail="Заказ не найден")
        if code == "demo_payment_disabled":
            raise HTTPException(
                status_code=403,
                detail="Demo Payment Bridge отключён (Production lock)",
            )
        if code == "not_a_demo_order":
            raise HTTPException(
                status_code=403,
                detail="Demo Payment только для demo-заказов",
            )
        if code == "amount_mismatch":
            raise HTTPException(status_code=400, detail="Сумма не совпадает")
        raise HTTPException(status_code=400, detail="Demo Payment не прошёл")
    return RevenuePaymentResponse(**result)


@app.post(
    "/api/owner/demo-orders/{order_id}/complete-payment",
    response_model=RevenuePaymentResponse,
)
def owner_demo_complete_payment(order_id: str) -> RevenuePaymentResponse:
    """Owner-only alias for Demo Payment Bridge (Mission Control demos)."""
    return sales_order_pay_demo(order_id)


@app.get("/api/owner/notifications", response_model=OwnerNotificationsResponse)
def owner_notifications() -> OwnerNotificationsResponse:
    items = _ctx().notifications.list_recent()
    return OwnerNotificationsResponse(
        notifications=[OwnerNotification(**n) for n in items]
    )


# --- G3.1 Evolution Center (AI Support · Owner approval required) ---------------


def _evolution_service():
    from app.evolution.service import EvolutionSupportService

    return EvolutionSupportService(_memory_dir())


@app.post("/api/public/evolution/tickets")
def public_evolution_ticket(body: dict) -> dict:
    """Client support intake — creates ticket + Change Proposal (not applied)."""
    from fastapi import HTTPException

    message = str((body or {}).get("message") or "")
    contact = str((body or {}).get("contact") or "")
    try:
        return _evolution_service().submit_ticket(message=message, contact=contact)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/owner/evolution/proposals")
def owner_evolution_proposals(status: str | None = None) -> dict:
    rows = _evolution_service().list_proposals(status=status)
    return {
        "proposals": rows,
        "rule": "AI may recommend changes. Only the Owner approves changes.",
        "applied_never_automatic": True,
    }


@app.get("/api/owner/evolution/proposals/{proposal_id}")
def owner_evolution_proposal(proposal_id: str) -> dict:
    from fastapi import HTTPException

    row = _evolution_service().get_proposal(proposal_id)
    if row is None:
        raise HTTPException(status_code=404, detail="proposal_not_found")
    return row


@app.post("/api/owner/evolution/proposals/{proposal_id}/approve")
def owner_evolution_approve(proposal_id: str, body: dict | None = None) -> dict:
    from fastapi import HTTPException

    note = str((body or {}).get("owner_note") or "")
    try:
        return _evolution_service().approve_proposal(proposal_id, owner_note=note)
    except ValueError as exc:
        code = str(exc)
        status = 404 if code == "proposal_not_found" else 400
        raise HTTPException(status_code=status, detail=code) from exc


@app.post("/api/owner/evolution/proposals/{proposal_id}/reject")
def owner_evolution_reject(proposal_id: str, body: dict | None = None) -> dict:
    from fastapi import HTTPException

    note = str((body or {}).get("owner_note") or "")
    try:
        return _evolution_service().reject_proposal(proposal_id, owner_note=note)
    except ValueError as exc:
        code = str(exc)
        status = 404 if code == "proposal_not_found" else 400
        raise HTTPException(status_code=status, detail=code) from exc


@app.post("/api/owner/evolution/learning/{learning_id}/promote")
def owner_evolution_promote_rule(learning_id: str, body: dict | None = None) -> dict:
    """Second Owner confirm — Rule Candidate → Knowledge Ledger (still not auto-apply)."""
    from fastapi import HTTPException

    note = str((body or {}).get("owner_note") or "")
    try:
        return _evolution_service().promote_rule_candidate(
            learning_id, owner_note=note
        )
    except ValueError as exc:
        code = str(exc)
        status = 404 if code == "learning_not_found" else 400
        raise HTTPException(status_code=status, detail=code) from exc


@app.post("/api/owner/evolution/learning/{learning_id}/dismiss")
def owner_evolution_dismiss_rule(learning_id: str, body: dict | None = None) -> dict:
    """Dismiss Rule Candidate — do not add to Knowledge Ledger."""
    from fastapi import HTTPException

    note = str((body or {}).get("owner_note") or "")
    try:
        return _evolution_service().dismiss_rule_candidate(
            learning_id, owner_note=note
        )
    except ValueError as exc:
        code = str(exc)
        status = 404 if code == "learning_not_found" else 400
        raise HTTPException(status_code=status, detail=code) from exc


@app.get("/api/owner/evolution/ledger")
def owner_evolution_ledger() -> dict:
    from app.evolution.service import EVOLUTION_MISSION, OWNER_APPROVAL_RULE

    return {
        "entries": _evolution_service().list_ledger(),
        "learning_queue": _evolution_service().list_learning_queue(),
        "auto_apply": False,
        "rule": OWNER_APPROVAL_RULE,
        "mission": EVOLUTION_MISSION,
    }


@app.post("/api/public/website-analysis")
def public_website_analysis(body: dict) -> dict:
    """Website Analysis v1 — owner report + Repair/New funnel CTAs."""
    from fastapi import HTTPException

    from app.integration.website_analysis_v1 import WebsiteAnalysisV1

    url = str((body or {}).get("url") or "").strip()
    locale = str((body or {}).get("locale") or "ru").strip()[:8] or "ru"
    use_cache = bool((body or {}).get("use_cache", True))
    email = str((body or {}).get("email") or "").strip()
    problem_note = str((body or {}).get("problem_note") or (body or {}).get("description") or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url_required")
    report = WebsiteAnalysisV1(_memory_dir()).analyze(
        url,
        locale=locale,
        use_cache=use_cache,
        email=email,
        problem_note=problem_note,
        save_case=True,
    )
    return report


@app.post("/api/public/vc-auditor")
def public_vc_website_auditor(body: dict) -> dict:
    """Virtus Core Website Auditor — public URL mode (Apify-ready brand)."""
    from fastapi import HTTPException

    from app.integration.vc_auditor import VirtusCoreWebsiteAuditor

    url = str((body or {}).get("url") or "").strip()
    locale = str((body or {}).get("locale") or "de").strip()[:8] or "de"
    if not url:
        raise HTTPException(status_code=400, detail="url_required")
    return VirtusCoreWebsiteAuditor(_memory_dir()).analyze_url(url, locale=locale)


@app.get("/api/public/vc-auditor/{report_id}")
def public_vc_auditor_get(report_id: str) -> dict:
    from fastapi import HTTPException

    from app.integration.vc_auditor import VirtusCoreWebsiteAuditor

    row = VirtusCoreWebsiteAuditor(_memory_dir()).get_report(report_id)
    if not row:
        raise HTTPException(status_code=404, detail="report_not_found")
    return row


@app.get("/api/public/vc-auditor/{report_id}/export")
def public_vc_auditor_export(report_id: str, format: str = "json"):
    from fastapi import HTTPException
    from fastapi.responses import Response

    from app.integration.vc_auditor import VirtusCoreWebsiteAuditor
    from app.integration.vc_auditor.branding import PRODUCT_ID

    out = VirtusCoreWebsiteAuditor(_memory_dir()).export(report_id, format)
    if not out:
        raise HTTPException(status_code=404, detail="report_not_found")
    body, media, suffix = out
    filename = f"{PRODUCT_ID}_{report_id}.{suffix}"
    return Response(
        content=body,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/client/orders/{order_id}/vc-auditor")
def client_vc_auditor_for_order(request: Request, order_id: str, locale: str = "de") -> dict:
    """Virtus Core mode — audit Factory package without URL entry."""
    customer_id, email = _client_store_identity(request)
    order = _ctx().sales.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")
    oid_cid = str(order.get("customer_id") or "")
    oid_email = str(order.get("email") or "").strip().lower()
    if customer_id and oid_cid and oid_cid != customer_id:
        if not email or oid_email != str(email).lower():
            raise HTTPException(status_code=403, detail="forbidden")
    from app.integration.vc_auditor import VirtusCoreWebsiteAuditor

    product_id = str(order.get("product_id") or "").strip() or None
    return VirtusCoreWebsiteAuditor(_memory_dir()).analyze_virtus_product(
        product_id=product_id,
        order_id=order_id,
        locale=locale or "de",
        niche=str(order.get("business_name") or "") or None,
    )


@app.get("/api/client/orders/{order_id}/vc-auditor/export")
def client_vc_auditor_export(
    request: Request, order_id: str, format: str = "markdown", locale: str = "de"
):
    """Run Virtus audit then export (JSON/CSV/MD/PDF)."""
    from fastapi.responses import Response

    from app.integration.vc_auditor import VirtusCoreWebsiteAuditor
    from app.integration.vc_auditor.branding import PRODUCT_ID
    from app.integration.vc_auditor.export import export_report

    report = client_vc_auditor_for_order(request, order_id, locale=locale)
    if not report.get("ok"):
        raise HTTPException(status_code=404, detail=report.get("error") or "audit_failed")
    body, media, suffix = export_report(report, format)
    filename = f"{PRODUCT_ID}_{order_id}.{suffix}"
    return Response(
        content=body,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@app.get("/api/public/website-analysis/{case_id}")
def public_website_analysis_case(case_id: str) -> dict:
    from fastapi import HTTPException

    from app.integration.website_analysis_v1 import WebsiteAnalysisV1

    row = WebsiteAnalysisV1(_memory_dir()).get_case(case_id)
    if not row:
        raise HTTPException(status_code=404, detail="case_not_found")
    return row


@app.get("/api/client/analysis-cases")
def client_analysis_cases(email: str = "") -> dict:
    """List saved analysis cases for a client email (cabinet)."""
    from fastapi import HTTPException

    from app.integration.website_analysis_v1 import WebsiteAnalysisV1

    em = str(email or "").strip()
    if not em or "@" not in em:
        raise HTTPException(status_code=400, detail="email_required")
    items = WebsiteAnalysisV1(_memory_dir()).list_cases_for_email(em)
    return {"ok": True, "email": em.lower(), "cases": items}


@app.get("/api/factory/products", response_model=FactoryProductsResponse)
def list_factory_products() -> FactoryProductsResponse:
    items = _ctx().factory.list_products()
    return FactoryProductsResponse(products=[FactoryProduct(**p) for p in items])


@app.get("/api/factory/products/{product_id}", response_model=FactoryProduct)
def get_factory_product(product_id: str) -> FactoryProduct:
    product = _ctx().factory.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    return FactoryProduct(**product)


@app.get("/api/factory/products/{product_id}/preview")
def preview_factory_product(product_id: str) -> HTMLResponse:
    html = _ctx().factory.read_preview_html(product_id)
    if not html:
        raise HTTPException(status_code=404, detail="Превью не найдено")
    return HTMLResponse(content=html)


@app.get("/api/factory/products/{product_id}/preview/{asset_path:path}")
def preview_factory_product_asset(product_id: str, asset_path: str):
    """Serve sandbox assets for Website Admin live preview (relative HTML/CSS urls)."""
    path = _ctx().factory.resolve_preview_asset(product_id, asset_path)
    if path is None:
        raise HTTPException(status_code=404, detail="asset_not_found")
    media = "application/octet-stream"
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        media = "image/jpeg"
    elif suffix == ".png":
        media = "image/png"
    elif suffix == ".webp":
        media = "image/webp"
    elif suffix == ".gif":
        media = "image/gif"
    elif suffix == ".svg":
        media = "image/svg+xml"
    elif suffix == ".css":
        media = "text/css; charset=utf-8"
        from pathlib import PurePosixPath

        rel_dir = str(PurePosixPath(asset_path).parent)
        if rel_dir == ".":
            rel_dir = ""
        css = path.read_text(encoding="utf-8", errors="replace")
        css = _ctx().factory.rewrite_asset_urls(
            css, product_id=product_id, relative_dir=rel_dir
        )
        return Response(content=css, media_type=media)
    elif suffix == ".js":
        media = "application/javascript"
    return FileResponse(path, media_type=media)


@app.post("/api/factory/products/{product_id}/approve", response_model=FactoryProduct)
def approve_factory_product(product_id: str) -> FactoryProduct:
    try:
        product = _ctx().factory.approve(product_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Продукт не найден") from None
    return FactoryProduct(**product)


@app.post("/api/factory/products/{product_id}/publish", response_model=FactoryProduct)
def publish_factory_product(product_id: str) -> FactoryProduct:
    try:
        product = _ctx().factory.publish(product_id)
    except ValueError as exc:
        if str(exc) == "not_approved":
            raise HTTPException(
                status_code=400,
                detail="Сначала одобрите продукт — «Готов отправить клиенту».",
            ) from None
        raise HTTPException(status_code=404, detail="Продукт не найден") from None
    return FactoryProduct(**product)


@app.get("/api/factory/products/{product_id}/export")
def export_factory_product(product_id: str) -> StreamingResponse:
    try:
        data, filename = _ctx().factory.build_export_zip(product_id)
    except ValueError as exc:
        if str(exc) == "not_approved":
            raise HTTPException(
                status_code=400,
                detail="Сначала одобрите продукт — «Готов отправить клиенту».",
            ) from None
        raise HTTPException(status_code=404, detail="Продукт не найден") from None
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/factory/products/{product_id}/delivered", response_model=FactoryProduct)
def deliver_factory_product(product_id: str) -> FactoryProduct:
    try:
        product = _ctx().factory.mark_delivered(product_id)
    except ValueError as exc:
        if str(exc) == "not_approved":
            raise HTTPException(
                status_code=400,
                detail="Сначала одобрите продукт.",
            ) from None
        if str(exc) == "not_published":
            raise HTTPException(
                status_code=400,
                detail="Сначала опубликуйте продукт — подготовка к передаче.",
            ) from None
        raise HTTPException(status_code=404, detail="Продукт не найден") from None
    try:
        _ctx().sales.mark_delivered_by_product(product_id)
    except Exception:
        logging.getLogger("genesis.factory").exception(
            "sales mark_delivered_by_product failed for %s", product_id
        )
    return FactoryProduct(**product)


@app.post("/api/webhooks/payment", response_model=PaymentRecordedResponse)
def payment_webhook(request: PaymentWebhookRequest) -> PaymentRecordedResponse:
    """Payment Hub callback — provider confirms funds on owner's account."""
    try:
        result = _ctx().finance.record_provider_payment(
            request.amount_eur,
            request.label,
            provider=request.provider,
            product_id=request.product_id,
            sender=request.sender,
        )
    except ValueError as exc:
        if str(exc) == "payment_not_connected":
            raise HTTPException(
                status_code=400,
                detail="Payment Hub не подключён. Подключите Stripe/PayPal в Finance Center.",
            ) from None
        raise HTTPException(status_code=400, detail="Некорректная сумма") from None
    return PaymentRecordedResponse(**result)


@app.post("/api/owner/finance/payments/{payment_id}/confirm", response_model=PaymentRecordedResponse)
def confirm_payment(payment_id: str) -> PaymentRecordedResponse:
    """Owner confirms funds received — only then update balance and history."""
    try:
        result = _ctx().finance.confirm_provider_payment(payment_id)
    except ValueError as exc:
        if str(exc) == "payment_not_found":
            raise HTTPException(status_code=404, detail="Платёж не найден") from None
        raise HTTPException(status_code=400, detail="Платёж уже подтверждён") from None
    return PaymentRecordedResponse(**result)


@app.post("/api/factory/products/{product_id}/improve", response_model=FactoryProduct)
def improve_factory_product(product_id: str, request: FactoryImproveRequest) -> FactoryProduct:
    try:
        product = _ctx().factory.improve(product_id, request.feedback)
    except ValueError:
        raise HTTPException(status_code=404, detail="Продукт не найден") from None
    return FactoryProduct(**product)


@app.post("/api/demo/run", response_model=DemoRunResponse)
def run_demo() -> DemoRunResponse:
    result = _ctx().demo.run_demo(count=5)
    return DemoRunResponse(
        tasks_created=result.tasks_created,
        tasks_completed=result.tasks_completed,
        tasks_failed=result.tasks_failed,
        task_ids=result.task_ids,
        message=(
            f"Demo complete: {result.tasks_completed} completed, "
            f"{result.tasks_failed} failed — check Tasks and Activity"
        ),
    )


@app.post("/api/control/stop", response_model=ControlResponse)
def control_stop() -> ControlResponse:
    return ControlResponse(
        ok=True,
        action="stop",
        message="Stop reserved — emergency halt not implemented in v0.1",
    )


@app.get("/api/cursor/status", response_model=CursorStatusResponse)
def cursor_status() -> CursorStatusResponse:
    return CursorStatusResponse(**_ctx().cursor_handoff.status())


@app.get("/api/cursor/last", response_model=CursorLastHandoffResponse)
def cursor_last_handoff() -> CursorLastHandoffResponse:
    last = _ctx().cursor_handoff.last_handoff()
    if not last:
        return CursorLastHandoffResponse()
    return CursorLastHandoffResponse(
        at=last.get("at"),
        kind=last.get("kind"),
        prompt=last.get("prompt"),
        chars=last.get("chars"),
    )


@app.post("/api/cursor/handoff", response_model=CursorHandoffResponse)
def cursor_handoff(request: CursorHandoffRequest) -> CursorHandoffResponse:
    kind = request.kind if request.kind in ("task", "status", "verify", "apply") else "task"
    if kind == "task":
        result = _ctx().cursor_handoff.submit_task(
            request.task_note,
            auto_open=request.auto_open,
        )
    else:
        result = _ctx().cursor_handoff.build_prompt(kind=kind, task_note=request.task_note)
    return CursorHandoffResponse(**result)


@app.get("/api/cursor/task/active", response_model=CursorTaskResponse)
def cursor_active_task() -> CursorTaskResponse:
    task = _ctx().cursor_handoff.active_task()
    return CursorTaskResponse(task=task)


@app.get("/api/cursor/tasks", response_model=CursorTasksListResponse)
def cursor_tasks_list() -> CursorTasksListResponse:
    tasks = _ctx().cursor_handoff.list_tasks()
    return CursorTasksListResponse(tasks=[CursorTask(**t) for t in tasks])


@app.get("/api/cursor/history", response_model=CursorHandoffHistoryResponse)
def cursor_handoff_history() -> CursorHandoffHistoryResponse:
    items = _ctx().cursor_handoff.handoff_history()
    return CursorHandoffHistoryResponse(items=items)


@app.post("/api/cursor/task/verify", response_model=CursorVerifyResponse)
def cursor_verify_task() -> CursorVerifyResponse:
    result = _ctx().cursor_handoff.verify_task()
    return CursorVerifyResponse(**result)


# --- AI Hub (Development Studio Stage 1) ---


@app.get("/api/ai-hub/providers", response_model=AiProvidersResponse)
def ai_hub_providers() -> AiProvidersResponse:
    from app.integration.ai_hub.provider_registry import default_development_provider, list_providers

    dev = default_development_provider()
    return AiProvidersResponse(
        providers=list_providers(tier="ceo"),
        default_development_provider=dev.id if dev else None,
    )


@app.post("/api/ai-hub/tasks", response_model=AiHubTaskResponse)
def ai_hub_create_task(body: AiHubTaskCreate) -> AiHubTaskResponse:
    task = _ai_hub().create_task(
        body.input_text,
        locale=body.locale or "ru",
        project_id=body.project_id,
        input_type=body.input_type,
    )
    return AiHubTaskResponse(task=AiHubTask(**task))


@app.get("/api/ai-hub/tasks/active", response_model=AiHubTaskResponse)
def ai_hub_active_task() -> AiHubTaskResponse:
    task = _ai_hub().active_task()
    return AiHubTaskResponse(task=AiHubTask(**task) if task else None)


@app.get("/api/ai-hub/tasks", response_model=AiHubTasksListResponse)
def ai_hub_list_tasks() -> AiHubTasksListResponse:
    tasks = _ai_hub().list_tasks()
    return AiHubTasksListResponse(tasks=[AiHubTask(**t) for t in tasks])


@app.get("/api/ai-hub/tasks/{task_id}", response_model=AiHubTaskResponse)
def ai_hub_get_task(task_id: str) -> AiHubTaskResponse:
    task = _ai_hub().get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return AiHubTaskResponse(task=AiHubTask(**task))


@app.post("/api/ai-hub/tasks/{task_id}/approve", response_model=AiHubTaskResponse)
def ai_hub_approve_task(task_id: str, body: AiHubApproveRequest) -> AiHubTaskResponse:
    try:
        task = _ai_hub().approve_task(task_id, auto_open=body.auto_open)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return AiHubTaskResponse(task=AiHubTask(**task))


@app.post("/api/ai-hub/tasks/{task_id}/verify", response_model=AiHubVerifyResponse)
def ai_hub_verify_task(task_id: str) -> AiHubVerifyResponse:
    try:
        result = _ai_hub().verify_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    task = result.get("hub_task")
    return AiHubVerifyResponse(
        ok=result.get("ok", False),
        message=result.get("message", ""),
        hub_task=AiHubTask(**task) if task else None,
    )


@app.post("/api/ai-hub/tasks/{task_id}/cancel", response_model=AiHubTaskResponse)
def ai_hub_cancel_task(task_id: str) -> AiHubTaskResponse:
    try:
        task = _ai_hub().cancel_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return AiHubTaskResponse(task=AiHubTask(**task))


@app.get("/api/dev/workspace", response_model=DevWorkspaceSnapshot)
def dev_workspace_snapshot() -> DevWorkspaceSnapshot:
    snap = _dev_workspace().snapshot()
    return DevWorkspaceSnapshot(**snap)


@app.get("/api/dev/projects", response_model=list[DevProject])
def dev_projects() -> list[DevProject]:
    return [DevProject(**p) for p in _dev_workspace().list_projects()]


@app.get("/api/dev/projects/{project_id}/files", response_model=list[DevFileEntry])
def dev_project_files(project_id: str) -> list[DevFileEntry]:
    return [DevFileEntry(**f) for f in _dev_workspace().list_files(project_id)]


@app.get("/api/dev/projects/{project_id}/docs", response_model=list[DevFileEntry])
def dev_project_docs(project_id: str) -> list[DevFileEntry]:
    return [DevFileEntry(**f) for f in _dev_workspace().list_docs(project_id)]
