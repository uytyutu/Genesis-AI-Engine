from pydantic import BaseModel, Field, model_validator


class SystemStatus(BaseModel):
    name: str
    version: str
    phase: str
    paused: bool
    uptime_sec: float | None = None
    git_commit: str | None = None
    build_time: str | None = None
    process_started: str | None = None
    runtime_identity: str | None = None
    backend_pid: int | None = None
    vector_chat_ready: bool | None = None
    vector_warmup_skipped: bool | None = None


class ModuleStatus(BaseModel):
    id: str
    label: str
    status: str


class ModulesResponse(BaseModel):
    modules: list[ModuleStatus]


class QueueStats(BaseModel):
    pending: int
    running: int
    completed: int
    failed: int


class ActivityEvent(BaseModel):
    at: str
    message: str
    task_id: str | None = None


class ActivityResponse(BaseModel):
    events: list[ActivityEvent]


class ControlResponse(BaseModel):
    ok: bool
    action: str
    message: str


class CreateTaskRequest(BaseModel):
    name: str = Field(min_length=1)
    action: str = "ping"
    input: dict = Field(default_factory=dict)


class TaskItem(BaseModel):
    task_id: str
    name: str
    status: str
    started_at: str
    finished_at: str | None = None
    duration_ms: float | None = None
    result: str
    error: str | None = None
    updated_at: str


class TasksResponse(BaseModel):
    tasks: list[TaskItem]


class TaskCreatedResponse(BaseModel):
    task_id: str
    ok: bool = True


class DemoRunResponse(BaseModel):
    ok: bool = True
    tasks_created: int
    tasks_completed: int
    tasks_failed: int
    task_ids: list[str]
    message: str


class OwnerEvent(BaseModel):
    icon: str
    message: str


class OwnerDashboard(BaseModel):
    owner_name: str
    greeting: str
    system_running: bool
    all_services_ok: bool
    tasks_completed_today: int
    errors_today: int
    uptime_label: str
    last_launch_label: str
    daily_goal: str
    queue_completed: int
    queue_failed: int
    queue_pending: int
    products_count: int
    products_created_today: int
    revenue_today_eur: float
    revenue_month_eur: float
    system_load_percent: int
    recent_events: list[OwnerEvent]
    tip: str
    services_summary: list[str]


class FactoryIntentRequest(BaseModel):
    product_type: str = Field(min_length=1)
    description: str = Field(min_length=3, max_length=2000)
    audience: str | None = Field(default=None, max_length=500)
    goal: str | None = Field(default=None, max_length=500)
    price_eur: float | None = Field(default=None, ge=0)
    deadline: str | None = Field(default=None, max_length=100)
    client_legal: dict | None = Field(
        default=None,
        description="Optional DE Impressum/Datenschutz fields for Factory legal pages",
    )
    package_id: str | None = Field(default=None, pattern="^(basic|business|premium)$")
    contacts: dict | None = Field(
        default=None,
        description="Order contacts for Path A package delivery (phone, whatsapp, city, …)",
    )


class ClientLegalFields(BaseModel):
    """Optional Path A fields for DE Impressum / Datenschutz templates."""

    owner_name: str | None = Field(default=None, max_length=200)
    legal_form: str | None = Field(default=None, max_length=120)
    street: str | None = Field(default=None, max_length=200)
    zip: str | None = Field(default=None, max_length=20)
    city: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default="DE", max_length=8)
    email: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    managing_director: str | None = Field(default=None, max_length=200)
    vat_id: str | None = Field(default=None, max_length=40)
    handelsregister: str | None = Field(default=None, max_length=80)
    register_court: str | None = Field(default=None, max_length=120)
    uses_maps: bool = False
    uses_analytics: bool = False


class FactoryIntentResponse(BaseModel):
    ok: bool = True
    message: str
    intent_id: str
    product_id: str | None = None
    quality_percent: int | None = None
    product: dict | None = None


class HandoffChecklistItem(BaseModel):
    id: str
    label: str
    done: bool


class FactoryProduct(BaseModel):
    product_id: str
    product_type: str
    business_name: str
    description: str
    status: str
    status_label: str
    quality_percent: int
    checks: list[dict[str, str | bool]]
    owner_approved: bool
    owner_approved_at: str | None
    published: bool = False
    published_at: str | None = None
    public_url: str | None = None
    delivered_to_client: bool = False
    delivered_at: str | None = None
    client_message: str = ""
    handoff_checklist: list[HandoffChecklistItem] = []
    revision: int
    niche: str
    template_id: str
    created_at: str
    updated_at: str
    preview_url: str


class FactoryProductsResponse(BaseModel):
    products: list[FactoryProduct]


class FactoryImproveRequest(BaseModel):
    feedback: str = Field(min_length=2, max_length=1000)


class PaymentWebhookRequest(BaseModel):
    amount_eur: float = Field(gt=0)
    label: str = Field(min_length=1, max_length=200)
    provider: str = "stripe"
    product_id: str | None = None
    sender: str | None = None


class PaymentRecordedResponse(BaseModel):
    ok: bool
    amount_eur: float
    recorded_at: str
    provider: str
    pending: bool = False
    payment_id: str | None = None


class PendingPayment(BaseModel):
    payment_id: str
    amount_eur: float
    label: str
    provider: str
    sender: str
    received_at: str


class FactoryIntentItem(BaseModel):
    intent_id: str
    product_type: str
    description: str
    at: str
    status: str


class FactoryIntentsResponse(BaseModel):
    intents: list[FactoryIntentItem]


class SalesPackage(BaseModel):
    id: str
    name: str
    price_eur: float
    deliverables: list[str]
    currency: str | None = None
    symbol: str | None = None
    market_code: str | None = None
    price_label: str | None = None


class SalesPackagesResponse(BaseModel):
    packages: list[SalesPackage]
    currency: str | None = None
    symbol: str | None = None
    market_code: str | None = None


class SalesOrderCreateRequest(BaseModel):
    business_name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=3, max_length=2000)
    city: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    whatsapp: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=120)
    needs_logo: bool = False
    needs_domain: bool = False
    extra_wishes: str | None = Field(default=None, max_length=2000)
    company_website: str | None = Field(
        default=None,
        max_length=400,
        description="Optional existing company site for Path A analysis → Factory brief",
    )
    domain_status: str | None = Field(
        default=None,
        description="none | have_domain | need_help",
    )
    existing_domain: str | None = Field(default=None, max_length=200)
    google_business: str | None = Field(default=None, max_length=400)
    instagram: str | None = Field(default=None, max_length=400)
    facebook: str | None = Field(default=None, max_length=400)
    tiktok: str | None = Field(default=None, max_length=400)
    linkedin: str | None = Field(default=None, max_length=400)
    youtube: str | None = Field(default=None, max_length=400)
    telegram: str | None = Field(default=None, max_length=400)
    material_ids: list[str] = Field(default_factory=list, max_length=40)
    client_legal: ClientLegalFields | None = None
    package_id: str | None = Field(default=None, pattern="^(basic|business|premium)$")
    product_id: str | None = Field(default=None, max_length=80)
    visitor_id: str | None = Field(default=None, max_length=64)
    market_code: str | None = Field(default=None, max_length=8)


