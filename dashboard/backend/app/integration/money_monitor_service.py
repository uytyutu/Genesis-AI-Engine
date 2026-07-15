"""Money Monitor — три канала денег: учебный ledger · биржа (цех) · B2B (банк)."""

from __future__ import annotations

from typing import Any

from app.integration.real_money_service import (
    build_real_money_tiers,
    get_actual_revenue,
    get_farm_potential,
)
from app.integration.mission2_kpi_service import build_mission2_kpi, build_sales_funnel_progress


def build_money_monitor(
    *,
    farm_state: dict[str, Any],
    payment_monitor: dict[str, Any] | None = None,
    opportunities: list[dict[str, Any]] | None = None,
    outbox_pending: int = 0,
    toloka_submit_count: int = 0,
    finance_inputs: dict[str, Any] | None = None,
    revenue_forecast: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Genesis = приборная панель. Биржа = касса (CEO вручную). B2B = реальный €."""
    pm = payment_monitor or {}
    monitor = pm.get("monitor") or {}
    payout = pm.get("payout") or {}
    opps = opportunities or []

    training_eur = round(float(farm_state.get("total_earned_eur") or 0), 2)
    llm_cost = round(float(farm_state.get("llm_cost_eur") or 0), 2)
    tasks = int(farm_state.get("total_tasks_done") or 0)

    fin = finance_inputs or {}
    actual_revenue = get_actual_revenue(
        finance_snapshot=fin.get("finance_snapshot") or {},
        settlements=fin.get("settlements") or [],
    )
    farm_potential = get_farm_potential(farm_state=farm_state)
    real_money = build_real_money_tiers(
        finance_snapshot=fin.get("finance_snapshot") or {},
        transactions=fin.get("transactions") or [],
        pending_payments=fin.get("pending_payments") or [],
        payout_history=fin.get("payout_history") or [],
        settlements=fin.get("settlements") or [],
        payment_connected=bool(fin.get("payment_connected")),
        demo_mode=bool(fin.get("demo_mode")),
        farm_training_eur=training_eur,
        opportunities=opps,
        revenue_forecast=revenue_forecast,
    )
    paid_by_client_eur = float(actual_revenue["paid_by_client_eur"])
    received_eur = float(actual_revenue["available_for_withdrawal_eur"])
    pending_eur = float(actual_revenue["pending_settlement_eur"])

    pending_proposals = sum(
        1 for r in opps if r.get("outreach_status") == "pending_approval"
    )
    contacted = sum(1 for r in opps if r.get("status") in ("contacted", "replied", "qualified"))

    toloka = monitor.get("toloka") or {}
    scale = monitor.get("scale") or {}
    threshold = float(payout.get("threshold_usd") or 10)

    exchange_balance_usd: float | None = None
    for row in (scale, toloka):
        bal = row.get("balance_usd")
        if bal is not None:
            exchange_balance_usd = float(bal)
            break

    withdraw_ready = bool(payout.get("has_withdraw_ready"))
    alert_message = ""
    if withdraw_ready and payout.get("pending_alerts"):
        alert_message = str(payout["pending_alerts"][0].get("message") or "")

    lanes = [
        {
            "id": "training_ledger",
            "icon": "📊",
            "label_ru": "Журнал фермы (не Stripe)",
            "amount_eur": farm_potential["farm_journal_eur"],
            "amount_label_ru": farm_potential["amount_label_ru"],
            "status": "simulation",
            "status_ru": "Учебный · не выручка CEO",
            "detail_ru": farm_potential["detail_ru"],
        },
        {
            "id": "exchange_factory",
            "icon": "🏭",
            "label_ru": "Биржа — заводской цех",
            "amount_eur": None,
            "amount_label_ru": (
                f"${exchange_balance_usd:.2f} на бирже"
                if exchange_balance_usd is not None
                else "Баланс: зайдите на биржу"
            ),
            "status": "crash_test" if toloka.get("connected") else "offline",
            "status_ru": (
                f"Toloka Requester · {toloka_submit_count} submit"
                if toloka_submit_count
                else "Toloka Requester · crash-test API"
            ),
            "detail_ru": (
                "Не работодатель — инструмент: stress-test pipeline, делегирование разметки клиенту. "
                "Wallet $0 при Requester — норма. Performer = другой аккаунт."
            ),
            "toloka_connected": bool(toloka.get("connected")),
            "scale_connected": bool(scale.get("connected")),
            "withdraw_note_ru": toloka.get("withdraw_note") or scale.get("withdraw_note") or "",
        },
        {
            "id": "b2b_client",
            "icon": "💶",
            "label_ru": "B2B — путь к банку",
            "amount_eur": paid_by_client_eur,
            "amount_label_ru": f"{paid_by_client_eur:.2f} € оплачено",
            "status": "primary" if paid_by_client_eur > 0 else "waiting",
            "status_ru": (
                "Клиент оплатил (webhook)" if paid_by_client_eur > 0 else "Ждём первую оплату клиента"
            ),
            "detail_ru": (
                f"Доступно к выводу: {received_eur:.2f} € · Settlement: {pending_eur:.2f} € · "
                f"Outbox: {outbox_pending or pending_proposals} · разговоров: {contacted}."
            ),
        },
    ]

    withdraw_alert = {
        "active": withdraw_ready,
        "level": (
            "green"
            if withdraw_ready
            else ("amber" if pending_proposals else "none")
        ),
        "title_ru": (
            "🟢 Биржа: можно вывести на Stripe (не B2B-выручка)"
            if withdraw_ready
            else (
                "🟡 Одобрите письма в Outbox — путь к первому €"
                if pending_proposals
                else "Баланс биржи ниже порога"
            )
        ),
        "message_ru": alert_message or (
            f"Порог ${threshold:.0f}. Genesis не выводит сам — зайдите на toloka.ai / scale.com → Withdraw → Stripe."
            if not withdraw_ready
            else alert_message
        ),
        "threshold_usd": threshold,
        "ceo_action_ru": (
            "toloka.ai или scale.com → Wallet → Withdraw → Stripe → банк (SEPA 1–3 дня)"
            if withdraw_ready
            else "/business → Одобрить все → дождаться оплаты клиента"
        ),
    }

    pipeline = [
        {"step": 1, "id": "spider", "title_ru": "Spider", "detail_ru": "Ищет компании и сырьё"},
        {"step": 2, "id": "discovery", "title_ru": "Discovery", "detail_ru": "Оценивает проблемы сайта"},
        {"step": 3, "id": "qualification", "title_ru": "Qualification", "detail_ru": "Сайт · email · оффер"},
        {"step": 4, "id": "audit", "title_ru": "Аудит + КП", "detail_ru": "Отчёт для клиента (продукт)"},
        {"step": 5, "id": "approve", "title_ru": "Approve CEO", "detail_ru": "Одна кнопка — вы"},
        {"step": 6, "id": "send", "title_ru": "Отправка", "detail_ru": "Email / WhatsApp"},
        {"step": 7, "id": "reply", "title_ru": "Ответ клиента", "detail_ru": "Журнал возможностей"},
        {"step": 8, "id": "pay", "title_ru": "Оплата", "detail_ru": "Stripe / счёт → банк · рыночный риск"},
        {"step": 9, "id": "factory", "title_ru": "Биржа (фон)", "detail_ru": "Crash-test + делегирование, не доход"},
    ]

    model_proven = paid_by_client_eur > 0
    sales_funnel = build_sales_funnel_progress(
        opps,
        received_eur=paid_by_client_eur,
        training_eur=training_eur,
        outbox_pending=outbox_pending or pending_proposals,
    )
    mission2_kpi = build_mission2_kpi(
        opps,
        received_eur=paid_by_client_eur,
        training_eur=training_eur,
        outbox_pending=outbox_pending or pending_proposals,
    )

    return {
        "title_ru": "Приборная панель — деньги",
        "subtitle_ru": "Hero = только Stripe/B2B · ферма и биржа — отдельно",
        "actual_revenue": actual_revenue,
        "farm_potential": farm_potential,
        "real_money": real_money,
        "sales_funnel": sales_funnel,
        "mission2_kpi": mission2_kpi,
        "lanes": lanes,
        "withdraw_alert": withdraw_alert,
        "pipeline": pipeline,
        "model_proven": model_proven,
        "model_verdict_ru": (
            "Модель доказана — деньги поступили на подключённый счёт."
            if model_proven
            else "Модель не доказана — нужна хотя бы 1 успешная B2B-сделка с оплатой."
        ),
        "toloka_role_ru": (
            "Toloka сейчас: Requester (заводской цех). "
            f"{toloka_submit_count} submit = портфолио надёжности API. "
            "Заработок performer — отдельный аккаунт toloka.ai."
        ),
    }
