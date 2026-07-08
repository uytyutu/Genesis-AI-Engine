"""Company overview — CEO-facing business language (Rule #8: company, not engines)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from app.integration.finance_service import FinanceService
from app.integration.health_service import HealthService
from app.integration.module_status_service import ModuleStatusService
from app.integration.owner_dashboard_service import OwnerDashboardService
from app.integration.task_service import TaskService


class CompanyService:
    def __init__(
        self,
        owner: OwnerDashboardService,
        finance: FinanceService,
        modules: ModuleStatusService,
        tasks: TaskService,
        health: HealthService,
        opportunity: object | None = None,
        sales: object | None = None,
        factory: object | None = None,
        notifications: object | None = None,
    ) -> None:
        self._owner = owner
        self._finance = finance
        self._modules = modules
        self._tasks = tasks
        self._health = health
        self._opportunity = opportunity
        self._sales = sales
        self._factory = factory
        self._notifications = notifications

    def _today_iso(self) -> str:
        return date.today().isoformat()

    def _is_today(self, iso: str) -> bool:
        return str(iso)[:10] == self._today_iso()

    def _ai_team(self) -> dict:
        module_list = self._modules.list_modules()
        active = [m for m in module_list if m["status"] in ("online", "degraded")]
        idle = [m for m in module_list if m["status"] == "offline"]
        stats = self._tasks.stats_today()
        return {
            "active_count": len(active),
            "idle_count": len(idle),
            "errors_today": stats["failed_today"],
            "active_departments": [
                {"id": m["id"], "label": self._department_label(m["label"]), "status": m["status"]}
                for m in active
            ],
            "idle_departments": [
                {"id": m["id"], "label": self._department_label(m["label"]), "status": m["status"]}
                for m in idle
            ],
        }

    def _department_label(self, technical: str) -> str:
        mapping = {
            "Kernel": "Операционный отдел",
            "Brain": "Планирование",
            "Queue": "Диспетчеризация",
            "Audit": "Контроль качества",
            "Factory": "Производство",
            "Opportunity": "Поиск возможностей",
            "Revenue": "Финансы",
            "CEO": "Координация",
        }
        return mapping.get(technical, technical)

    def _opportunities(self) -> list[dict]:
        if self._opportunity is None:
            return []
        return self._opportunity.list_opportunities(limit=500)

    def _orders(self) -> list[dict]:
        if self._sales is None:
            return []
        return self._sales.list_orders(200)

    def _products(self) -> list[dict]:
        if self._factory is None:
            return []
        return self._factory.list_products()

    def pulse(self) -> dict:
        opps = self._opportunities()
        orders = self._orders()
        products = self._products()

        new_opportunities = sum(1 for o in opps if o.get("status") in ("new", "reviewed"))
        active_negotiations = sum(
            1 for o in opps if o.get("status") in ("proposed", "contacted", "replied", "qualified")
        )
        awaiting_payment = sum(1 for o in orders if o.get("status") == "awaiting_payment")
        in_production_orders = sum(1 for o in orders if o.get("status") == "in_production")
        in_production_products = sum(
            1
            for p in products
            if p.get("status") in ("completed", "owner_approved", "published")
        )
        in_production = in_production_orders + in_production_products
        completed_orders = sum(1 for o in orders if o.get("status") in ("ready", "delivered"))
        completed_products = sum(1 for p in products if p.get("status") == "delivered")
        completed = completed_orders + completed_products

        paid_names: dict[str, int] = {}
        for order in orders:
            if order.get("paid") or order.get("status") in (
                "paid",
                "in_production",
                "ready",
                "delivered",
            ):
                key = (order.get("business_name") or "").strip().lower()
                if key:
                    paid_names[key] = paid_names.get(key, 0) + 1
        repeat_clients = sum(1 for count in paid_names.values() if count > 1)

        metrics = [
            {
                "id": "new_opportunities",
                "icon": "📥",
                "label": "Новые возможности",
                "count": new_opportunities,
                "href": "/opportunities",
            },
            {
                "id": "active_negotiations",
                "icon": "💬",
                "label": "Активные переговоры",
                "count": active_negotiations,
                "href": "/opportunities",
            },
            {
                "id": "awaiting_payment",
                "icon": "💶",
                "label": "Ожидают оплату",
                "count": awaiting_payment,
                "href": "/",
            },
            {
                "id": "in_production",
                "icon": "🏭",
                "label": "В работе",
                "count": in_production,
                "href": "/projects",
            },
            {
                "id": "completed",
                "icon": "✅",
                "label": "Завершено",
                "count": completed,
                "href": "/projects",
            },
            {
                "id": "repeat_clients",
                "icon": "⭐",
                "label": "Повторные клиенты",
                "count": repeat_clients,
                "href": None,
            },
        ]
        return {"metrics": metrics}

    def morning_brief(self, owner_name: str, greeting: str, fin: dict) -> dict:
        opps = self._opportunities()
        orders = self._orders()
        products = self._products()
        today = self._today_iso()

        opps_today = sum(1 for o in opps if self._is_today(str(o.get("found_at", ""))))
        orders_today = sum(1 for o in orders if self._is_today(str(o.get("created_at", ""))))
        revenue_today = float(fin.get("revenue_today_eur", 0) or 0)
        completed_today = sum(
            1
            for p in products
            if p.get("status") == "delivered" and self._is_today(str(p.get("updated_at", "")))
        )

        pulse = self.pulse()
        decisions = (
            pulse["metrics"][2]["count"]
            + sum(1 for o in opps if o.get("status") == "proposed")
        )

        lines: list[dict] = []
        if opps_today:
            lines.append({"text": f"+{opps_today} новых возможностей", "highlight": True})
        if orders_today:
            lines.append({"text": f"+{orders_today} заявок", "highlight": True})
        if revenue_today > 0:
            lines.append(
                {
                    "text": f"+{revenue_today:.0f} € оплачено",
                    "highlight": True,
                }
            )
        if completed_today:
            lines.append({"text": f"Производство завершило {completed_today} проект(ов)"})
        if decisions > 0:
            lines.append({"text": f"Требуется ваше решение: {decisions}", "highlight": True})

        if not lines:
            lines.append(
                {
                    "text": "Компания готова. Следующий шаг — привлечь первого клиента через /site.",
                    "highlight": False,
                }
            )

        first_name = (owner_name or "владелец").split()[0]
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_greet = "Доброе утро"
        elif 12 <= hour < 18:
            time_greet = "Добрый день"
        else:
            time_greet = "Добрый вечер"

        return {
            "headline": f"{time_greet}, {first_name}.",
            "owner_greeting": greeting,
            "lines": lines,
            "decisions_needed": decisions,
        }

    def overview(self) -> dict:
        dash = self._owner.dashboard()
        fin = self._finance.finance_center(dash["owner_name"], dash["greeting"])
        team = self._ai_team()
        conversion = 0.0
        if fin["clients"] > 0 and fin["products_sold"] > 0:
            conversion = round(min(100.0, fin["products_sold"] / fin["clients"] * 100), 1)

        pulse = self.pulse()
        morning = self.morning_brief(dash["owner_name"], dash["greeting"], fin)

        return {
            "owner_name": dash["owner_name"],
            "greeting": dash["greeting"],
            "company_name": "Virtus Core",
            "system_running": dash["system_running"],
            "platform_balance_eur": fin["platform_balance_eur"],
            "revenue_today_eur": fin["revenue_today_eur"],
            "revenue_month_eur": fin["revenue_month_eur"],
            "gross_revenue_eur": fin["gross_revenue_eur"],
            "expenses_eur": fin["expenses_eur"],
            "net_profit_eur": fin["net_profit_eur"],
            "available_for_withdrawal_eur": fin["available_for_withdrawal_eur"],
            "pending_payouts_eur": fin["pending_payouts_eur"],
            "products_created": dash["products_count"],
            "products_created_today": dash["products_created_today"],
            "products_sold": fin["products_sold"],
            "clients": fin["clients"],
            "active_subscriptions": fin["active_subscriptions"],
            "rating": 0.0,
            "client_countries": [],
            "digital_employees_active": team["active_count"],
            "digital_employees_idle": team["idle_count"],
            "digital_employees_errors": team["errors_today"],
            "sales_today": fin["products_sold"] if fin["revenue_today_eur"] > 0 else 0,
            "conversion_percent": conversion,
            "ai_expenses_eur": fin.get("ai_expenses_eur", 0.0),
            "tasks_completed_today": dash["tasks_completed_today"],
            "system_load_percent": dash["system_load_percent"],
            "payment_connected": fin["payment_connected"],
            "payment_provider_label": fin["payment_provider_label"],
            "data_source_note": fin["data_source_note"],
            "ai_team": team,
            "pulse": pulse,
            "morning_brief": morning,
            "ceo_note": "CEO видит компанию. Технические движки — в разделе «Разработчик».",
        }