class SalesOrderCreatedResponse(BaseModel):
    ok: bool = True
    order_id: str
    message: str
    package_name: str
    price_eur: float
    deliverables: list[str]
    buyer_insights: dict | None = None
    currency: str | None = None
    price_label: str | None = None
    symbol: str | None = None
    market_code: str | None = None


class OrderMaterialUploadResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size: int
    findings: list[dict] = Field(default_factory=list)
    status_de: str


class OrderInsightsPreviewRequest(BaseModel):
    company_website: str | None = Field(default=None, max_length=400)
    domain_status: str | None = Field(default=None, max_length=40)
    existing_domain: str | None = Field(default=None, max_length=200)
    google_business: str | None = Field(default=None, max_length=400)
    instagram: str | None = Field(default=None, max_length=400)
    facebook: str | None = Field(default=None, max_length=400)
    tiktok: str | None = Field(default=None, max_length=400)
    linkedin: str | None = Field(default=None, max_length=400)
    youtube: str | None = Field(default=None, max_length=400)
    telegram: str | None = Field(default=None, max_length=400)
    whatsapp: str | None = Field(default=None, max_length=40)
    material_ids: list[str] = Field(default_factory=list, max_length=40)


class OrderInsightsPreviewResponse(BaseModel):
    ok: bool = True
    checks: list[dict] = Field(default_factory=list)
    note_de: str = ""
    site_analysis: dict | None = None


class SalesOrderSummary(BaseModel):
    order_id: str
    status: str
    status_label: str
    business_name: str
    city: str = ""
    phone: str = ""
    whatsapp: str = ""
    package_name: str
    price_eur: float
    created_at: str
    product_id: str | None = None
    proposal_text: str = ""
    paid: bool = False
    paid_at: str | None = None
    estimated_delivery_at: str | None = None


class OrderTimelineStep(BaseModel):
    id: str
    label: str
    done: bool


class SalesOrderPublicStatus(BaseModel):
    order_id: str
    business_name: str
    package_name: str
    price_eur: float
    price_label: str | None = None
    currency: str | None = None
    symbol: str | None = None
    market_code: str | None = None
    ui_lang: str | None = None
    status: str
    status_label: str
    current_step: str
    next_step: str = ""
    timeline: list[OrderTimelineStep] = []
    estimated_delivery_at: str | None = None
    estimated_hours: int | None = None
    client_message: str = ""
    client_receipt_text: str = ""
    product_id: str | None = None
    paid: bool = False
    download_ready: bool = False
    download_url: str | None = None
    service_id: str | None = None
    launch_mode: bool = False
    review_eligible: bool = False
    review_submitted: bool = False
    review_url: str | None = None


class ClientReviewSubmitRequest(BaseModel):
    token: str = Field(min_length=8, max_length=128)
    stars: int = Field(ge=1, le=5)
    text: str = Field(min_length=20, max_length=1000)
    show_company_name: bool = True
    show_logo: bool = False
    company_display_name: str | None = Field(default=None, max_length=200)


class ClientReviewSubmitResponse(BaseModel):
    ok: bool = True
    review_id: str
    status: str
    flags: list[str] = []
    message_ru: str = ""
    message_de: str = ""


class ClientReviewPublicCard(BaseModel):
    review_id: str | None = None
    stars: int
    text: str
    company_display_name: str | None = None
    show_logo: bool = False
    logo_url: str | None = None
    verified_purchase: bool = True
    published_at: str | None = None


class ClientReviewsPublicResponse(BaseModel):
    has_reviews: bool
    count: int = 0
    average_stars: float | None = None
    recommend_pct: int | None = None
    empty_message: str | None = None
    reviews: list[ClientReviewPublicCard] = []


class ClientReviewModerateRequest(BaseModel):
    action: str = Field(pattern="^(publish|reject)$")
    note: str = Field(default="", max_length=500)


class ClientReviewModerationItem(BaseModel):
    review_id: str
    order_id: str
    stars: int
    text: str
    status: str
    flags: list[str] = []
    company_display_name: str | None = None
    created_at: str | None = None
    show_company_name: bool = True
    show_logo: bool = False
    verified_purchase: bool = True


class ClientReviewsPendingResponse(BaseModel):
    pending: list[ClientReviewModerationItem] = []
    count: int = 0


class SalesCheckoutRequest(BaseModel):
    success_url: str = Field(min_length=8, max_length=500)
    cancel_url: str = Field(min_length=8, max_length=500)


class SalesCheckoutResponse(BaseModel):
    ok: bool = True
    order_id: str
    checkout_url: str
    provider: str
    sandbox: bool = False
    session_id: str | None = None


class PaymentStatusResponse(BaseModel):
    configured: bool
    provider: str | None = None
    provider_label: str
    sandbox: bool = False
    live_mode: bool = False
    webhook_configured: bool = False


class EmailStatusResponse(BaseModel):
    configured: bool
    has_api_key: bool
    has_from_address: bool


class PricingEventRequest(BaseModel):
    event: str = Field(min_length=1)
    tier_id: str | None = None
    page: str = "pricing"
    meta: dict = Field(default_factory=dict)


class PricingEventResponse(BaseModel):
    ok: bool = True


class RevenuePaymentResponse(BaseModel):
    ok: bool = True
    order_id: str
    amount_eur: float | None = None
    product_id: str | None = None
    client_message: str = ""
    order: SalesOrderPublicStatus | None = None
    already_processed: bool = False
    receipt_email: dict | None = None


class StripeWebhookResponse(BaseModel):
    status: str
    ok: bool = True
    event_type: str | None = None
    order_id: str | None = None
    amount_eur: float | None = None
    product_id: str | None = None
    client_message: str = ""
    already_processed: bool = False


class OwnerNotification(BaseModel):
    at: str
    title: str
    message: str
    order_id: str | None = None
    read: bool = False


class OwnerNotificationsResponse(BaseModel):
    notifications: list[OwnerNotification]


class SalesOrdersListResponse(BaseModel):
    orders: list[SalesOrderSummary]


class SalesOrderActionResponse(BaseModel):
    ok: bool = True
    message: str
    order: SalesOrderSummary | None = None
    product_id: str | None = None


class TimelineMilestone(BaseModel):
    id: str
    label: str
    status: str
    symbol: str


