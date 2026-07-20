from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import io
import os

from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse
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
    local_owner_access_allowed,
    production_api_allowed,
)
from app.integration.owner_auth import owner_access_allowed
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
    ClientReviewSubmitResponse,
    ClientReviewsPublicResponse,
    ClientReviewModerateRequest,
    ClientReviewModerationItem,
    ClientReviewsPendingResponse,
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
    ClientLoginRequest,
    ClientWelcomeAnswerRequest,
    ClientMergeVisitorRequest,
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

    # Country Desk / market runner: always STOPPED on process start (launcher).
    # CEO starts the market only via Пуск in Mission Control — never resume from disk.
    try:
        from app.integration.outreach_ceo_prefs import save_prefs
        from app.integration.outreach_runner_service import OutreachRunnerService

        save_prefs(memory_dir, auto_refresh=False)
        OutreachRunnerService(memory_dir).stop()
        logging.getLogger("genesis").info(
            "Country Desk market forced STOP on startup (Пуск only)"
        )
    except Exception:
        logging.getLogger("genesis").exception("market force-stop on startup failed")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip()
        for o in os.getenv(
            "GENESIS_CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
        ).split(",")
        if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.webhooks.stripe import router as stripe_webhook_router

app.include_router(stripe_webhook_router)

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
async def rate_limit_public(request: Request, call_next):
    """Basic DoS guard on public chat endpoints (per client IP)."""
    if is_production() and request.url.path.startswith("/api/public/"):
        import time
        from collections import defaultdict

        if not hasattr(app.state, "_rate_buckets"):
            app.state._rate_buckets = defaultdict(list)
        ip = (request.client.host if request.client else "unknown") or "unknown"
        now = time.time()
        window = 60.0
        limit = int(os.getenv("GENESIS_RATE_LIMIT_PER_MIN", "40"))
        bucket: list[float] = app.state._rate_buckets[ip]
        bucket[:] = [t for t in bucket if now - t < window]
        if len(bucket) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests — please wait a moment"},
            )
        bucket.append(now)
    return await call_next(request)


@app.middleware("http")
async def guard_internal_routes(request: Request, call_next):
    path = request.url.path
    method = request.method
    if is_production():
        if not production_api_allowed(path, method):
            return JSONResponse(status_code=403, content=api_access_denied_response(path, method))
    elif is_internal_api_path(path) and not (
        owner_access_allowed(request)
        if is_owner_api_path(path)
        else local_owner_access_allowed(request)
    ):
        return JSONResponse(status_code=403, content=api_access_denied_response(path, method))
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
    return _ctx().micro_farm.run_tick(workers=max(1, min(100, workers)))


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


@app.get("/api/acquisition/status", response_model=AcquisitionStudioStatus)
def acquisition_studio_status() -> AcquisitionStudioStatus:
    return AcquisitionStudioStatus(**_ctx().acquisition.studio_status())


@app.get("/api/acquisition/gate-funnel")
def acquisition_gate_funnel() -> dict:
    return _ctx().acquisition.gate_funnel()


@app.get("/api/acquisition/pipeline")
def acquisition_pipeline(limit: int = 50) -> dict:
    items = _ctx().acquisition.pipeline_leads(limit=max(1, min(100, limit)))
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
        language = str(body.get("language") or "de").strip() or "de"
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
    locale: str = "de",
) -> VisualExperiencePreviewResponse:
    """Adaptive VXP preview for Path A order wizard (still / motion — never empty)."""
    from app.integration.path_a_visual_preview import resolve_path_a_visual_preview

    exp = resolve_path_a_visual_preview(
        niche_id=niche,
        tier=tier,
        specialization=specialization,
        locale=locale,
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

    niches = []
    for nid in known_niche_ids():
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


# --- M2 Universal Identity (client API — human-facing responses, plain language) ---


def _customer_identity():
    from app.integration.customer_identity import CustomerIdentityService

    return CustomerIdentityService(_memory_dir())


@app.post("/api/client/register")
def client_register(body: ClientRegisterRequest) -> dict:
    return _customer_identity().register(
        name=body.name,
        email=body.email,
        password=body.password,
        locale=body.locale,
        country=body.country,
        prior_visitor_id=body.visitor_id,
    )


@app.post("/api/client/login")
def client_login(body: ClientLoginRequest) -> dict:
    return _customer_identity().login(email=body.email, password=body.password)


@app.get("/api/client/me")
def client_me(request: Request) -> dict:
    from app.integration.customer_identity.auth import require_client

    payload = require_client(request)
    return _customer_identity().me(str(payload["sub"]))


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


@app.post("/api/sales/orders", response_model=SalesOrderCreatedResponse)
def create_sales_order(request: SalesOrderCreateRequest) -> SalesOrderCreatedResponse:
    from app.integration.receipt_email_service import ReceiptEmailService

    result = _ctx().sales.create_order(request.model_dump())
    order = _ctx().sales.get_order(result["order_id"])
    if order and order.get("email"):
        ReceiptEmailService().send_order_received(order=order)
    return SalesOrderCreatedResponse(**result)


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

        visual_experience = resolve_path_a_visual_preview(
            niche_id=body.niche,
            tier=body.package_id or "business",
            specialization=body.specialization,
            locale="de",
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


@app.get("/api/owner/reviews/pending", response_model=ClientReviewsPendingResponse)
def owner_reviews_pending() -> ClientReviewsPendingResponse:
    pending = _ctx().reviews.list_pending()
    items = [
        ClientReviewModerationItem(
            review_id=str(r.get("review_id") or ""),
            order_id=str(r.get("order_id") or ""),
            stars=int(r.get("stars") or 0),
            text=str(r.get("text") or ""),
            status=str(r.get("status") or ""),
            flags=list(r.get("flags") or []),
            company_display_name=r.get("company_display_name"),
            created_at=r.get("created_at"),
            show_company_name=bool(r.get("show_company_name")),
            show_logo=bool(r.get("show_logo")),
            verified_purchase=bool(r.get("verified_purchase", True)),
        )
        for r in pending
    ]
    return ClientReviewsPendingResponse(pending=items, count=len(items))


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
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden") from None
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


@app.get("/api/owner/notifications", response_model=OwnerNotificationsResponse)
def owner_notifications() -> OwnerNotificationsResponse:
    items = _ctx().notifications.list_recent()
    return OwnerNotificationsResponse(
        notifications=[OwnerNotification(**n) for n in items]
    )


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
