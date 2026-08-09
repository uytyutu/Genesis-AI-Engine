"""Money Monitor — REAL / SPENT / PREDICTION · Earn vs Spend · B2B."""

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
    """Genesis = приборная панель. Earn OFF сегодня · Spend = requester · B2B = Stripe."""
    from app.integration.swarm_bridge import ensure_swarm_importable

    ensure_swarm_importable()
    from swarm.farm_channel_board import build_farm_channel_board, build_money_truth
    from swarm.payout_manager import build_payout_manager

    pm = payment_monitor or {}
    monitor = pm.get("monitor") or {}
    payout = pm.get("payout") or {}
    opps = opportunities or []

    training_eur = round(float(farm_state.get("total_earned_eur") or 0), 2)
    llm_cost = round(float(farm_state.get("llm_cost_eur") or 0), 2)
    verified_spend = round(float(farm_state.get("verified_spend_eur") or 0), 2)
    spent_eur = round(llm_cost + verified_spend, 2)
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
    prediction_eur = float((real_money.get("forecast") or {}).get("amount_eur") or 0)

    channel_board = build_farm_channel_board()
    money_truth = build_money_truth(
        real_eur=paid_by_client_eur,
        spent_eur=spent_eur,
        prediction_eur=prediction_eur,
    )
    earn_on = int(channel_board["summary"]["earn_on_count"])

    sandbox = bool(fin.get("sandbox")) or str(fin.get("system_mode") or "").lower() == "sandbox"
    payout_manager = build_payout_manager(
        finance_snapshot=fin.get("finance_snapshot") or {},
        payout_history=fin.get("payout_history") or [],
        payment_connected=bool(fin.get("payment_connected")),
        demo_mode=bool(fin.get("demo_mode")),
        sandbox=sandbox,
        farm_state=farm_state,
    )
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

    withdraw_ready = bool(payout.get("has_withdraw_ready")) and earn_on > 0
    alert_message = ""
    if withdraw_ready and payout.get("pending_alerts"):
        alert_message = str(payout["pending_alerts"][0].get("message") or "")

    api_farm_block: dict[str, Any] = {}
    rapidapi_actual = 0.0
    rapidapi_pending = 0.0
    rapidapi_gross = 0.0
    rapidapi_fee = 0.0
    try:
        from swarm.farm_channels.rapidapi.monitor import portfolio_metrics
        from swarm.farm_channels.rapidapi.revenue import revenue_summary
        from swarm.farm_channels.rapidapi.store import ApiFarmStore
        from swarm.farm_channels.rapidapi.worker import status_payload as api_farm_status

        _afs = ApiFarmStore()
        port = portfolio_metrics(_afs)
        rev = revenue_summary(_afs)
        rapidapi_actual = float(rev.get("actual_revenue") or 0)
        rapidapi_pending = float(rev.get("pending_payout") or 0)
        rapidapi_gross = float(rev.get("gross_revenue") or 0)
        rapidapi_fee = float(rev.get("marketplace_fee") or 0)
        st = api_farm_status(_afs)
        api_farm_block = {
            **port,
            "revenue": rev,
            "status": st,
            "ceo_action": st.get("ceo_action") or [],
            "requires_ceo_action": bool(st.get("requires_ceo_action")),
            "paypal_payout_confirmed": bool(st.get("paypal_payout_confirmed")),
            "public_api": st.get("public_api") or {},
            "best_candidate": st.get("best_candidate"),
            "payout_path_ru": "RapidAPI → PayPal",
            "not_stripe": True,
            "actual_only_paid_out": True,
        }
    except Exception:
        api_farm_block = {
            "candidates": 0,
            "building": 0,
            "testing": 0,
            "ready": 0,
            "published": 0,
            "active": 0,
            "failed": 0,
            "api_calls": 0,
            "subscribers": 0,
            "revenue": {
                "actual_revenue": 0,
                "pending_payout": 0,
                "gross_revenue": 0,
                "marketplace_fee": 0,
                "paid_out": 0,
                "net_earned": 0,
                "potential_not_real": 0,
            },
        }

    total_actual = round(paid_by_client_eur + rapidapi_actual, 2)
    real_revenue_hero = {
        "title_ru": "REAL REVENUE",
        "stripe_gross_eur": paid_by_client_eur,
        "stripe_net_eur": received_eur,
        "stripe_pending_eur": pending_eur,
        "rapidapi_gross": rapidapi_gross,
        "rapidapi_fee": rapidapi_fee,
        "rapidapi_net_earned": float(
            (api_farm_block.get("revenue") or {}).get("net_earned") or 0
        ),
        "rapidapi_pending_payout": rapidapi_pending,
        "rapidapi_paid_out": rapidapi_actual,
        "b2b_eur": paid_by_client_eur,
        "api_farm_eur": rapidapi_actual,
        "total_actual_eur": total_actual,
        "total_actual_label_ru": f"{total_actual:.2f} €",
        "farm_potential_not_real_eur": float(farm_potential["farm_journal_eur"]),
        "training_ledger_not_real_eur": training_eur,
        "legend_ru": {
            "actual": "Только подтверждённые Stripe settlements + RapidAPI PAID_OUT",
            "potential": "Farm Potential / Training Ledger — НЕ деньги",
        },
    }

    lanes = [
        {
            "id": "training_ledger",
            "icon": "📊",
            "label_ru": "Журнал фермы (estimate) — НЕ деньги",
            "amount_eur": farm_potential["farm_journal_eur"],
            "amount_label_ru": farm_potential["amount_label_ru"],
            "status": "simulation",
            "status_ru": "NOT REAL MONEY · не Actual Revenue",
            "detail_ru": farm_potential["detail_ru"],
        },
        {
            "id": "exchange_factory",
            "icon": "🏭",
            "label_ru": "Spend · Requester цех",
            "amount_eur": None,
            "amount_label_ru": (
                f"${exchange_balance_usd:.2f} баланс кабинета"
                if exchange_balance_usd is not None
                else "Spend-канал · не копилка Virtus"
            ),
            "status": "crash_test" if toloka.get("connected") else "offline",
            "status_ru": (
                f"Toloka Requester · {toloka_submit_count} submit"
                if toloka_submit_count
                else "Toloka Requester · earn OFF"
            ),
            "detail_ru": (
                "Текущая роль: Spend (Virtus платит за разметку). "
                "Путь Performer → баланс → Withdraw → Stripe в коде не подключён."
            ),
            "toloka_connected": bool(toloka.get("connected")),
            "scale_connected": bool(scale.get("connected")),
            "withdraw_note_ru": "",
        },
        {
            "id": "b2b_client",
            "icon": "💶",
            "label_ru": "Stripe / B2B — REAL",
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
        {
            "id": "rapidapi_api_farm",
            "icon": "🔌",
            "label_ru": "RapidAPI / API Farm — REAL only PAID_OUT",
            "amount_eur": rapidapi_actual,
            "amount_label_ru": f"{rapidapi_actual:.2f} paid out",
            "status": "primary" if rapidapi_actual > 0 else "waiting",
            "status_ru": (
                "Есть подтверждённый RapidAPI payout"
                if rapidapi_actual > 0
                else "Ждём 1 API → 1 user → 1 PAID_OUT (PayPal)"
            ),
            "detail_ru": (
                f"Gross {rapidapi_gross:.2f} · Fee {rapidapi_fee:.2f} · "
                f"Pending {rapidapi_pending:.2f} · Payout: RapidAPI→PayPal (не Stripe). "
                f"Candidates {api_farm_block.get('candidates', 0)} · "
                f"Active {api_farm_block.get('active', 0)}."
            ),
        },
    ]

    if earn_on > 0 and withdraw_ready:
        withdraw_alert = {
            "active": True,
            "level": "green",
            "title_ru": "🟢 Earn-канал: можно вывести (не B2B)",
            "message_ru": alert_message
            or f"Порог ${threshold:.0f}. Вывод вручную в кабинете биржи → Stripe.",
            "threshold_usd": threshold,
            "ceo_action_ru": "Кабинет биржи (performer) → Withdraw → Stripe → банк",
        }
    elif pending_proposals:
        withdraw_alert = {
            "active": False,
            "level": "amber",
            "title_ru": "🟡 Одобрите письма в Outbox — путь к первому €",
            "message_ru": "Earn-каналы OFF. Реальный доход сегодня — Path A (Stripe).",
            "threshold_usd": threshold,
            "ceo_action_ru": "/business → Одобрить → дождаться оплаты клиента",
        }
    else:
        withdraw_alert = {
            "active": False,
            "level": "none",
            "title_ru": "Earn OFF · фокус Path A",
            "message_ru": (
                "Toloka/Scale в Virtus = requester (SPENT), не performer (REAL). "
                "Не путать прогноз фермы с деньгами на счёте."
            ),
            "threshold_usd": threshold,
            "ceo_action_ru": "Mission 1: Places → Email → Stripe. Mission VRE — после первого клиента.",
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

    path_a_funnel = None
    try:
        from app.integration.pricing_display_service import PricingDisplayService

        path_a_funnel = PricingDisplayService().path_a_funnel_summary()
    except Exception:
        path_a_funnel = None

    return {
        "title_ru": "Приборная панель — деньги",
        "subtitle_ru": (
            "REAL REVENUE = Stripe + RapidAPI PAID_OUT · "
            "Farm Potential / Training — NOT REAL MONEY"
        ),
        "money_truth": money_truth,
        "channel_board": channel_board,
        "payout_manager": payout_manager,
        "actual_revenue": actual_revenue,
        "farm_potential": {
            **farm_potential,
            "label_ru": "Farm Potential — NOT REAL MONEY",
            "not_real_money": True,
        },
        "real_money": real_money,
        "real_revenue_hero": real_revenue_hero,
        "api_farm": api_farm_block,
        "sales_funnel": sales_funnel,
        "path_a_funnel": path_a_funnel,
        "mission2_kpi": mission2_kpi,
        "lanes": lanes,
        "withdraw_alert": withdraw_alert,
        "pipeline": pipeline,
        "model_proven": model_proven or rapidapi_actual > 0,
        "model_verdict_ru": (
            "Модель доказана — деньги поступили на подключённый счёт."
            if model_proven or rapidapi_actual > 0
            else "Модель не доказана — нужна 1 B2B Stripe оплата или 1 RapidAPI PAID_OUT."
        ),
        "toloka_role_ru": (
            "Toloka сейчас: Execution + Spend / Requester. "
            f"{toloka_submit_count} submit · LLM/API SPENT={spent_eur:.2f} €. "
            "Не источник вывода. ROI — по операции с клиентом."
        ),
    }