class TimelineResponse(BaseModel):
    progress_percent: int
    label: str
    milestones: list[TimelineMilestone]
    done_count: int
    active_count: int
    pending_count: int


class AssistantRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    locale: str | None = Field(default=None, max_length=16)


class ConciergeRequest(BaseModel):
    question: str = Field(default="", max_length=2000)
    locale: str | None = Field(default=None, max_length=16)
    ui_locale: str | None = Field(default=None, max_length=16)
    assistant_locale: str | None = Field(default=None, max_length=16)
    communication_style: str | None = Field(default=None, max_length=24)
    visitor_id: str | None = Field(default=None, max_length=64)
    session_id: str | None = Field(default=None, max_length=64)
    context: dict | None = None
    history: list["ChatTurn"] | None = None
    attachment_ids: list[str] | None = None

    @model_validator(mode="after")
    def require_message_or_files(self) -> "ConciergeRequest":
        if not self.question.strip() and not self.attachment_ids:
            raise ValueError("question or attachment_ids required")
        return self


class ChatAttachmentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size: int
    is_image: bool
    stored_only: bool = True


class TtsRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    speed: float = Field(default=1.1, ge=0.85, le=1.25)
    locale: str = Field(default="ru-RU", max_length=16)


class ChatTurn(BaseModel):
    role: str = Field(pattern=r"^(user|assistant)$")
    content: str = Field(max_length=4000)


class AssistantResponse(BaseModel):
    answer: str
    source: str = "genesis"


class CtaAction(BaseModel):
    href: str
    label: str


class ConciergeResponse(BaseModel):
    answer: str
    source: str = "genesis-ai"
    mode: str = "genesis"
    provider: str | None = None
    cta_href: str | None = None
    cta_label: str | None = None
    cta_actions: list[CtaAction] | None = None
    context: dict | None = None
    debug: dict | None = None
    session_id: str | None = None


