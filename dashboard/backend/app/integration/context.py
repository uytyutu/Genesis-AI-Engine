from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from app.integration.brain_adapter import BrainAdapter
from app.integration.company_service import CompanyService
from app.integration.demo_service import DemoService
from app.factory.factory_service import FactoryService
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.sales_order_service import SalesOrderService
from app.integration.revenue_pipeline_service import RevenuePipelineService
from app.integration.finance_service import FinanceService
from app.integration.growth_service import GrowthService
from app.integration.system_check_service import SystemCheckService
from app.integration.health_service import HealthService
from app.integration.mission_control_service import MissionControlService
from app.integration.module_status_service import ModuleStatusService
from app.integration.owner_dashboard_service import OwnerDashboardService
from app.integration.runtime import get_server_started_at, mark_server_started
from app.integration.task_service import TaskService
from app.integration.opportunity_service import OpportunityService
from app.integration.acquisition_studio_service import AcquisitionStudioService
from app.integration.lead_intake_service import LeadIntakeService
from app.integration.asset_scanner_service import AssetScannerService
from app.integration.monetization_engine_service import MonetizationEngineService
from app.integration.engine_accounting_service import EngineAccountingService
from app.integration.cursor_handoff_service import CursorHandoffService
from app.integration.public_launch_service import PublicLaunchService
from app.integration.pricing_display_service import PricingDisplayService
from app.integration.timeline_service import TimelineService

_MEMORY_DIR = Path(
    os.getenv("GENESIS_MEMORY_DIR", "")
).expanduser() if os.getenv("GENESIS_MEMORY_DIR") else Path(__file__).resolve().parent.parent / "memory"

_SEED_MEMORY = Path(__file__).resolve().parent.parent / "memory"


def _bootstrap_memory(path: Path) -> None:
    """Copy bundled templates into persistent volume on first deploy."""
    if not os.getenv("GENESIS_MEMORY_DIR"):
        return
    path.mkdir(parents=True, exist_ok=True)
    for name in ("public_launch.json", "pricing_display.json"):
        target = path / name
        if target.is_file():
            continue
        seed = _SEED_MEMORY / name
        if seed.is_file():
            target.write_text(seed.read_text(encoding="utf-8"), encoding="utf-8")


@dataclass
class IntegrationContext:
    adapter: BrainAdapter
    health: HealthService
    modules: ModuleStatusService
    tasks: TaskService
    demo: DemoService
    factory_intent: FactoryIntentService
    factory: FactoryService
    sales: SalesOrderService
    revenue: RevenuePipelineService
    notifications: OwnerNotificationService
    owner: OwnerDashboardService
    finance: FinanceService
    growth: GrowthService
    system_check: SystemCheckService
    company: CompanyService
    mission_control: MissionControlService
    timeline: TimelineService
    cursor_handoff: CursorHandoffService
    opportunity: OpportunityService
    acquisition: AcquisitionStudioService
    lead_intake: LeadIntakeService
    asset_scanner: AssetScannerService
    monetization_engine: MonetizationEngineService
    engine_accounting: EngineAccountingService
    public_launch: PublicLaunchService
    pricing_display: PricingDisplayService


_context: IntegrationContext | None = None


def get_integration(memory_dir: Path | None = None) -> IntegrationContext:
    global _context
    if _context is None:
        from app.integration.memory_root import MemoryRoot

        raw = memory_dir or _MEMORY_DIR
        path = MemoryRoot(raw).root
        _bootstrap_memory(path)
        path.mkdir(parents=True, exist_ok=True)
        adapter = BrainAdapter(path)
        health = HealthService(adapter)
        tasks = TaskService(adapter)
        started = get_server_started_at()
        finance = FinanceService(path)
        growth = GrowthService(path, finance)
        factory = FactoryService(path)
        factory_intent = FactoryIntentService(path, factory)
        sales = SalesOrderService(path, factory_intent)
        checkout = PaymentCheckoutService(path)
        notifications = OwnerNotificationService(path)
        revenue = RevenuePipelineService(sales, finance, checkout, notifications)
        owner = OwnerDashboardService(tasks, health, path, started, finance)
        modules = ModuleStatusService(health)
        opportunity = OpportunityService(path)
        acquisition = AcquisitionStudioService(opportunity, sales)
        lead_intake = LeadIntakeService(opportunity, notifications)
        asset_scanner = AssetScannerService(opportunity)
        monetization_engine = MonetizationEngineService(
            opportunity, finance, checkout, asset_scanner, path
        )
        engine_accounting = EngineAccountingService(opportunity, path)
        company = CompanyService(
            owner, finance, modules, tasks, health, opportunity, sales, factory, notifications
        )
        system_check = SystemCheckService(health, modules, tasks, owner, finance, path)
        cursor_handoff = CursorHandoffService(path, system_check, factory, finance)
        public_launch = PublicLaunchService(path, checkout)
        pricing_display = PricingDisplayService(path)
        _context = IntegrationContext(
            adapter=adapter,
            health=health,
            modules=modules,
            tasks=tasks,
            demo=DemoService(tasks, adapter),
            factory_intent=factory_intent,
            factory=factory,
            sales=sales,
            revenue=revenue,
            notifications=notifications,
            owner=owner,
            finance=finance,
            growth=growth,
            system_check=system_check,
            company=company,
            mission_control=MissionControlService(
                owner, finance, company, tasks, factory, path, opportunity
            ),
            timeline=TimelineService(),
            cursor_handoff=cursor_handoff,
            opportunity=opportunity,
            acquisition=acquisition,
            lead_intake=lead_intake,
            asset_scanner=asset_scanner,
            monetization_engine=monetization_engine,
            engine_accounting=engine_accounting,
            public_launch=public_launch,
            pricing_display=pricing_display,
        )
    return _context


def reset_integration() -> None:
    """For tests only."""
    global _context
    from app.integration import runtime

    _context = None
    runtime._server_started_at = None
