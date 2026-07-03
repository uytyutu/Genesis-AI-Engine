from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import io
import os

from fastapi.responses import HTMLResponse, StreamingResponse
from contextlib import asynccontextmanager

from app.integration.context import get_integration, reset_integration
from app.integration.runtime import light_system_status, mark_server_started, set_brain_paused
from app.integration.assistant_service import AssistantService
from app.schemas import (
    ActivityResponse,
    AssistantRequest,
    AssistantResponse,
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
    PaymentStatusResponse,
    SalesOrderActionResponse,
    SalesOrderCreateRequest,
    SalesOrderCreatedResponse,
    SalesOrdersListResponse,
    SalesPackage,
    SalesPackagesResponse,
    CompanyOverview,
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
    TimelineResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    mark_server_started()

    def _warm_integration() -> None:
        try:
            ctx = get_integration()
            set_brain_paused(ctx.adapter.is_paused)
        except Exception:
            pass

    import threading

    threading.Thread(target=_warm_integration, daemon=True, name="genesis-warm").start()
    yield


app = FastAPI(
    title="Genesis Command Center API",
    description="Integration Layer v0.1 — live Brain data",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip()
        for o in os.getenv("GENESIS_CORS_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ctx():
    return get_integration()


@app.get("/api/status", response_model=SystemStatus)
def get_status() -> SystemStatus:
    return SystemStatus(**light_system_status())


@app.get("/api/owner/dashboard", response_model=OwnerDashboard)
def get_owner_dashboard() -> OwnerDashboard:
    data = _ctx().owner.dashboard()
    return OwnerDashboard(**data)


@app.get("/api/owner/finance", response_model=FinanceCenter)
def get_finance_center() -> FinanceCenter:
    ctx = _ctx()
    dash = ctx.owner.dashboard()
    data = ctx.finance.finance_center(dash["owner_name"], dash["greeting"])
    return FinanceCenter(**data)


@app.get("/api/owner/company", response_model=CompanyOverview)
def get_company_overview() -> CompanyOverview:
    data = _ctx().company.overview()
    return CompanyOverview(**data)


@app.get("/api/owner/system-check", response_model=SystemCheckResponse)
def get_system_check() -> SystemCheckResponse:
    data = _ctx().system_check.run()
    return SystemCheckResponse(**data)


@app.get("/api/owner/public-launch", response_model=PublicLaunchChecklist)
def get_public_launch_checklist() -> PublicLaunchChecklist:
    return PublicLaunchChecklist(**_ctx().public_launch.run())


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


@app.get("/api/owner/mission-control", response_model=MissionControl)
def get_mission_control() -> MissionControl:
    data = _ctx().mission_control.snapshot()
    return MissionControl(**data)


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
    result = svc.ask(request.question)
    return AssistantResponse(**result)


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
def list_sales_packages() -> SalesPackagesResponse:
    items = _ctx().sales.packages()
    return SalesPackagesResponse(packages=[SalesPackage(**p) for p in items])


@app.post("/api/sales/orders", response_model=SalesOrderCreatedResponse)
def create_sales_order(request: SalesOrderCreateRequest) -> SalesOrderCreatedResponse:
    result = _ctx().sales.create_order(request.model_dump())
    return SalesOrderCreatedResponse(**result)


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
        raise HTTPException(status_code=400, detail="Нельзя оплатить этот заказ")
    return SalesCheckoutResponse(**result)


@app.get("/api/sales/orders/{order_id}/status", response_model=SalesOrderPublicStatus)
def sales_order_public_status(order_id: str) -> SalesOrderPublicStatus:
    try:
        data = _ctx().sales.public_status(order_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return SalesOrderPublicStatus(**data)


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


@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request) -> RevenuePaymentResponse:
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        result = _ctx().revenue.handle_stripe_webhook(payload, signature)
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный webhook")
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