class ChatSessionSummary(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str
    preview: str = ""
    pinned: bool = False


class ChatSessionListResponse(BaseModel):
    sessions: list[ChatSessionSummary]


class ChatSessionCreateRequest(BaseModel):
    visitor_id: str = Field(max_length=64)
    title: str = Field(default="Новое поручение", max_length=80)


class ChatSessionCreateResponse(BaseModel):
    session_id: str
    title: str
    created_at: str


class ChatSessionDetailResponse(BaseModel):
    session_id: str
    visitor_id: str
    title: str
    created_at: str
    updated_at: str
    pinned: bool = False
    messages: list[ChatTurn] = Field(default_factory=list)


class ChatSessionRenameRequest(BaseModel):
    visitor_id: str = Field(max_length=64)
    title: str = Field(min_length=1, max_length=80)


class ChatSessionPinRequest(BaseModel):
    visitor_id: str = Field(max_length=64)
    pinned: bool = True


class FinanceTransaction(BaseModel):
    at: str
    amount_eur: float
    label: str
    category: str


class PaymentWallet(BaseModel):
    id: str
    label: str
    icon: str
    connected: bool
    balance_label: str | None = None


class PayoutRecord(BaseModel):
    at: str
    amount_eur: float
    provider: str
    status: str
    status_label: str


class LastWithdrawal(BaseModel):
    at: str
    amount_eur: float
    provider: str
    status_label: str


class SettlementRecord(BaseModel):
    settlement_id: str | None = None
    payment_id: str | None = None
    amount_eur: float
    provider: str | None = None
    label: str | None = None
    paid_at: str | None = None
    available_at: str | None = None
    settlement_status: str | None = None
    settlement_status_ru: str | None = None


class FinancialView(BaseModel):
    system_mode: str = "sandbox"
    funds_held_by_genesis_eur: float = 0.0
    money_never_stored: bool = True
    money_route: str = ""
    custody_note: str = ""
    gross_synced_eur: float = 0.0
    paid_by_client_eur: float = 0.0
    pending_settlement_eur: float = 0.0
    available_for_withdrawal_eur: float = 0.0
    commission_eur: float = 0.0
    net_after_fees_eur: float = 0.0
    tax_reserve_eur: float = 0.0
    net_clean_eur: float = 0.0
    safe_to_withdraw_eur: float = 0.0
    safe_to_withdraw_status: str = "sandbox"
    safe_to_withdraw_label: str = ""
    pending_at_provider_eur: float = 0.0
    potential_revenue_eur: float = 0.0
    potential_revenue: dict = {}
    reconcile_enabled: bool = False
    withdraw_enabled: bool = False
    last_reconcile_at: str | None = None
    disclaimer: str = ""


class FinanceCenter(BaseModel):
    owner_name: str
    greeting: str
    demo_mode: bool = False
    payment_provider: str | None
    payment_provider_label: str
    payment_connected: bool
    last_sync_at: str | None
    data_source_note: str
    currency: str
    platform_balance_eur: float
    paid_by_client_eur: float = 0.0
    pending_settlement_eur: float = 0.0
    revenue_today_eur: float
    revenue_month_eur: float
    gross_revenue_eur: float
    expenses_eur: float
    net_profit_eur: float
    available_for_withdrawal_eur: float
    pending_payouts_eur: float
    products_sold: int
    clients: int
    active_subscriptions: int
    recent_transactions: list[FinanceTransaction]
    withdrawal_enabled: bool
    wallets: list[PaymentWallet] = []
    payout_history: list[PayoutRecord] = []
    last_withdrawal: LastWithdrawal | None = None
    revenue_sparkline: list[float] = []
    pending_payments: list[PendingPayment] = []
    settlements: list[SettlementRecord] = []
    settlement_note_ru: str = ""
    global_revenue: dict = {}
    system_mode: str = "sandbox"
    financial_view: FinancialView | dict = {}


class DepartmentStatus(BaseModel):
    id: str
    label: str
    status: str


class AiTeamSummary(BaseModel):
    active_count: int
    idle_count: int
    errors_today: int
    active_departments: list[DepartmentStatus]
    idle_departments: list[DepartmentStatus]


class CompanyPulseMetric(BaseModel):
    id: str
    icon: str
    label: str
    count: int
    href: str | None = None


class CompanyPulse(BaseModel):
    metrics: list[CompanyPulseMetric]


class CompanyMorningLine(BaseModel):
    text: str
    highlight: bool = False


class CompanyMorningBrief(BaseModel):
    headline: str
    owner_greeting: str
    lines: list[CompanyMorningLine]
    decisions_needed: int


class CompanyOverview(BaseModel):
    owner_name: str
    greeting: str
    company_name: str
    system_running: bool
    platform_balance_eur: float
    revenue_today_eur: float
    revenue_month_eur: float
    gross_revenue_eur: float
    expenses_eur: float
    net_profit_eur: float
    available_for_withdrawal_eur: float
    pending_payouts_eur: float
    products_created: int
    products_created_today: int
    products_sold: int
    clients: int
    active_subscriptions: int
    rating: float
    client_countries: list[str]
    digital_employees_active: int
    digital_employees_idle: int
    digital_employees_errors: int
    sales_today: int
    conversion_percent: float
    ai_expenses_eur: float
    tasks_completed_today: int
    system_load_percent: int
    payment_connected: bool
    payment_provider_label: str
    data_source_note: str
    ai_team: AiTeamSummary
    pulse: CompanyPulse
    morning_brief: CompanyMorningBrief
    ceo_note: str


class DigitalEmployee(BaseModel):
    id: str
    label: str
    icon: str
    status: str
    status_label: str = "Ожидает"
    message: str = ""


class LiveActivityEvent(BaseModel):
    icon: str
    message: str
    at: str | None = None


class NarrativeEvent(BaseModel):
    department: str
    message: str
    at: str
    icon: str = "•"
    action_label: str | None = None
    action_href: str | None = None
    progress_percent: int | None = None
    delay_ms: int = 0


class CompanyAssets(BaseModel):
    products: int
    clients: int
    revenue_month_eur: float
    ai_employees: int
    published: int


class ValuationFactor(BaseModel):
    label: str
    value_label: str
    active: bool


class NightShiftEvent(BaseModel):
    at: str
    department: str
    message: str
    icon: str = "•"


class CommercialEvent(BaseModel):
    icon: str
    label: str
    detail: str


class MorningSummary(BaseModel):
    headline: str
    owner_greeting: str
    company_status: str
    company_days: int
    hours_worked: int
    tasks_done_today: int
    journey_progress_percent: int
    next_goal_label: str
    products_created_count: int
    products_improved_count: int
    ideas_found_count: int
    decisions_needed_count: int
    overnight_checklist: list[dict[str, str | bool]]
    recommendation_title: str | None = None
    recommendation_reason: str | None = None
    recommendation_href: str | None = None
    mode: str = "pre_revenue"
    revenue_today_eur: float = 0.0
    revenue_week_eur: float = 0.0
    payments_confirmed: int = 0
    pending_withdrawal_eur: float = 0.0
    company_value_eur: float = 0.0
    company_value_growth_week_percent: float = 0.0
    valuation_methodology: str = ""
    valuation_is_estimate: bool = False
    valuation_factors: list[ValuationFactor] = []
    assets: CompanyAssets


class IncomeGoal(BaseModel):
    id: str
    label: str
    current_label: str
    remaining_label: str
    progress_percent: float = 0
    done: bool = False
    href: str | None = None


class CompanyReadinessItem(BaseModel):
    id: str
    label: str
    done: bool


class CompanyReadiness(BaseModel):
    percent: int
    completed_count: int
    total_count: int
    items: list[CompanyReadinessItem]
    remaining_labels: list[str]


class CompanyOperations(BaseModel):
    uptime_label: str
    last_downtime_label: str
    all_systems_ok: bool
    systems_status_label: str


class OpportunityQueueItem(BaseModel):
    id: str | None = None
    title: str
    status: str
    source_id: str | None = None
    score: int | None = None


class OpportunitySourceToday(BaseModel):
    source_id: str
    label: str
    enabled: bool
    count_today: int


class OpportunitySnapshot(BaseModel):
    engine_active: bool
    department_label: str
    status_message: str
    found_today: int
    used_today: int
    clients_from_opportunities: int
    revenue_from_opportunities_eur: float
    pending_owner_approval: int
    prepared_count: int
    queue_preview: list[OpportunityQueueItem] = []
    sources_today: list[OpportunitySourceToday] = []
    potential_value_eur: float = 0.0
    kpi_note: str


class OpportunitySource(BaseModel):
    id: str
    label: str
    adapter: str
    enabled: bool
    auto_search: bool


class OpportunityType(BaseModel):
    id: str
    label: str


class OpportunityStatusOption(BaseModel):
    id: str
    label: str


class OpportunityRecord(BaseModel):
    id: str
    opportunity_type: str
    source_id: str
    company_name: str
    contact: str = ""
    fit_reason: str = ""
    score: int = 0
    status: str
    status_label: str
    proposed_message: str = ""
    notes: str = ""
    potential_value_eur: float = 0.0
    revenue_eur: float = 0.0
    found_at: str
    updated_at: str
    website_url: str = ""
    site_analysis: dict | None = None
    recommended_package_id: str = ""
    recommended_price_eur: float = 0.0
    pricing_rationale: str = ""
    email_subject: str = ""
    outreach_status: str = "none"
    interactions: list[dict] = []
    meta: dict = {}


class OpportunityCreateRequest(BaseModel):
    source_id: str = "manual"
    opportunity_type: str = "lead"
    company_name: str
    contact: str = ""
    fit_reason: str = ""
    score: int | None = None
    proposed_message: str = ""
    notes: str = ""
    potential_value_eur: float = 0.0
    website_url: str = ""


class OpportunityUpdateRequest(BaseModel):
    status: str | None = None
    proposed_message: str | None = None
    notes: str | None = None
    contact: str | None = None
    fit_reason: str | None = None
    company_name: str | None = None
    score: int | None = None
    potential_value_eur: float | None = None
    revenue_eur: float | None = None
    website_url: str | None = None


class OpportunitySourcesResponse(BaseModel):
    sources: list[OpportunitySource]
    types: list[OpportunityType]
    statuses: list[OpportunityStatusOption]


class OpportunityListResponse(BaseModel):
    opportunities: list[OpportunityRecord]


class OpportunityDashboard(BaseModel):
    date: str
    total_today: int
    potential_value_eur: float
    sources_today: list[OpportunitySourceToday]
    pipeline_count: int
    won_count: int
    revenue_eur: float
    top_today: list[OpportunityRecord]
    kpi_note: str


class OpportunityCreatedResponse(BaseModel):
    ok: bool
    opportunity: OpportunityRecord
    message: str


class OpportunityUpdatedResponse(BaseModel):
    ok: bool
    opportunity: OpportunityRecord
    message: str


class SiteAnalysisResult(BaseModel):
    url: str
    final_url: str = ""
    status_code: int = 0
    title: str = ""
    load_ms: int = 0
    has_https: bool = False
    has_viewport: bool = False
    issues: list[str] = []
    strengths: list[str] = []
    issue_count: int = 0
    improvement_score: int = 0
    analyzed_at: str = ""
    error: str | None = None


class LeadIntakeRequest(BaseModel):
    niche: str = "generic"
    known: dict[str, str] = {}
    visitor_id: str = ""
    transcript: str = ""


class LeadIntakeResponse(BaseModel):
    hot: bool
    score: int
    gaps: list[str] = []
    follow_up: str | None = None
    lead_id: str | None = None
    message: str = ""
    duplicate: bool = False


class LeadInboxResponse(BaseModel):
    leads: list[OpportunityRecord]
    count: int


class AssetScannerDashboard(BaseModel):
    targets_found: int
    in_work: int
    monetized: int
    my_income_eur: float
    pipeline_potential_eur: float
    security_law: str


class AssetNiche(BaseModel):
    id: str
    label: str
    default_value_eur: float


class AssetNichesResponse(BaseModel):
    niches: list[AssetNiche]


class AssetScanRequest(BaseModel):
    url: str
    niche: str = "local_service"


class AssetScanResponse(BaseModel):
    ok: bool
    target: OpportunityRecord
    message: str


class AssetActionResponse(BaseModel):
    ok: bool
    target: OpportunityRecord
    message: str


class AssetTargetsResponse(BaseModel):
    targets: list[OpportunityRecord]
    count: int


class EngineTarget(BaseModel):
    id: str
    name: str
    url: str = ""
    potential_eur: float = 0.0
    profit_score: int = 0
    traffic_band: str = "trace"
    abandoned: bool = False
    status: str = ""
    status_label: str = ""
    income_rationale: str = ""
    revenue_eur: float = 0.0
    niche: str = "local_service"
    processing_lane: str = ""
    micro_revenue_eur: float = 0.0


class EngineDashboard(BaseModel):
    mode: str
    system_mode: str = "sandbox"
    mode_label: str = ""
    financial_docs_enabled: bool = False
    harvest_balance_label: str = "Баланс добычи"
    potential_revenue: dict = {}
    realized_revenue: dict = {}
    owner_name: str
    security_law: str
    harvest_balance_eur: float
    lifetime_harvest_eur: float
    pipeline_potential_eur: float
    active_assets_count: int
    available_for_withdrawal_eur: float
    pending_payouts_eur: float
    payment_connected: bool
    payment_provider: str | None = None
    payment_provider_label: str = ""
    last_sync_at: str | None = None
    auto_gate_min_score: int
    pending_targets: list[EngineTarget]
    active_assets: list[EngineTarget]
    harvested_assets: list[EngineTarget] = []
    harvested_count: int = 0
    junk_archive_assets: list[EngineTarget] = []
    junk_archive_count: int = 0
    junk_micro_revenue_eur: float = 0.0
    network: dict = {}
    pattern_intel_value_eur: float = 0.0
    pattern_hits_total: int = 0
    hunter: dict = {}
    global_spider: dict = {}
    places_autopilot: dict = {}
    stealth_mode: dict = {}
    ai_brain: dict = {}
    smart_gate: dict = {}
    digital_dust: dict = {}
    finance_gateway: dict = {}
    wallets: list[dict] = []
    withdrawal_enabled: bool = False


class EngineScanModeRequest(BaseModel):
    niche: str = "local_service"
    city: str = "New York"
    limit: int = 8


class EngineScanModeResponse(BaseModel):
    ok: bool
    niche: str
    city: str
    query: str
    scanned: int
    passed_gate: int
    hidden: int
    archived: int = 0
    junk_micro_revenue_eur: float = 0.0
    errors: list[str] = []
    message: str


class EngineJunkArchiveResponse(BaseModel):
    ok: bool
    processed: int
    revenue_eur: float
    message: str


class EngineNetworkScanRequest(BaseModel):
    niche: str = "local_service"
    batch_limit: int = 1000
    region: str = "WORLD"


class EngineNetworkScanResponse(BaseModel):
    ok: bool
    niche: str
    region: str
    batch_limit: int
    scanned: int
    passed_gate: int
    archived: int
    cities_scanned: int = 0
    junk_micro_revenue_eur: float = 0.0
    network: dict = {}
    errors: list[str] = []
    message: str


class EngineGlobalSpiderScanRequest(BaseModel):
    niche: str = "local_service"
    batch_limit: int = 500
    tech_pattern_ids: list[str] = []


class EngineGlobalSpiderScanResponse(BaseModel):
    ok: bool
    mode: str = "global_spider"
    niche: str
    batch_limit: int
    scanned: int
    passed_gate: int
    archived: int
    skipped_tech_filter: int = 0
    regions_scanned: int = 0
    countries_hit: dict = {}
    discovery: dict = {}
    global_spider: dict = {}
    junk_micro_revenue_eur: float = 0.0
    network: dict = {}
    errors: list[str] = []
    message: str


class EngineScanRequest(BaseModel):
    url: str
    niche: str = "local_service"
    manual: bool = True


class EngineScanResponse(BaseModel):
    ok: bool
    profit_score: int
    shown_to_owner: bool
    message: str
    target: OpportunityRecord


class ConnectWalletRequest(BaseModel):
    wallet_id: str
    account_label: str


class WithdrawRequest(BaseModel):
    amount_eur: float
    wallet_id: str


class WithdrawResponse(BaseModel):
    ok: bool
    amount_eur: float
    wallet_id: str
    status: str
    sync: str
    message: str


class PaymentSyncResponse(BaseModel):
    provider: str | None = None
    configured: bool
    live_mode: bool = False
    synced_at: str
    stripe_available_eur: float | None = None
    stripe_error: str | None = None


class EngineTaxSettings(BaseModel):
    vat_rate_percent: float = 19.0
    stripe_fee_percent: float = 1.4
    stripe_fee_fixed_eur: float = 0.25
    service_label: str = "IT-Analyse und Automatisierung von Internet-Assets"


class EngineHarvestLine(BaseModel):
    date: str = ""
    asset_id: str = ""
    asset_name: str = ""
    asset_url: str = ""
    niche: str = ""
    status: str = ""
    gross_eur: float = 0.0
    commission_eur: float = 0.0
    net_after_fees_eur: float = 0.0
    tax_reserve_eur: float = 0.0
    net_clean_eur: float = 0.0


class EngineAccountingSummary(BaseModel):
    system_mode: str = "sandbox"
    financial_docs_enabled: bool = False
    tax_settings: EngineTaxSettings
    totals: dict[str, float]
    potential_revenue: dict = {}
    harvest_count: int
    harvest_lines: list[EngineHarvestLine]
    dsgvo_note: str = ""
    service_label: str = ""
    operator_ready: bool = False
    operator_trade_name: str = ""
    export_summary: dict = {}
    sandbox_note: str = ""


class EngineActivateBusinessRequest(BaseModel):
    confirmed: bool = False
    phrase: str = ""
    owner_name: str = "CEO"


class EngineFinancialExportSummary(BaseModel):
    entries_count: int
    fiat_gross_eur: float
    crypto_gross_eur: float
    payouts_eur: float
    platform_balance_eur: float
    available_for_withdrawal_eur: float
    format: str
    note: str


class OutreachQuotaHealth(BaseModel):
    """CEO send-capacity snapshot (per market region + domain detail)."""

    daily_cap: int
    hard_max: int = 100
    day: str | None = None
    domain_count: int = 0
    region_count: int = 0
    pool_cap_total: int = 0
    sent_today_total: int = 0
    remaining_today_total: int = 0
    primary_used_today: int = 0
    primary_remaining: int = 0
    global_daily_cap: int | None = None
    min_interval_sec: int | None = None
    regions: list[dict] = []
    domains: list[dict] = []
    phase_note_ru: str = ""
    sniper_note_ru: str = ""


class AcquisitionStudioStatus(BaseModel):
    version: str
    name: str
    auto_search: bool
    auto_send: bool
    outreach_send_enabled: bool
    outreach_send_note: str
    law: str
    pending_approval_count: int
    sent_count: int
    pipeline_count: int
    channels: list[dict] = []
    manual_review_count: int = 0
    auto_draft_max_eur: float = 50.0
    outreach_daily_cap: int | None = None
    outreach_quota: OutreachQuotaHealth | dict | None = None
    markets_dashboard: dict | None = None
    adaptive_outreach: dict | None = None
    outreach_runner: dict | None = None
    pilot_catalog: dict | None = None


class AcquisitionApprovalItem(BaseModel):
    id: str
    company_name: str
    contact: str = ""
    website_url: str = ""
    recommended_price_eur: float = 0.0
    recommended_package_id: str = ""
    email_subject: str = ""
    proposed_message: str = ""
    fit_reason: str = ""
    pricing_rationale: str = ""
    issue_count: int = 0
    score: int = 0
    outreach_status: str | None = None
    price_tier: str | None = None


class AcquisitionApprovalQueueResponse(BaseModel):
    items: list[AcquisitionApprovalItem]


class AcquisitionPrepareRequest(BaseModel):
    website_url: str | None = None


class AcquisitionPrepareResponse(BaseModel):
    ok: bool
    opportunity: OpportunityRecord
    message: str


class AcquisitionGenerateDraftsRequest(BaseModel):
    city: str
    query: str
    limit: int = 10
    language: str = "de"
    throttle_ms: int = 250


class AcquisitionGenerateDraftsResponse(BaseModel):
    ok: bool
    created: int = 0
    drafted: int = 0
    skipped_has_site: int = 0
    message: str = ""


class AcquisitionApproveResponse(BaseModel):
    ok: bool
    opportunity: OpportunityRecord
    message: str
    send_result: dict | None = None


class AcquisitionInteractionRequest(BaseModel):
    event: str
    note: str = ""
    market_lesson: str = ""
    market_reason: str = ""


class AcquisitionEvidenceReport(BaseModel):
    sample_size: int
    contacted: int
    replied: int
    won: int
    lost: int
    reply_rate_pct: float
    by_segment: dict = {}
    by_price_band: dict = {}
    lost_reasons: dict = {}
    reason_counts: list[dict] = []
    market_reason_catalog: list[dict] = []
    learning: dict = {}
    insights: list[str] = []
    recent_lessons: list[dict] = []
    evidence_ready: bool
    note: str
    milestone_ru: str = ""


class AcquisitionDailyWorklist(BaseModel):
    date: str
    mode: str
    note: str
    target_per_day: int
    segments: list[dict] = []
    sources_disabled: list[str] = []
    target_city: str | None = None
    search_radius: int | None = None
    profitable_niches: list[str] = []
    target_per_day_note_ru: str | None = None
    outreach_daily_cap: int | None = None
    outreach_quota: OutreachQuotaHealth | dict | None = None


class AcquisitionCatalogResponse(BaseModel):
    principle: str
    services: list[dict]


class MissionSuggestion(BaseModel):
    id: str
    label: str
    href: str


class MissionDecision(BaseModel):
    id: str
    label: str
    href: str


class FirstCustomerStep(BaseModel):
    id: str
    label: str
    done: bool


class FirstCustomerJourney(BaseModel):
    title: str
    subtitle: str
    steps: list[FirstCustomerStep]
    completed_count: int
    total_count: int


class FirstRevenueJourney(BaseModel):
    title: str
    subtitle: str
    steps: list[FirstCustomerStep]
    completed_count: int
    total_count: int


class CursorHandoffRequest(BaseModel):
    kind: str = "task"
    task_note: str | None = Field(default=None, max_length=4000)
    auto_open: bool = True


class CursorTaskStep(BaseModel):
    id: str
    label: str
    done: bool
    active: bool


class CursorTask(BaseModel):
    task_id: str
    state: str
    state_label: str
    progress_percent: int | None = None
    progress_label: str | None = None
    progress_is_estimated: bool = False
    steps: list[CursorTaskStep]
    cursor_opened: bool = False
    cursor_message: str | None = None
    verify_summary: str | None = None
    task_note: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CursorHandoffResponse(BaseModel):
    ok: bool = True
    kind: str
    prompt: str
    chars: int
    copied_hint: str
    mode: str
    bridge_ready: bool
    label: str
    status_icon: str
    status_label: str
    hint: str
    task: CursorTask | None = None


class CursorStatusResponse(BaseModel):
    mode: str
    bridge_ready: bool
    label: str
    status_icon: str
    status_label: str
    hint: str
    cursor_cli_available: bool = False
    active_task_id: str | None = None


class CursorTaskResponse(BaseModel):
    task: CursorTask | None = None


class CursorVerifyResponse(BaseModel):
    ok: bool
    message: str
    verify_summary: str | None = None
    task: CursorTask | None = None


class CursorLastHandoffResponse(BaseModel):
    at: str | None = None
    kind: str | None = None
    prompt: str | None = None
    chars: int | None = None


class CursorHandoffHistoryItem(BaseModel):
    at: str | None = None
    kind: str | None = None
    task_note: str | None = None
    chars: int | None = None


class CursorTasksListResponse(BaseModel):
    tasks: list[CursorTask]


class CursorHandoffHistoryResponse(BaseModel):
    items: list[CursorHandoffHistoryItem]


class CompanyHistory(BaseModel):
    total_revenue_eur: float
    total_clients: int
    total_products: int
    total_ai_tasks: int
    best_month_label: str | None
    best_product_label: str | None


class ProductionDepartment(BaseModel):
    label: str
    status: str
    status_label: str
    product_type: str | None
    product_id: str | None
    preview_url: str | None
    business_name: str | None = None
    checks: list[dict[str, str | bool]] = []
    owner_approved: bool = False
    quality_percent: int = 0


class MissionControl(BaseModel):
    company_name: str
    owner_name: str
    greeting: str
    system_running: bool
    company_days: int
    demo_mode: bool
    company_value_eur: float
    company_value_growth_month_percent: float
    valuation_methodology: str
    valuation_is_estimate: bool
    platform_balance_eur: float
    available_for_withdrawal_eur: float
    revenue_today_eur: float
    revenue_month_eur: float
    net_profit_eur: float
    pending_payouts_eur: float
    ai_expenses_eur: float
    server_expenses_eur: float
    clients: int
    active_subscriptions: int
    products_count: int
    products_created_today: int
    marketplace_status: str
    digital_employees: list[DigitalEmployee]
    production_department: ProductionDepartment
    overnight_events: list[OwnerEvent]
    suggestions: list[MissionSuggestion]
    decisions_needed: list[MissionDecision]
    system_status_label: str
    company_status_headline: str
    live_activity: list[LiveActivityEvent]
    recommendations_today: list[str]
    published_count: int
    payment_connected: bool
    ai_employees_online: int
    active_projects: int
    potential_clients: int
    first_customer_journey: FirstCustomerJourney | None = None
    first_revenue_journey: FirstRevenueJourney | None = None
    morning_summary: MorningSummary
    narrative_feed: list[NarrativeEvent]
    night_shift_feed: list[NightShiftEvent] = []
    commercial_events: list[CommercialEvent] = []
    company_history: CompanyHistory
    data_source_note: str
    payment_provider_label: str
    income_goals: list[IncomeGoal] = []
    company_readiness: CompanyReadiness
    company_operations: CompanyOperations
    opportunity_snapshot: OpportunitySnapshot | None = None


class DemoModeRequest(BaseModel):
    enabled: bool


class DemoModeResponse(BaseModel):
    demo_mode: bool
    message: str


class GrowthCenter(BaseModel):
    demo_mode: bool
    data_source_note: str
    users_total: int
    users_growth_percent: float
    subscriptions_total: int
    subscriptions_growth_percent: float
    revenue_growth_percent: float
    conversion_percent: float
    conversion_growth_percent: float
    cac_eur: float
    cac_change_percent: float
    retention_percent: float
    retention_growth_percent: float


class SystemCheckItem(BaseModel):
    id: str
    label: str
    icon: str
    state: str
    message: str


class SystemCheckResponse(BaseModel):
    ready: bool
    headline: str
    technical_checks: list[SystemCheckItem]
    business_checks: list[SystemCheckItem]
    warnings: list[str]
    demo_mode: bool


class PublicLaunchCheckItem(BaseModel):
    id: str
    label: str
    icon: str
    state: str
    required: bool
    message: str


class PublicLaunchChecklist(BaseModel):
    sprint: str
    kpi: str
    launch_ready: bool
    soft_ready: bool
    public_url: str | None
    payment_provider: str | None
    checks: list[PublicLaunchCheckItem]
    blocking_count: int
    headline: str


# --- AI Hub (Development Studio Stage 1) ---


class AiHubPlanStep(BaseModel):
    id: str
    title: str
    capability: str
    provider_id: str | None = None
    tool_id: str | None = None
    requires_approve: bool = False
    status: str = "pending"


class AiHubTaskCreate(BaseModel):
    input_text: str = Field(min_length=1, max_length=4000)
    locale: str | None = Field(default=None, max_length=16)
    project_id: str | None = Field(default=None, max_length=64)
    input_type: str = Field(default="text", max_length=16)


class AiHubTask(BaseModel):
    id: str
    input_text: str
    input_type: str = "text"
    locale: str = "ru"
    project_id: str
    phase: str
    plan: list[AiHubPlanStep]
    plan_summary: str = ""
    approved_at: str | None = None
    cursor_task_id: str | None = None
    error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    cursor_task: CursorTask | None = None


class AiHubTaskResponse(BaseModel):
    task: AiHubTask | None = None


class AiHubTasksListResponse(BaseModel):
    tasks: list[AiHubTask]


class AiHubApproveRequest(BaseModel):
    auto_open: bool = True


class AiHubVerifyResponse(BaseModel):
    ok: bool
    message: str
    hub_task: AiHubTask | None = None


class DevProject(BaseModel):
    id: str
    name: str
    kind: str
    path_label: str
    available: bool


class DevFileEntry(BaseModel):
    path: str
    name: str
    is_dir: bool = False


class DevBuildEntry(BaseModel):
    at: str | None = None
    task_id: str | None = None
    label: str | None = None
    state: str | None = None
    state_label: str | None = None
    verify_summary: str | None = None


class DevSuggestion(BaseModel):
    id: str
    title: str
    detail: str
    action: str
    task_id: str | None = None
    project_id: str | None = None


class DevWorkspaceSnapshot(BaseModel):
    projects: list[DevProject]
    suggestions: list[DevSuggestion]
    build_history: list[DevBuildEntry]


class AiProviderInfo(BaseModel):
    id: str
    kind: str
    capabilities: list[str]
    label: str
    status: str
    min_tier: str


class AiProvidersResponse(BaseModel):
    providers: list[AiProviderInfo]
    default_development_provider: str | None = None


class WorkforceEmployeeStatus(BaseModel):
    id: str
    label: str
    status: str
    premium: bool = False
    core: bool = False
    tier: str | None = None
    roles: list[str] = []
    quota_remaining: int = 0
    quota_limit: int = 0


class GenesisAISetupStatus(BaseModel):
    genesis_ready: bool = True
    workforce_tier: str
    cloud_employees_ready: int = 0
    employees: list[WorkforceEmployeeStatus]
    llm_configured: bool
    intelligence_active: bool = True
    mode: str
    env_file: str
    setup_wizard_available: bool
    allowed_models: list[str]
    connectable: list[str] = []


class GenesisAISetupRequest(BaseModel):
    provider: str = Field(default="groq", max_length=32)
    api_key: str = Field(default="", max_length=256)
    model: str | None = Field(default=None, max_length=64)


class GenesisAISetupResponse(BaseModel):
    ok: bool
    provider: str | None = None
    llm_configured: bool
    workforce_tier: str | None = None
    employees: list[WorkforceEmployeeStatus] | None = None
    mode: str
    model: str | None = None
    message: str
    env_file: str | None = None


class ClientRegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)
    locale: str = Field(default="ru", max_length=8)
    country: str = Field(default="", max_length=64)
    visitor_id: str | None = Field(default=None, max_length=64)


class ClientLoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)


class ClientWelcomeAnswerRequest(BaseModel):
    answer: str = Field(default="", max_length=500)
    skip: bool = False


class ClientMergeVisitorRequest(BaseModel):
    visitor_id: str = Field(min_length=8, max_length=64)


class BusinessHealthKpi(BaseModel):
    current: int
    target: int
    auto: int
    manual: int
    progress_pct: int


class BusinessHealthFunnelWeek(BaseModel):
    companies_found: int
    conversations: int
    proposals: int
    deals: int
    revenue_eur: float
    net_profit_eur: float


class BusinessHealthWeeklyReview(BaseModel):
    period_label_ru: str
    best_seller_ru: str
    worst_seller_ru: str
    top_rejection_ru: str
    top_rejection_count: int
    recommendation_ru: str


class BusinessHealthMorningLine(BaseModel):
    text: str
    highlight: bool = False


class BusinessHealthMorningBrief(BaseModel):
    headline_ru: str
    lines_ru: list[BusinessHealthMorningLine]
    recommendation_ru: str


class BusinessHealthMarketSignal(BaseModel):
    opportunities_total: int
    lost_reasons_logged: int
    pipeline_active: int
    data_honesty_ru: str


class BusinessHealthCeoOutboxItem(BaseModel):
    id: str
    company_name: str | None = None
    contact: str | None = None
    website_url: str | None = None
    recommended_price_eur: float | None = None
    email_subject: str | None = None
    proposed_message: str | None = None
    score: int | None = None


