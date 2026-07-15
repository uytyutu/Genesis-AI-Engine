"""Real money tiers — Получено / Ожидается / Прогноз / Учебный.

Rule: without a link to an external transaction or confirmed provider payment,
Genesis must NOT show a sum as earned (received).
"""

from __future__ import annotations

from typing import Any

_EXTERNAL_PROVIDERS = frozenset({"stripe", "paypal", "bank", "bitcoin", "usdt"})
_SIMULATION_CATEGORIES = frozenset({"training", "simulation", "farm_ledger", "demo"})
_ACTIVE_PIPELINE_STATUSES = frozenset(
    {"new", "qualified", "contacted", "replied", "proposal", "negotiation", "pending_approval"}
)


def _is_verified_external_transaction(row: dict[str, Any]) -> bool:
    provider = str(row.get("provider") or "").lower()
    if provider not in _EXTERNAL_PROVIDERS:
        return False
    category = str(row.get("category") or "sale").lower()
    if category in _SIMULATION_CATEGORIES:
        return False
    if not (row.get("payment_id") or row.get("order_id") or row.get("external_id")):
        return False
    return True


def _format_eur(amount: float) -> str:
    return f"{amount:,.2f} €".replace(",", " ").replace(".", ",")


def get_actual_revenue(
    *,
    finance_snapshot: dict[str, Any],
    settlements: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Real B2B revenue — only finance_settlements.jsonl (Stripe webhook path)."""
    paid = round(float(finance_snapshot.get("paid_by_client_eur") or 0), 2)
    pending = round(float(finance_snapshot.get("pending_settlement_eur") or 0), 2)
    available = round(float(finance_snapshot.get("available_for_withdrawal_eur") or 0), 2)
    settles = settlements or []
    return {
        "paid_by_client_eur": paid,
        "pending_settlement_eur": pending,
        "available_for_withdrawal_eur": available,
        "withdrawable_label_ru": _format_eur(available),
        "paid_by_client_label_ru": _format_eur(paid),
        "pending_settlement_label_ru": _format_eur(pending),
        "source_ru": "finance_settlements.jsonl · webhook Stripe / CEO confirm",
        "payment_count": len(settles),
    }


def get_farm_potential(*, farm_state: dict[str, Any]) -> dict[str, Any]:
    """Farm / exchange ledger — never mixed with Stripe revenue."""
    journal = round(float(farm_state.get("total_earned_eur") or 0), 2)
    today = round(float(farm_state.get("today_earned_eur") or 0), 2)
    tasks = int(farm_state.get("total_tasks_done") or 0)
    return {
        "farm_journal_eur": journal,
        "farm_today_eur": today,
        "total_tasks_done": tasks,
        "label_ru": "Накопления фермы",
        "amount_label_ru": _format_eur(journal),
        "detail_ru": (
            f"{tasks} задач · учебный журнал конвейера. "
            "Не Stripe, не банк — контроль на бирже (Toloka/Scale), не в Genesis."
        ),
    }


def build_real_money_tiers(
    *,
    finance_snapshot: dict[str, Any],
    transactions: list[dict[str, Any]],
    pending_payments: list[dict[str, Any]],
    payout_history: list[dict[str, Any]],
    settlements: list[dict[str, Any]] | None = None,
    payment_connected: bool,
    demo_mode: bool,
    farm_training_eur: float,
    opportunities: list[dict[str, Any]] | None = None,
    revenue_forecast: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Four independent tiers — never mix training ledger with received."""
    opps = opportunities or []
    settles = settlements or []

    paid_by_client_eur = round(float(finance_snapshot.get("paid_by_client_eur") or 0), 2)
    pending_settlement_eur = round(float(finance_snapshot.get("pending_settlement_eur") or 0), 2)
    available_eur = round(float(finance_snapshot.get("available_for_withdrawal_eur") or 0), 2)

    received_items: list[dict[str, Any]] = []
    if not demo_mode:
        for row in settles:
            amount = round(float(row.get("amount_eur") or 0), 2)
            if amount <= 0:
                continue
            received_items.append(
                {
                    "amount_eur": amount,
                    "provider": str(row.get("provider") or ""),
                    "label": str(row.get("label") or "Поступление"),
                    "at": str(row.get("paid_at") or ""),
                    "payment_id": str(row.get("payment_id") or ""),
                    "settlement_status": str(row.get("settlement_status") or ""),
                    "settlement_status_ru": str(row.get("settlement_status_ru") or ""),
                    "available_at": str(row.get("available_at") or ""),
                }
            )
        if not received_items:
            for row in transactions:
                if not _is_verified_external_transaction(row):
                    continue
                amount = round(float(row.get("amount_eur") or 0), 2)
                if amount <= 0:
                    continue
                paid_by_client_eur = max(paid_by_client_eur, amount)
                received_items.append(
                    {
                        "amount_eur": amount,
                        "provider": str(row.get("provider") or ""),
                        "label": str(row.get("label") or "Поступление"),
                        "at": str(row.get("at") or ""),
                        "payment_id": str(row.get("payment_id") or row.get("external_id") or ""),
                        "settlement_status": str(row.get("settlement_status") or "paid_by_client"),
                        "settlement_status_ru": "Оплачено клиентом (webhook)",
                    }
                )
            paid_by_client_eur = round(
                sum(float(i["amount_eur"]) for i in received_items),
                2,
            )

    pending_provider_eur = 0.0
    pending_items: list[dict[str, Any]] = []
    if not demo_mode:
        for row in pending_payments:
            amount = round(float(row.get("amount_eur") or 0), 2)
            if amount <= 0:
                continue
            pending_provider_eur += amount
            pending_items.append(
                {
                    "amount_eur": amount,
                    "provider": str(row.get("provider") or ""),
                    "label": str(row.get("label") or "Ожидает подтверждения CEO"),
                    "payment_id": str(row.get("payment_id") or ""),
                }
            )
        if pending_settlement_eur > 0:
            pending_items.append(
                {
                    "amount_eur": pending_settlement_eur,
                    "provider": "stripe",
                    "label": "Stripe DE — удержание ~3 раб. дня",
                    "payment_id": "settlement-hold",
                }
            )
    pending_eur = round(pending_provider_eur + pending_settlement_eur, 2)

    pipeline_opps = [
        r
        for r in opps
        if str(r.get("status") or "") in _ACTIVE_PIPELINE_STATUSES
        or r.get("outreach_status") in ("pending_approval", "approved", "sent")
    ]
    b2b_forecast_eur = round(
        sum(float(r.get("revenue_eur") or 0) for r in pipeline_opps),
        2,
    )
    farm_forecast_eur = 0.0
    if revenue_forecast:
        day = revenue_forecast.get("labeling_swarm_per_day") or {}
        farm_forecast_eur = round(
            float(day.get("net_eur") or day.get("profit_eur") or day.get("revenue_eur") or 0),
            2,
        )
    forecast_eur = round(max(b2b_forecast_eur, farm_forecast_eur), 2)

    training_eur = round(float(farm_training_eur or 0), 2)

    bindings_needed: list[str] = []
    if not payment_connected:
        bindings_needed.append("Stripe / PayPal / банк — для «Получено»")
    if demo_mode:
        bindings_needed.append("Отключить demo_mode в finance_config")

    return {
        "rule_ru": (
            "«Оплачено клиентом» — только после webhook Stripe. "
            "«Доступно к выводу» — после 3 рабочих дней (DE). Учебный журнал не смешивается."
        ),
        "paid_by_client": {
            "id": "paid_by_client",
            "icon": "💳",
            "label_ru": "Оплачено клиентом",
            "amount_eur": paid_by_client_eur,
            "amount_label_ru": _format_eur(paid_by_client_eur),
            "detail_ru": (
                f"{len(received_items)} платежей с подтверждением Stripe/webhook."
                if received_items
                else "0 € — только после webhook, не после создания счёта."
            ),
            "payment_count": len(received_items),
            "items": received_items[:8],
        },
        "available": {
            "id": "available",
            "icon": "✅",
            "label_ru": "Доступно к выводу",
            "amount_eur": available_eur,
            "amount_label_ru": _format_eur(available_eur),
            "detail_ru": (
                "Settlement пройден — можно нажать «Вывести»."
                if available_eur > 0
                else "Появится через ~3 рабочих дня после оплаты (Stripe DE)."
            ),
        },
        "received": {
            "id": "received",
            "icon": "✅",
            "label_ru": "Доступно к выводу",
            "amount_eur": available_eur,
            "amount_label_ru": _format_eur(available_eur),
            "detail_ru": "Legacy alias — см. paid_by_client и available.",
            "payment_count": len(received_items),
            "items": received_items[:8],
        },
        "pending": {
            "id": "pending",
            "icon": "⏳",
            "label_ru": "Ожидается",
            "amount_eur": pending_eur,
            "amount_label_ru": _format_eur(pending_eur),
            "detail_ru": (
                f"Удержание settlement: {_format_eur(pending_settlement_eur)} · "
                f"ожидает CEO: {_format_eur(pending_provider_eur)}."
                if pending_eur
                else "Нет ожидающих сумм."
            ),
            "payment_count": len(pending_items),
            "items": pending_items[:8],
        },
        "forecast": {
            "id": "forecast",
            "icon": "📈",
            "label_ru": "Прогноз",
            "amount_eur": forecast_eur,
            "amount_label_ru": _format_eur(forecast_eur),
            "detail_ru": (
                f"B2B воронка: {_format_eur(b2b_forecast_eur)} · "
                f"ферма (если все задачи оплатят): {_format_eur(farm_forecast_eur)}. "
                "Только аналитика — не баланс."
            ),
            "b2b_pipeline_eur": b2b_forecast_eur,
            "farm_analytics_eur": farm_forecast_eur,
        },
        "training": {
            "id": "training",
            "icon": "📊",
            "label_ru": "Учебный режим",
            "amount_eur": training_eur,
            "amount_label_ru": _format_eur(training_eur),
            "detail_ru": "Внутренний журнал фермы — симуляция, не выводить и не смешивать с «Получено».",
        },
        "bindings_needed": bindings_needed,
        "demo_mode": demo_mode,
        "payment_connected": payment_connected,
    }
