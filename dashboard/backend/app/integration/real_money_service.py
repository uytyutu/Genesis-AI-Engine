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


def build_real_money_tiers(
    *,
    finance_snapshot: dict[str, Any],
    transactions: list[dict[str, Any]],
    pending_payments: list[dict[str, Any]],
    payout_history: list[dict[str, Any]],
    payment_connected: bool,
    demo_mode: bool,
    farm_training_eur: float,
    opportunities: list[dict[str, Any]] | None = None,
    revenue_forecast: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Four independent tiers — never mix training ledger with received."""
    opps = opportunities or []

    received_eur = 0.0
    received_items: list[dict[str, Any]] = []
    if not demo_mode:
        for row in transactions:
            if not _is_verified_external_transaction(row):
                continue
            amount = round(float(row.get("amount_eur") or 0), 2)
            if amount <= 0:
                continue
            received_eur += amount
            received_items.append(
                {
                    "amount_eur": amount,
                    "provider": str(row.get("provider") or ""),
                    "label": str(row.get("label") or "Поступление"),
                    "at": str(row.get("at") or ""),
                    "payment_id": str(row.get("payment_id") or row.get("external_id") or ""),
                }
            )
        for row in payout_history:
            status = str(row.get("status") or "").lower()
            if status not in {"completed", "confirmed", "received"}:
                continue
            amount = round(float(row.get("amount_eur") or 0), 2)
            if amount <= 0:
                continue
            received_eur += amount
            received_items.append(
                {
                    "amount_eur": amount,
                    "provider": str(row.get("provider") or "bank"),
                    "label": "Выплата на счёт",
                    "at": str(row.get("at") or ""),
                    "payment_id": f"payout-{row.get('at', '')}",
                }
            )
    received_eur = round(received_eur, 2)

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
                    "label": str(row.get("label") or "Ожидает подтверждения"),
                    "payment_id": str(row.get("payment_id") or ""),
                }
            )
        pending_payouts = round(float(finance_snapshot.get("pending_payouts_eur") or 0), 2)
        if pending_payouts > 0 and payment_connected:
            pending_provider_eur = round(pending_provider_eur + pending_payouts, 2)
            pending_items.append(
                {
                    "amount_eur": pending_payouts,
                    "provider": "stripe",
                    "label": "На Stripe — ещё не на банке",
                    "payment_id": "pending-payout",
                }
            )
    pending_eur = round(pending_provider_eur, 2)

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
            "Без связи с внешней транзакцией (Stripe, PayPal, банк) сумма не показывается как «заработано»."
        ),
        "received": {
            "id": "received",
            "icon": "✅",
            "label_ru": "Получено",
            "amount_eur": received_eur,
            "amount_label_ru": _format_eur(received_eur),
            "detail_ru": (
                f"{len(received_items)} подтверждённых поступлений на подключённые счета."
                if received_items
                else "0 € — нет поступлений с внешним подтверждением."
            ),
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
                f"{len(pending_items)} платежей подтверждены провайдером, но ещё не на банке."
                if pending_items
                else "Нет ожидающих выплат с внешним подтверждением."
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