class BusinessHealthCeoOutbox(BaseModel):
    title_ru: str
    pending_count: int
    outreach_send_enabled: bool
    money_path_ru: str
    law_ru: str
    pipeline_steps_ru: list[str] = Field(default_factory=list)
    week_targets_ru: dict[str, str] = Field(default_factory=dict)
    money_accounts_ru: list[str] = Field(default_factory=list)
    items: list[BusinessHealthCeoOutboxItem]


class MoneyMonitorWithdrawAlert(BaseModel):
    active: bool
    level: str
    title_ru: str
    message_ru: str
    ceo_action_ru: str
    threshold_usd: float | None = None


class RealMoneyTier(BaseModel):
    id: str
    icon: str = ""
    label_ru: str
    amount_eur: float
    amount_label_ru: str
    detail_ru: str
    payment_count: int | None = None
    b2b_pipeline_eur: float | None = None
    farm_analytics_eur: float | None = None


class RealMoneyDashboard(BaseModel):
    rule_ru: str
    received: RealMoneyTier
    pending: RealMoneyTier
    forecast: RealMoneyTier
    training: RealMoneyTier
    bindings_needed: list[str] = Field(default_factory=list)
    demo_mode: bool = False
    payment_connected: bool = False


class SalesFunnelStep(BaseModel):
    id: str
    label_ru: str
    count: int | None = None
    amount_eur: float | None = None
    amount_label_ru: str | None = None
    icon: str = ""


