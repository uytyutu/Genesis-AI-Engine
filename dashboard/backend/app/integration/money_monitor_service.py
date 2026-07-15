"""Money Monitor — три канала денег: учебный ledger · биржа (цех) · B2B (банк)."""

from __future__ import annotations

from typing import Any


def build_money_monitor(
    *,
    farm_state: dict[str, Any],
    payment_monitor: dict[str, Any] | None = None,
    opportunities: list[dict[str, Any]] | None = None,
    outbox_pending: int = 0,
    toloka_submit_count: int = 0,
) -> dict[str, Any]:
    """Genesis = приборная панель. Биржа = касса (CEO вручную). B2B = реальный €."""
    pm = payment_monitor or {}
    monitor = pm.get("monitor") or {}
    payout = pm.get("payout") or {}
    opps = opportunities or []

    training_eur = round(float(farm_state.get("total_earned_eur") or 0), 2)
    llm_cost = round(float(farm_state.get("llm_cost_eur") or 0), 2)
    tasks = int(farm_state.get("total_tasks_done") or 0)

    won = [r for r in opps if r.get("status") == "won"]
    b2b_revenue = round(sum(float(r.get("revenue_eur") or 0) for r in won), 2)
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
            "label_ru": "Учебный счётчик фермы",
            "amount_eur": training_eur,
            "amount_label_ru": f"{training_eur:.2f} €",
            "status": "simulation",
            "status_ru": "Не банк · не выводить",
            "detail_ru": (
                f"{tasks} задач × ~0,05 € — журнал для теста конвейера. "
                f"Расход LLM (реальный): {llm_cost:.2f} €."
            ),
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
            "amount_eur": b2b_revenue,
            "amount_label_ru": f"{b2b_revenue:.2f} € подтверждено",
            "status": "primary" if b2b_revenue > 0 else "waiting",
            "status_ru": (
                "Первый € получен" if b2b_revenue > 0 else "Ждём первую оплату клиента"
            ),
            "detail_ru": (
                f"Outbox: {outbox_pending or pending_proposals} на Approve · "
                f"разговоров: {contacted}. Продаём аудит 50–500 €, не разметку."
            ),
        },
    ]

    withdraw_alert = {
        "active": withdraw_ready,
        "level": "green" if withdraw_ready else ("amber" if b2b_revenue <= 0 and pending_proposals else "none"),
        "title_ru": (
            "🟢 Пора вывести с биржи"
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
        {"step": 8, "id": "pay", "title_ru": "Оплата", "detail_ru": "Stripe / счёт → банк"},
        {"step": 9, "id": "factory", "title_ru": "Биржа (фон)", "detail_ru": "Crash-test + делегирование, не доход"},
    ]

    model_proven = b2b_revenue > 0

    return {
        "title_ru": "Приборная панель — деньги",
        "subtitle_ru": "Genesis показывает · биржа выдаёт по команде CEO · B2B = банк",
        "lanes": lanes,
        "withdraw_alert": withdraw_alert,
        "pipeline": pipeline,
        "model_proven": model_proven,
        "model_verdict_ru": (
            "Модель доказана — есть оплата клиента."
            if model_proven
            else "Модель не доказана — нужна хотя бы 1 успешная B2B-сделка."
        ),
        "toloka_role_ru": (
            "Toloka сейчас: Requester (заводской цех). "
            f"{toloka_submit_count} submit = портфолио надёжности API. "
            "Заработок performer — отдельный аккаунт toloka.ai."
        ),
    }
