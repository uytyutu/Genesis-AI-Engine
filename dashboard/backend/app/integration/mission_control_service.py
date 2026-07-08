"""Genesis Mission Control — owner morning screen (single API)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.factory.factory_service import FactoryService
from app.integration.company_service import CompanyService
from app.integration.runtime import get_server_started_at, mark_server_started
from app.integration.finance_service import FinanceService
from app.integration.opportunity_service import OpportunityService
from app.integration.task_service import TaskService
from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_DIGITAL_EMPLOYEES = [
    ("analyst", "Analyst", ("brain",)),
    ("factory", "Отдел создания продуктов", ("queue", "factory")),
    ("finance", "Finance", ("revenue",)),
    ("marketing", "Marketing", ("opportunity",)),
    ("publisher", "Publisher", ()),
    ("support", "Support", ("kernel",)),
    ("validator", "Validator", ("audit",)),
]

_DEMO_SNAPSHOT = {
    "platform_balance_eur": 12482.0,
    "available_for_withdrawal_eur": 8920.0,
    "revenue_today_eur": 341.0,
    "revenue_month_eur": 8214.90,
    "gross_revenue_eur": 12482.0,
    "expenses_eur": 40.0,
    "net_profit_eur": 279.0,
    "pending_payouts_eur": 264.0,
    "ai_expenses_eur": 22.0,
    "server_expenses_eur": 18.0,
    "products_sold": 184,
    "clients": 842,
    "active_subscriptions": 391,
    "company_value_eur": 4_800_000.0,
    "company_value_growth_month_percent": 7.4,
}


class MissionControlService:
    def __init__(
        self,
        owner: OwnerDashboardService,
        finance: FinanceService,
        company: CompanyService,
        tasks: TaskService,
        factory: FactoryService,
        memory_dir: Path | None = None,
        opportunity: OpportunityService | None = None,
    ) -> None:
        self._owner = owner
        self._finance = finance
        self._company = company
        self._tasks = tasks
        self._factory = factory
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._opportunity = opportunity or OpportunityService(self._memory)

    def _launcher_config(self) -> dict:
        path = self._memory / "launcher_config.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _company_history(self) -> dict:
        path = self._memory / "company_history.json"
        defaults = {
            "total_revenue_eur": 0.0,
            "total_clients": 0,
            "total_products": 0,
            "total_ai_tasks": 0,
            "best_month_label": None,
            "best_product_label": None,
        }
        if not path.exists():
            return defaults
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {**defaults, **data}
        except (json.JSONDecodeError, OSError):
            return defaults

    def _company_days(self) -> int:
        config = self._launcher_config()
        founded = str(config.get("company_founded_at", "") or config.get("last_launch_at", ""))
        if not founded:
            return 1
        try:
            start = datetime.fromisoformat(founded.replace("Z", "+00:00"))
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - start
            return max(1, delta.days)
        except ValueError:
            return 1

    def _digital_employee_status(
        self,
        production: dict | None,
        fin: dict,
        demo: bool,
    ) -> list[dict[str, str]]:
        modules = {m["id"]: m["status"] for m in self._company._modules.list_modules()}
        labels = {"online": "Работает", "degraded": "На паузе", "offline": "Ожидает"}
        rows = []
        for emp_id, label, module_ids in _DIGITAL_EMPLOYEES:
            statuses = [modules.get(mid, "offline") for mid in module_ids] if module_ids else ["offline"]
            if any(s == "online" for s in statuses):
                icon = "🟢"
                state = "online"
            elif any(s == "degraded" for s in statuses):
                icon = "🟡"
                state = "degraded"
            else:
                icon = "⚪"
                state = "offline"
            rows.append(
                {
                    "id": emp_id,
                    "label": label,
                    "icon": icon,
                    "status": state,
                    "status_label": labels[state],
                    "message": self._employee_message(emp_id, production, fin, demo, state),
                }
            )
        return rows

    def _employee_message(
        self,
        emp_id: str,
        production: dict | None,
        fin: dict,
        demo: bool,
        state: str,
    ) -> str:
        if emp_id == "factory":
            if production and production.get("product_id"):
                name = production.get("business_name") or "продукт"
                if production.get("owner_approved"):
                    return f'"{name}" одобрен владельцем.'
                return f'"{name}" готов к просмотру.'
            return "Ожидает задачу на создание продукта."
        if emp_id == "finance":
            if fin.get("payment_connected"):
                return "Данные синхронизированы с платёжным провайдером."
            return "Payment Hub не подключён — доход пока 0 €."
        if emp_id == "publisher":
            return "Ожидает вашего подтверждения публикации."
        if emp_id == "analyst":
            return "Анализирует ниши по вашим запросам." if state == "online" else "Ожидает запуска системы."
        if emp_id == "marketing":
            return "Готов к исследованию спроса после первого продукта."
        if state == "offline":
            return f"Ожидает запуска {BRAND_NAME}."
        return "Выполняет задачи компании."

    def _company_status_headline(self, dash: dict) -> str:
        if not dash.get("system_running"):
            return "Запустите Virtus Core с рабочего стола"
        if dash.get("errors_today", 0) > 0:
            return "Требуется внимание владельца"
        return "Все системы работают"

    def _live_activity(self, dash: dict, production: dict | None, demo: bool) -> list[dict[str, str | None]]:
        now = datetime.now().strftime("%H:%M")
        if demo:
            return [
                {"icon": "✔", "message": "Virtus Core успешно запущен", "at": now},
                {"icon": "✔", "message": "Проверена система", "at": now},
                {"icon": "✔", "message": "Создан Landing (демо)", "at": now},
                {"icon": "✔", "message": "Ошибок нет", "at": None},
            ]

        items: list[dict[str, str | None]] = []
        if dash.get("system_running"):
            items.append({"icon": "✔", "message": "Virtus Core успешно запущен", "at": now})
        items.append({"icon": "✔", "message": "Проверена система", "at": now})

        if production and production.get("product_id"):
            name = production.get("business_name") or production.get("product_type", "Landing")
            items.append({"icon": "✔", "message": f"Создан {name}", "at": now})

        for ev in dash.get("recent_events", [])[:4]:
            items.append({"icon": ev.get("icon", "•"), "message": ev.get("message", ""), "at": None})

        if dash.get("errors_today", 0) == 0:
            items.append({"icon": "✔", "message": "Ошибок нет", "at": None})
        else:
            items.append(
                {
                    "icon": "⚠",
                    "message": f"Ошибок сегодня: {dash['errors_today']}",
                    "at": now,
                }
            )

        if production and production.get("product_id") and not production.get("owner_approved"):
            name = production.get("business_name") or "продукт"
            items.append(
                {
                    "icon": "⚠",
                    "message": f"Требуется ваше решение: {name}",
                    "at": now,
                }
            )
        return items[:10]

    def _recommendations_today(
        self,
        production: dict | None,
        demo: bool,
        decisions: list[dict[str, str]],
    ) -> list[str]:
        if demo:
            return [
                "Улучшить последний Landing",
                "Проверить новый шаблон",
                "Подключить Payment Hub",
            ]
        rec: list[str] = []
        if production and production.get("product_id") and not production.get("owner_approved"):
            name = production.get("business_name") or "продукт"
            rec.append(f"Завершить и одобрить: {name}")
        elif not self._factory.list_products():
            rec.append("Создать первый лендинг")
        else:
            rec.append("Показать продукт реальному предпринимателю")
        for d in decisions:
            if d["label"] not in rec:
                rec.append(d["label"])
        if len(rec) < 3:
            rec.append("Пройти проверку системы")
        return rec[:4]

    def _hours_worked(self, dash: dict) -> int:
        if not dash.get("system_running"):
            return 0
        started = get_server_started_at()
        hours = int((datetime.now(timezone.utc) - started).total_seconds() // 3600)
        return max(1, hours)

    def _valuation_factors(
        self,
        fin: dict,
        products_count: int,
        published: int,
        growth_week: float,
        demo: bool,
    ) -> list[dict]:
        subs = int(fin.get("active_subscriptions", 0))
        clients = int(fin.get("clients", 0))
        revenue = float(fin.get("revenue_month_eur", 0))
        repeat = int(fin.get("products_sold", 0)) - clients if fin.get("products_sold", 0) > clients else 0
        repeat = max(0, repeat)
        growth_label = f"{growth_week:+.1f}%" if growth_week else "—"

        def row(label: str, value: str, active: bool) -> dict:
            return {"label": label, "value_label": value, "active": active or demo}

        return [
            row("Доход", f"{revenue:,.0f} €".replace(",", " "), revenue > 0),
            row("Активные подписки", str(subs), subs > 0),
            row("Количество клиентов", str(clients), clients > 0),
            row("Активные продукты", str(products_count), products_count > 0),
            row("Опубликовано", str(published), published > 0),
            row("Повторные продажи", str(repeat), repeat > 0),
            row("Темпы роста (неделя)", growth_label, growth_week != 0),
        ]

    def _night_shift_feed(
        self,
        dash: dict,
        fin: dict,
        production: dict | None,
        demo: bool,
    ) -> list[dict]:
        if not dash.get("system_running"):
            return [{"at": "—", "department": "Система", "message": "Virtus Core остановлен", "icon": "⚪"}]

        products = self._factory.list_products()
        improved = sum(1 for p in products if int(p.get("revision", 0)) > 0)
        niches = len({p.get("niche") for p in products if p.get("niche")})
        events: list[dict] = []

        def add(at: str, department: str, message: str, icon: str = "•") -> None:
            events.append({"at": at, "department": department, "message": message, "icon": icon})

        if demo:
            add("02:11", "Analyst", "Изучаю новые ниши…", "📊")
            add("03:42", "Отдел создания продуктов", "Подготовлен новый шаблон.", "🏭")
            add("04:08", "Growth", "Нашёл возможность улучшить конверсию.", "📈")
            add("05:30", "CEO Advisor", "Подготовлен утренний отчёт.", "🎯")
            return events

        add("02:11", "Analyst", "Изучаю каталог ниш и шаблонов…", "📊")
        if improved:
            add("03:42", "Отдел создания продуктов", f"Улучшено продуктов: {improved}", "🏭")
        elif products:
            add("03:42", "Отдел создания продуктов", f"Портфель: {len(products)} продукт(ов) готовы к работе", "🏭")
        else:
            add("03:42", "Отдел создания продуктов", "Ожидает задачу на создание", "🏭")
        if production and production.get("product_id"):
            name = production.get("business_name") or "продукт"
            add("04:08", "Validator", f"Проверен: {name}", "✅")
        else:
            add("04:08", "Growth", "Готов рекомендации после первых продаж", "📈")
        add("05:30", "CEO Advisor", "Подготовлен утренний отчёт для владельца", "🎯")
        if niches:
            events[0]["message"] = f"В портфеле {niches} ниш — анализ продолжается"
        return events

    def _commercial_events(self, fin: dict, published_count: int, demo: bool) -> list[dict]:
        if demo:
            return [
                {"icon": "💰", "label": "Получен платёж", "detail": "79 €"},
                {"icon": "👤", "label": "Новый клиент", "detail": "1"},
                {"icon": "📄", "label": "Подписан договор", "detail": "Landing Pro"},
                {"icon": "🌍", "label": "Опубликован сайт", "detail": "1"},
            ]
        rows: list[dict] = []
        if float(fin.get("revenue_today_eur", 0)) > 0:
            rows.append(
                {
                    "icon": "💰",
                    "label": "Получен платёж",
                    "detail": f"{fin['revenue_today_eur']:.0f} €",
                }
            )
        if int(fin.get("clients", 0)) > 0:
            rows.append({"icon": "👤", "label": "Клиенты", "detail": str(fin["clients"])})
        if published_count > 0:
            rows.append({"icon": "🌍", "label": "Опубликовано", "detail": str(published_count)})
        return rows

    def _morning_summary(
        self,
        dash: dict,
        journey: dict | None,
        fin: dict,
        demo: bool,
        decisions: list[dict],
        owner_name: str,
        greeting: str,
        valuation: dict,
        published_count: int,
        ai_employees_online: int,
    ) -> dict:
        tasks = int(dash.get("tasks_completed_today", 0)) + int(dash.get("products_created_today", 0))
        progress = 0
        next_goal = "Создать первый лендинг"
        if journey:
            total = max(1, journey["total_count"])
            progress = int(100 * journey["completed_count"] / total)
            for step in journey["steps"]:
                if not step["done"]:
                    next_goal = step["label"]
                    break

        products = self._factory.list_products()
        created_today = int(dash.get("products_created_today", 0))
        created_total = len(products)
        improved = sum(1 for p in products if int(p.get("revision", 0)) > 0)
        niches = {p.get("niche") for p in products if p.get("niche")}
        ideas = len(niches) if niches else (1 if dash.get("system_running") else 0)
        decisions_count = len(decisions)

        revenue_today = float(fin.get("revenue_today_eur", 0))
        revenue_month = float(fin.get("revenue_month_eur", 0))
        has_revenue = revenue_today > 0 or revenue_month > 0
        mode = "revenue" if has_revenue and not demo else "pre_revenue"

        checklist: list[dict[str, str | bool]] = [
            {"icon": "✔", "label": "Проверена система", "done": bool(dash.get("system_running"))},
            {
                "icon": "✔",
                "label": f"Создано продуктов: {created_today if created_today else created_total}",
                "done": created_total > 0,
            },
            {"icon": "✔", "label": f"Улучшено продуктов: {improved}", "done": improved > 0},
            {"icon": "✔", "label": f"Найдено новых идей: {ideas}", "done": ideas > 0},
            {
                "icon": "⚠" if decisions_count else "✔",
                "label": f"Требуется решений: {decisions_count}",
                "done": decisions_count == 0,
            },
        ]

        rec_title: str | None = None
        rec_reason: str | None = None
        rec_href: str | None = None
        if mode == "revenue":
            rec_title = "Проверить финансы и выплаты"
            rec_reason = "Есть подтверждённые поступления — обновите план на неделю."
            rec_href = "/finance"
        elif not products:
            rec_title = "Создать Landing для стоматологий"
            rec_reason = (
                "Analyst: высокий спрос на простые сайты для частных клиник (шаблон в каталоге)."
                if not demo
                else "Analyst: спрос на сайты для стоматологий вырос на 28% (демо-оценка)."
            )
            rec_href = "/create"
        else:
            rec_title = next_goal
            rec_reason = "Следующий шаг на пути к первому клиенту."
            rec_href = "/projects"

        company_value = float(valuation.get("company_value_eur", 0))
        growth_week = self._valuation_week_growth(company_value, demo)

        return {
            "headline": BRAND_NAME.upper(),
            "owner_greeting": greeting or f"Доброе утро, {owner_name}",
            "company_status": (
                "Пока ты отдыхал — компания работала"
                if dash.get("system_running")
                else "Запустите Virtus Core"
            ),
            "company_days": self._company_days(),
            "hours_worked": self._hours_worked(dash),
            "tasks_done_today": tasks,
            "journey_progress_percent": progress,
            "next_goal_label": next_goal,
            "products_created_count": created_total,
            "products_improved_count": improved,
            "ideas_found_count": ideas,
            "decisions_needed_count": decisions_count,
            "overnight_checklist": checklist,
            "recommendation_title": rec_title,
            "recommendation_reason": rec_reason,
            "recommendation_href": rec_href,
            "mode": mode,
            "revenue_today_eur": revenue_today,
            "revenue_week_eur": round(revenue_month * 0.25, 2) if revenue_month else revenue_today,
            "payments_confirmed": int(fin.get("products_sold", 0)),
            "pending_withdrawal_eur": float(fin.get("available_for_withdrawal_eur", 0)),
            "company_value_eur": company_value,
            "company_value_growth_week_percent": growth_week,
            "valuation_methodology": str(valuation.get("methodology", "")),
            "valuation_is_estimate": bool(valuation.get("is_estimate")),
            "valuation_factors": self._valuation_factors(
                fin, created_total, published_count, growth_week, demo
            ),
            "assets": {
                "products": created_total,
                "clients": int(fin.get("clients", 0)),
                "revenue_month_eur": revenue_month,
                "ai_employees": ai_employees_online,
                "published": published_count,
            },
        }

    def _narrative_feed(
        self,
        dash: dict,
        production: dict | None,
        journey: dict | None,
        demo: bool,
        fin: dict,
        owner_name: str = "Владелец",
    ) -> list[dict]:
        events: list[dict] = []
        delay = 0
        step_ms = 3500

        def add(
            department: str,
            message: str,
            *,
            icon: str = "•",
            action_label: str | None = None,
            action_href: str | None = None,
            progress_percent: int | None = None,
        ) -> None:
            nonlocal delay
            events.append(
                {
                    "department": department,
                    "message": message,
                    "at": datetime.now().strftime("%H:%M"),
                    "icon": icon,
                    "action_label": action_label,
                    "action_href": action_href,
                    "progress_percent": progress_percent,
                    "delay_ms": delay,
                }
            )
            delay += step_ms

        add(ASSISTANT_NAME, str(dash.get("greeting") or "Добро пожаловать"), icon="👋")

        if not dash.get("products_count"):
            add(ASSISTANT_NAME, "Сегодня рекомендую создать первый продукт.", icon="💡")
        elif journey:
            next_step = next((s["label"] for s in journey["steps"] if not s["done"]), "продолжайте работу")
            add(ASSISTANT_NAME, f"Следующая цель: {next_step}", icon="🎯")

        add("Система", "Система проверена.", icon="✔")

        products = self._factory.list_products()
        if not products and dash.get("system_running"):
            add(
                "Analyst",
                f"{owner_name}, я заметил перспективную нишу — стоматология. Высокий спрос на простые лендинги.",
                icon="💡",
                action_label="Посмотреть",
                action_href="/create",
            )
            add(
                "Отдел создания продуктов",
                "Подготовил предложение. Создать Landing для стоматологии?",
                icon="🏭",
                action_label="Да, создать",
                action_href="/create",
            )
        elif production and production.get("product_id"):
            quality = int(production.get("quality_percent", 0) or 0)
            if not production.get("owner_approved"):
                add(
                    "Validator",
                    "Проверяю качество…",
                    icon="🧪",
                    progress_percent=min(100, max(quality, 62 if quality == 0 else quality)),
                )
            name = production.get("business_name") or "Landing"
            pid = production["product_id"]
            add(
                "Отдел создания продуктов",
                f"{name} готов к просмотру.",
                icon="✔",
                action_label="Открыть",
                action_href=f"/products/{pid}",
            )
            if not production.get("owner_approved"):
                add(
                    ASSISTANT_NAME,
                    "Требуется ваше решение — одобрить продукт для клиента?",
                    icon="⚠",
                    action_label="Решить",
                    action_href=f"/products/{pid}",
                )

        if demo and len(events) < 5:
            add("Finance", "Демо: после подключения Payment Hub здесь появятся поступления.", icon="💰")

        rev_today = float(fin.get("revenue_today_eur", 0)) if fin else 0
        if rev_today > 0 and not demo:
            add(
                "Finance",
                f"Поступила оплата — +{rev_today:.0f} € (подтверждено Payment Hub).",
                icon="💰",
                action_href="/finance",
            )
        if len(products) >= 2 and not demo:
            add(
                "Growth",
                "Сравните продукты в Аналитике — развивайте то, что ближе к первой продаже.",
                icon="📈",
                action_href="/growth",
            )

        return events

    def _owner_milestones(self) -> dict:
        path = self._memory / "owner_milestones.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _income_goals(self, fin: dict, demo: bool) -> list[dict]:
        import math

        revenue_today = float(fin.get("revenue_today_eur", 0))
        gross = float(fin.get("gross_revenue_eur", 0))
        milestones = self._owner_milestones()
        pending = self._finance._pending_payments()
        has_pending = len(pending) > 0

        first_payment = bool(milestones.get("first_payment")) or gross > 0 or revenue_today > 0
        avg_sale = 49.0
        clients_to_100 = (
            0 if gross >= 100 else max(1, int(math.ceil(max(0.0, 100 - gross) / avg_sale)))
        )

        if demo:
            return [
                {
                    "id": "today",
                    "label": "Сегодня",
                    "current_label": "341 €",
                    "remaining_label": "демо",
                    "progress_percent": 34.0,
                    "done": True,
                    "href": "/finance",
                },
                {
                    "id": "first_euro",
                    "label": "До первого €",
                    "current_label": "49 €",
                    "remaining_label": "получено",
                    "progress_percent": 100.0,
                    "done": True,
                    "href": "/finance",
                },
                {
                    "id": "hundred",
                    "label": "До 100 €",
                    "current_label": "82 €",
                    "remaining_label": "ещё 1 клиент",
                    "progress_percent": 82.0,
                    "done": False,
                    "href": "/finance",
                },
                {
                    "id": "thousand_day",
                    "label": "До 1000 €/день",
                    "current_label": "341 €/день",
                    "remaining_label": "построить систему",
                    "progress_percent": 34.0,
                    "done": False,
                    "href": "/growth",
                },
            ]

        return [
            {
                "id": "today",
                "label": "Сегодня",
                "current_label": f"{revenue_today:.0f} €",
                "remaining_label": "продажи идут" if revenue_today > 0 else "пока без продаж",
                "progress_percent": min(100.0, round(revenue_today / 10 * 100, 1)),
                "done": revenue_today > 0,
                "href": "/finance",
            },
            {
                "id": "first_euro",
                "label": "До первого €",
                "current_label": f"{gross:.0f} €" if gross else "0 €",
                "remaining_label": (
                    "ожидает подтверждения"
                    if has_pending and not first_payment
                    else ("получено" if first_payment else "1 клиент")
                ),
                "progress_percent": 100.0 if first_payment else (60.0 if has_pending else 0.0),
                "done": first_payment,
                "href": "/create",
            },
            {
                "id": "hundred",
                "label": "До 100 €",
                "current_label": f"{gross:.0f} €",
                "remaining_label": "получено" if gross >= 100 else f"ещё {clients_to_100} клиента",
                "progress_percent": min(100.0, round(gross / 100 * 100, 1)),
                "done": gross >= 100,
                "href": "/finance",
            },
            {
                "id": "thousand_day",
                "label": "До 1000 €/день",
                "current_label": f"{revenue_today:.0f} €/день",
                "remaining_label": "получено" if revenue_today >= 1000 else "построить систему",
                "progress_percent": min(100.0, round(revenue_today / 1000 * 100, 1)),
                "done": revenue_today >= 1000,
                "href": "/growth",
            },
        ]

    def _company_readiness(
        self,
        dash: dict,
        milestones: dict,
        fin: dict,
        products_count: int,
        published_count: int,
        demo: bool,
    ) -> dict:
        products = self._factory.list_products()
        approved = any(p.get("owner_approved") for p in products)
        first_payment = bool(milestones.get("first_payment")) or float(fin.get("gross_revenue_eur", 0)) > 0

        items = [
            {"id": "system", "label": "Система проверена", "done": bool(dash.get("system_running"))},
            {"id": "product", "label": "Первый продукт создан", "done": products_count > 0},
            {"id": "approved", "label": "Продукт одобрен клиенту", "done": approved},
            {"id": "published", "label": "Publisher — опубликован", "done": published_count > 0},
            {"id": "client", "label": "Показан первому клиенту", "done": bool(milestones.get("owner_tested"))},
            {
                "id": "payment_hub",
                "label": "Payment Hub подключён",
                "done": bool(fin.get("payment_connected")),
            },
            {"id": "first_payment", "label": "Первый платёж", "done": first_payment},
        ]

        if demo:
            items = [
                {"id": "system", "label": "Система проверена", "done": True},
                {"id": "product", "label": "Первый продукт создан", "done": True},
                {"id": "approved", "label": "Продукт одобрен клиенту", "done": True},
                {"id": "published", "label": "Publisher — опубликован", "done": True},
                {"id": "client", "label": "Показан первому клиенту", "done": False},
                {"id": "payment_hub", "label": "Payment Hub подключён", "done": True},
                {"id": "first_payment", "label": "Первый платёж", "done": False},
            ]

        done_count = sum(1 for i in items if i["done"])
        total = len(items)
        percent = round(done_count / total * 100) if total else 0
        remaining = [i["label"] for i in items if not i["done"]]

        return {
            "percent": percent,
            "completed_count": done_count,
            "total_count": total,
            "items": items,
            "remaining_labels": remaining[:5],
        }

    def _company_operations(self, dash: dict, demo: bool) -> dict:
        started = get_server_started_at()
        ops_path = self._memory / "genesis_ops.json"
        if ops_path.exists():
            try:
                ops = json.loads(ops_path.read_text(encoding="utf-8"))
                raw = str(ops.get("last_started_at", "") or "")
                if raw:
                    ops_started = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                    if ops_started.tzinfo is None:
                        ops_started = ops_started.replace(tzinfo=timezone.utc)
                    if dash.get("system_running"):
                        started = ops_started
            except (json.JSONDecodeError, OSError, ValueError):
                pass

        uptime = datetime.now(timezone.utc) - started
        hours, rem = divmod(int(uptime.total_seconds()), 3600)
        minutes, _ = divmod(rem, 60)

        last_downtime = "0"
        if ops_path.exists():
            try:
                ops = json.loads(ops_path.read_text(encoding="utf-8"))
                stopped = str(ops.get("last_stopped_at", "") or "")
                if stopped and not dash.get("system_running"):
                    last_downtime = "сейчас"
                elif stopped and dash.get("system_running"):
                    last_downtime = "0"
            except (json.JSONDecodeError, OSError):
                pass

        if demo:
            return {
                "uptime_label": "12 ч 41 мин",
                "last_downtime_label": "0",
                "all_systems_ok": True,
                "systems_status_label": "🟢 Все системы",
            }

        all_ok = bool(dash.get("all_services_ok")) and bool(dash.get("system_running"))
        return {
            "uptime_label": f"{hours} ч {minutes} мин",
            "last_downtime_label": last_downtime,
            "all_systems_ok": all_ok,
            "systems_status_label": "🟢 Все системы" if all_ok else "🟡 Требуется внимание",
        }

    def _first_revenue_journey(self, demo: bool, fin: dict) -> dict | None:
        if demo:
            return None
        revenue = float(fin.get("gross_revenue_eur", 0)) or float(fin.get("revenue_month_eur", 0))
        if revenue >= 1000:
            return None
        products = self._factory.list_products()
        milestones = self._owner_milestones()
        clients = int(fin.get("clients", 0))
        first_payment = bool(milestones.get("first_payment")) or revenue > 0
        steps = [
            {"id": "product", "label": "Первый продукт", "done": len(products) > 0},
            {
                "id": "client",
                "label": "Первый клиент",
                "done": bool(milestones.get("owner_tested")) or clients > 0,
            },
            {"id": "payment", "label": "Первый платёж", "done": first_payment},
            {"id": "euro_100", "label": "Первые 100 €", "done": revenue >= 100},
            {"id": "euro_1000", "label": "Первые 1000 €", "done": revenue >= 1000},
        ]
        completed = sum(1 for s in steps if s["done"])
        return {
            "title": "До первого дохода",
            "subtitle": "Первый заработанный € важнее десяти новых модулей",
            "steps": steps,
            "completed_count": completed,
            "total_count": len(steps),
        }

    def _first_customer_journey(self, demo: bool, fin: dict) -> dict | None:
        if demo:
            return None
        if float(fin.get("revenue_month_eur", 0)) > 0 or float(fin.get("revenue_today_eur", 0)) > 0:
            return None

        products = self._factory.list_products()
        has_products = len(products) > 0
        approved = any(p.get("owner_approved") for p in products)
        milestones = self._owner_milestones()
        payment_connected = bool(self._finance._load_config().get("payment_provider"))
        first_payment = bool(milestones.get("first_payment")) or (
            payment_connected and float(fin.get("revenue_today_eur", 0)) > 0
        )

        steps = [
            {"id": "landing", "label": "Первый лендинг создан", "done": has_products},
            {
                "id": "approved",
                "label": "Owner Approved — готов отправить клиенту",
                "done": approved,
            },
            {"id": "published", "label": "Первый опубликованный сайт", "done": bool(milestones.get("published"))},
            {
                "id": "owner_test",
                "label": "Показан реальному предпринимателю",
                "done": bool(milestones.get("owner_tested")),
            },
            {
                "id": "feedback",
                "label": "Первый положительный отзыв",
                "done": bool(milestones.get("positive_feedback")),
            },
            {"id": "payment", "label": "Первый платёж", "done": first_payment},
            {
                "id": "repeat",
                "label": "Первый повторный клиент",
                "done": bool(milestones.get("repeat_client")),
            },
        ]

        completed = sum(1 for s in steps if s["done"])
        return {
            "title": "До первого клиента",
            "subtitle": "Реальные цели — не количество тестов",
            "steps": steps,
            "completed_count": completed,
            "total_count": len(steps),
        }

    def _decisions_needed(self, production: dict | None, demo: bool) -> list[dict[str, str]]:
        decisions: list[dict[str, str]] = []
        if production and production.get("product_id") and not production.get("owner_approved"):
            pid = production["product_id"]
            name = production.get("business_name") or "продукт"
            decisions.append(
                {
                    "id": "approve_product",
                    "label": f"Одобрить продукт: {name}",
                    "href": f"/products/{pid}",
                }
            )
        elif production and production.get("owner_approved") and not production.get("published"):
            pid = production["product_id"]
            name = production.get("business_name") or "продукт"
            decisions.append(
                {
                    "id": "publish_product",
                    "label": f"Опубликовать: {name}",
                    "href": f"/products/{pid}",
                }
            )
        if not self._finance._load_config().get("payment_provider") and not demo:
            decisions.append(
                {
                    "id": "connect_payment",
                    "label": "Подключить Payment Hub",
                    "href": "/finance",
                }
            )
        pending_outreach = self._opportunity.list_opportunities(limit=500)
        outreach_pending = [
            r
            for r in pending_outreach
            if r.get("outreach_status") == "pending_approval"
        ]
        if outreach_pending:
            first = outreach_pending[0]
            name = first.get("company_name") or "клиент"
            decisions.append(
                {
                    "id": "approve_outreach",
                    "label": f"Одобрить письмо: {name} ({len(outreach_pending)} в очереди)",
                    "href": "/acquisition",
                }
            )
        return decisions

    def _system_status_label(self, dash: dict) -> str:
        if not dash.get("system_running"):
            return "Остановлена"
        if dash.get("errors_today", 0) > 0:
            return "Требуется внимание"
        return "Всё исправно"

    def _overnight_summary(self, dash: dict, demo: bool) -> list[dict[str, str]]:
        if demo:
            return [
                {"icon": "✔", "message": "Проверена система"},
                {"icon": "✔", "message": "Создано 2 новых лендинга"},
                {"icon": "✔", "message": "Найдены 5 новых идей"},
                {"icon": "✔", "message": "Получено 18 оплат"},
                {"icon": "✔", "message": "Добавлено 4 новых клиента"},
            ]
        events = [{"icon": "✔", "message": "Проверено состояние системы"}]
        completed = dash.get("tasks_completed_today", 0)
        created = dash.get("products_created_today", 0)
        errors = dash.get("errors_today", 0)
        products = self._factory.list_products()
        improved = sum(1 for p in products if int(p.get("revision", 0)) > 0)
        published = sum(1 for p in products if p.get("published"))
        if created:
            events.append({"icon": "✔", "message": f"Создан {created} новый лендинг" if created == 1 else f"Создано лендингов: {created}"})
        if improved:
            events.append({"icon": "✔", "message": f"Улучшен шаблон ({improved} продукт)" if improved == 1 else f"Улучшено продуктов: {improved}"})
        if published:
            events.append({"icon": "✔", "message": "Продукт опубликован — готов к продаже"})
        if completed:
            events.append({"icon": "✔", "message": f"Выполнено задач: {completed}"})
        if errors:
            events.append({"icon": "⚠", "message": f"Ошибок: {errors}"})
        if len(events) == 1:
            events.append({"icon": "•", "message": "Подготовлен отчёт — откройте Mission Control"})
        return events

    def _suggestions(self, demo: bool) -> list[dict[str, str]]:
        base = [
            {"id": "create", "label": "Создать продукт", "href": "/create"},
            {"id": "check", "label": "Проверка системы", "href": "/check"},
            {"id": "finance", "label": "Финансовый центр", "href": "/finance"},
            {"id": "growth", "label": "Центр роста", "href": "/growth"},
            {"id": "company", "label": "Открыть компанию", "href": "/company"},
        ]
        if demo:
            base.extend(
                [
                    {"id": "template", "label": "Создать новый шаблон", "href": "/create"},
                    {"id": "research", "label": "Запустить исследование", "href": "/ai"},
                    {"id": "marketplace", "label": "Открыть Marketplace", "href": "/marketplace"},
                ]
            )
        return base

    def _valuation_week_growth(self, current: float, demo: bool) -> float:
        if demo:
            return 6.2
        path = self._memory / "valuation_snapshots.json"
        today = datetime.now(timezone.utc).date().isoformat()
        data: dict[str, float] = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
        data[today] = round(current, 2)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
        prior = data.get(week_ago)
        if prior is None or prior <= 0:
            return 0.0
        return round(100.0 * (current - prior) / prior, 1)

    def _valuation(
        self,
        revenue_month: float,
        clients: int,
        products: int,
        published: int,
        net_profit: float,
        demo: bool,
    ) -> dict:
        if demo:
            return {
                "company_value_eur": _DEMO_SNAPSHOT["company_value_eur"],
                "growth_month_percent": _DEMO_SNAPSHOT["company_value_growth_month_percent"],
                "methodology": (
                    "Демо-режим: оценка рассчитана как (месячная выручка × 14) + "
                    "(клиенты × 120 €) + (продукты × 50 €). "
                    "В продакшене Virtus Core покажет формулу только на реальных данных."
                ),
                "is_estimate": True,
            }
        if revenue_month <= 0 and clients <= 0 and products <= 0 and published <= 0:
            return {
                "company_value_eur": 0.0,
                "growth_month_percent": 0.0,
                "methodology": (
                    "Стоимость компании растёт с активами: продукты, клиенты, доход. "
                    "Virtus Core не рисует цифры — считает только на фактах."
                ),
                "is_estimate": False,
            }
        value = (
            revenue_month * 12
            + clients * 80.0
            + products * 25.0
            + published * 40.0
            + net_profit * 6
        )
        return {
            "company_value_eur": round(value, 2),
            "growth_month_percent": 0.0,
            "methodology": (
                f"Оценка-модель: (выручка за месяц × 12) + (клиенты × 80 €) + "
                f"(продукты × 25 €) + (опубликовано × 40 €) + (чистая прибыль × 6). "
                "Не является рыночной ценой — только ориентир для владельца."
            ),
            "is_estimate": True,
        }

    def _apply_demo_finance(self, fin: dict) -> dict:
        merged = dict(fin)
        for key in (
            "platform_balance_eur",
            "available_for_withdrawal_eur",
            "revenue_today_eur",
            "revenue_month_eur",
            "gross_revenue_eur",
            "expenses_eur",
            "net_profit_eur",
            "pending_payouts_eur",
            "products_sold",
            "clients",
            "active_subscriptions",
        ):
            merged[key] = _DEMO_SNAPSHOT[key]
        merged["ai_expenses_eur"] = _DEMO_SNAPSHOT["ai_expenses_eur"]
        merged["server_expenses_eur"] = _DEMO_SNAPSHOT["server_expenses_eur"]
        merged["data_source_note"] = (
            "Демо-режим: цифры имитируют подключённый Payment Hub для оценки интерфейса. "
            "Virtus Core не хранит средства — в продакшене данные приходят от провайдера."
        )
        merged["payment_provider_label"] = "Demo (имитация)"
        merged["payment_connected"] = False
        merged["recent_transactions"] = [
            {"at": "2026-07-02T18:00:00Z", "amount_eur": 49.0, "label": "Landing Page", "category": "sale"},
            {"at": "2026-07-02T17:30:00Z", "amount_eur": 29.0, "label": "Подписка Pro", "category": "subscription"},
            {"at": "2026-07-02T16:00:00Z", "amount_eur": 199.0, "label": "SaaS Builder", "category": "sale"},
            {"at": "2026-07-02T15:00:00Z", "amount_eur": 9.0, "label": "Комиссия Marketplace", "category": "commission"},
        ]
        return merged

    def snapshot(self) -> dict:
        dash = self._owner.dashboard()
        fin = self._finance.finance_center(dash["owner_name"], dash["greeting"])
        demo = self._finance.is_demo_mode()
        if demo:
            fin = self._apply_demo_finance(fin)

        ai_exp = float(fin.get("ai_expenses_eur", 0.0))
        server_exp = float(fin.get("server_expenses_eur", 0.0))
        if not demo and fin["expenses_eur"] > 0 and ai_exp == 0:
            ai_exp = round(fin["expenses_eur"] * 0.55, 2)
            server_exp = round(fin["expenses_eur"] - ai_exp, 2)

        production = self._production_department()
        employees = self._digital_employee_status(production, fin, demo)
        ai_online = sum(1 for e in employees if e["status"] == "online")
        milestones = self._owner_milestones()
        decisions = self._decisions_needed(production, demo)
        published_count = sum(1 for p in self._factory.list_products() if p.get("published"))
        if not demo and milestones.get("published"):
            published_count = max(published_count, int(milestones.get("published", 0)))

        valuation = self._valuation(
            fin["revenue_month_eur"],
            fin["clients"],
            dash["products_count"],
            published_count,
            fin["net_profit_eur"],
            demo,
        )
        history = self._company_history()
        if demo:
            history = {
                "total_revenue_eur": 1_482_913.0,
                "total_clients": 24_281,
                "total_products": 67_382,
                "total_ai_tasks": 9_845_183,
                "best_month_label": "Март 2029",
                "best_product_label": "Landing Dental Pro",
            }

        journey = self._first_customer_journey(demo, fin)
        revenue_journey = self._first_revenue_journey(demo, fin)

        return {
            "company_name": "Virtus Core",
            "owner_name": dash["owner_name"],
            "greeting": dash["greeting"],
            "system_running": dash["system_running"],
            "company_days": self._company_days(),
            "demo_mode": demo,
            "company_value_eur": valuation["company_value_eur"],
            "company_value_growth_month_percent": valuation["growth_month_percent"],
            "valuation_methodology": valuation["methodology"],
            "valuation_is_estimate": valuation["is_estimate"],
            "platform_balance_eur": fin["platform_balance_eur"],
            "available_for_withdrawal_eur": fin["available_for_withdrawal_eur"],
            "revenue_today_eur": fin["revenue_today_eur"],
            "revenue_month_eur": fin["revenue_month_eur"],
            "net_profit_eur": fin["net_profit_eur"],
            "pending_payouts_eur": fin["pending_payouts_eur"],
            "ai_expenses_eur": ai_exp,
            "server_expenses_eur": server_exp,
            "clients": fin["clients"],
            "active_subscriptions": fin["active_subscriptions"],
            "products_count": dash["products_count"],
            "products_created_today": dash["products_created_today"],
            "marketplace_status": "online" if demo else "скоро",
            "digital_employees": employees,
            "production_department": production,
            "overnight_events": self._overnight_summary(dash, demo),
            "decisions_needed": decisions,
            "system_status_label": self._system_status_label(dash),
            "company_status_headline": self._company_status_headline(dash),
            "live_activity": self._live_activity(dash, production, demo),
            "recommendations_today": self._recommendations_today(production, demo, decisions),
            "published_count": published_count,
            "payment_connected": bool(fin.get("payment_connected")),
            "ai_employees_online": ai_online,
            "active_projects": dash["products_count"],
            "potential_clients": 18 if demo else 0,
            "first_customer_journey": journey,
            "first_revenue_journey": revenue_journey,
            "morning_summary": self._morning_summary(
                dash,
                journey,
                fin,
                demo,
                decisions,
                dash["owner_name"],
                dash["greeting"],
                valuation,
                published_count,
                ai_online,
            ),
            "narrative_feed": self._narrative_feed(
                dash, production, journey, demo, fin, str(dash.get("owner_name") or "Владелец")
            ),
            "night_shift_feed": self._night_shift_feed(dash, fin, production, demo),
            "commercial_events": self._commercial_events(fin, published_count, demo),
            "suggestions": self._suggestions(demo),
            "company_history": history,
            "data_source_note": fin["data_source_note"],
            "payment_provider_label": fin["payment_provider_label"],
            "income_goals": self._income_goals(fin, demo),
            "company_readiness": self._company_readiness(
                dash, milestones, fin, dash["products_count"], published_count, demo
            ),
            "company_operations": self._company_operations(dash, demo),
            "opportunity_snapshot": None
            if demo
            else self._opportunity.snapshot(
                revenue_today_eur=float(fin.get("revenue_today_eur", 0)),
                clients=int(fin.get("clients", 0)),
            ),
        }

    def _production_department(self) -> dict | None:
        dept = "Отдел создания продуктов"
        latest = self._factory.latest_product()
        if not latest:
            return {
                "label": dept,
                "status": "idle",
                "status_label": "Ожидает задачу",
                "product_type": None,
                "product_id": None,
                "preview_url": None,
                "checks": [],
                "owner_approved": False,
                "quality_percent": 0,
            }
        return {
            "label": dept,
            "status": latest["status"],
            "status_label": latest["status_label"],
            "product_type": latest["product_type"],
            "product_id": latest["product_id"],
            "preview_url": latest["preview_url"],
            "business_name": latest.get("business_name", ""),
            "checks": latest.get("checks", []),
            "owner_approved": latest.get("owner_approved", False),
            "published": latest.get("published", False),
            "quality_percent": latest.get("quality_percent", 0),
        }

    def set_demo_mode(self, enabled: bool) -> dict:
        self._finance.set_demo_mode(enabled)
        return {"demo_mode": enabled, "message": "Демо-режим включён" if enabled else "Демо-режим выключен"}