class SalesFunnelDashboard(BaseModel):
    title_ru: str
    headline_ru: str
    subtitle_ru: str
    steps: list[SalesFunnelStep]
    training_note_ru: str = ""
    next_action_href: str = "/business"


class Mission2KpiMetric(BaseModel):
    id: str
    label_ru: str
    value: float
    format: str
    display: str | None = None


class Mission2Conversion(BaseModel):
    id: str
    label_ru: str
    from_label_ru: str
    to_label_ru: str
    percent: int
    from_count: int
    to_count: int


class Mission2NextAction(BaseModel):
    title_ru: str
    text_ru: str
    detail_ru: str
    href: str
    priority: str
    action_id: str


class Mission2NavSection(BaseModel):
    href: str
    label_ru: str
    hint_ru: str


class Mission2KpiDashboard(BaseModel):
    title_ru: str
    subtitle_ru: str
    metrics: list[Mission2KpiMetric]
    conversions: list[Mission2Conversion]
    bottleneck_ru: str
    next_action: Mission2NextAction
    nav_sections: list[Mission2NavSection]
    training_eur: float = 0.0
    training_note_ru: str = ""


class MissionProofStep(BaseModel):
    id: str
    label_ru: str
    done: bool
    icon: str = ""


class MissionProofDashboard(BaseModel):
    title_ru: str
    subtitle_ru: str
    progress_pct: int
    progress_label_ru: str
    steps: list[MissionProofStep]
    next_unproven_ru: str


class RevenueEngineEntry(BaseModel):
    id: str
    number: int
    label_ru: str
    subtitle_ru: str
    counts_as_profit: bool
    wallet_ru: str
    promotion_ru: str = ""
    confirmed_eur: float = 0.0
    confirmed_label_ru: str = ""
    available_eur: float = 0.0
    pending_settlement_eur: float = 0.0
    lab_journal_eur: float = 0.0
    lab_journal_label_ru: str = ""


class RevenueEnginesDashboard(BaseModel):
    title_ru: str
    subtitle_ru: str
    engines: list[RevenueEngineEntry]
    experiments: list[dict] = Field(default_factory=list)
    money_route_ru: str
    lab_rule_ru: str
    stripe_operational_note_ru: str = ""
    generated_at: str = ""


class StripeSetupStep(BaseModel):
    id: str
    label_ru: str
    done: bool
    detail_ru: str


class StripeSetupDashboard(BaseModel):
    configured: bool
    live_mode: bool
    test_mode: bool
    webhook_configured: bool
    mode_label_ru: str
    webhook_url: str
    steps: list[StripeSetupStep]
    ceo_path_ru: list[str]
    sync_hint_ru: str


class MoneyMonitorLane(BaseModel):
    id: str
    icon: str = ""
    label_ru: str
    amount_label_ru: str
    status_ru: str
    detail_ru: str


class MoneyMonitorPipelineStep(BaseModel):
    step: int
    id: str = ""
    title_ru: str
    detail_ru: str


class MoneyMonitorDashboard(BaseModel):
    title_ru: str
    subtitle_ru: str
    real_money: RealMoneyDashboard | None = None
    sales_funnel: SalesFunnelDashboard | None = None
    mission2_kpi: Mission2KpiDashboard | None = None
    lanes: list[MoneyMonitorLane]
    withdraw_alert: MoneyMonitorWithdrawAlert
    pipeline: list[MoneyMonitorPipelineStep] = Field(default_factory=list)
    model_proven: bool
    model_verdict_ru: str
    toloka_role_ru: str = ""


class BusinessHealthDashboard(BaseModel):
    mission: str
    date: str
    week_start: str
    kpi_note_ru: str
    kpis: dict[str, BusinessHealthKpi]
    kpi_labels_ru: dict[str, str]
    funnel_week: BusinessHealthFunnelWeek
    funnel_steps_ru: list[str]
    weekly_review: BusinessHealthWeeklyReview
    morning_brief: BusinessHealthMorningBrief
    market_signal: BusinessHealthMarketSignal
    links: dict[str, str]
    ceo_outbox: BusinessHealthCeoOutbox | None = None
    money_monitor: MoneyMonitorDashboard | None = None
    mission2_kpi: Mission2KpiDashboard | None = None
    mission_proof: MissionProofDashboard | None = None
    revenue_engines: RevenueEnginesDashboard | None = None


class BusinessHealthManualBumpRequest(BaseModel):
    field: str = Field(pattern="^(conversations|proposals|payments|repeats)$")
    delta: int = Field(default=1, ge=-10, le=10)
