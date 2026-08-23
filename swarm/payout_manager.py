"""Payout Manager — where REAL sits and how it may leave (official paths only).

Not an Earn source. Does not invent withdraw methods.
See docs/MISSION_BOARD.md · Payout role.
"""

from __future__ import annotations

from typing import Any


def _eur(amount: float) -> str:
    return f"{float(amount):,.2f} €".replace(",", " ").replace(".", ",")


# Catalog of Earn → payout profiles (research + live Stripe). Extend per new Earn Connector.
_EARN_PAYOUT_PROFILES: list[dict[str, Any]] = [
    {
        "id": "stripe_path_a",
        "name": "Stripe · Path A / B2B",
        "role": "earn",
        "status": "live",
        "balance_location_ru": "Stripe (баланс провайдера)",
        "methods": [
            {
                "id": "sepa_bank",
                "label_ru": "SEPA / банковский счёт",
                "official": True,
            },
            {
                "id": "stripe_payout",
                "label_ru": "Stripe Payout (по расписанию аккаунта)",
                "official": True,
            },
        ],
        "min_note_ru": "После settlement (DE ~3 раб. дня) · лимиты Stripe",
        "fees_note_ru": "Комиссии Stripe + банк получателя — по тарифу аккаунта",
        "external_dashboard_url": "https://dashboard.stripe.com/balance/overview",
        "virtus_withdraw_api": True,
        "note_ru": "Единственный живой Earn сегодня. Вывод только из confirmed available.",
    },
    {
        "id": "rapidapi_provider",
        "name": "RapidAPI Provider",
        "role": "earn",
        "status": "research",
        "balance_location_ru": "RapidAPI (кабинет провайдера)",
        "methods": [
            {
                "id": "paypal",
                "label_ru": "PayPal (официально)",
                "official": True,
            },
        ],
        "min_note_ru": "Выплаты по календарю Rapid (~лаг 1–2 мес.)",
        "fees_note_ru": "Marketplace fee ~25% + PayPal",
        "external_dashboard_url": "https://rapidapi.com/developer/billing",
        "virtus_withdraw_api": False,
        "note_ru": (
            "API Farm channel (swarm/farm_channels/rapidapi). "
            "Payout: RapidAPI → PayPal. Virtus пишет Actual только после PAID_OUT Hard REAL. "
            "Stripe сюда не подмешивается."
        ),
    },
    {
        "id": "own_api_mpp",
        "name": "Own API · Stripe MPP / Checkout",
        "role": "earn",
        "status": "research",
        "balance_location_ru": "Тот же Stripe balance",
        "methods": [
            {
                "id": "sepa_bank",
                "label_ru": "SEPA / банковский счёт",
                "official": True,
            },
        ],
        "min_note_ru": "Как у Stripe Path A",
        "fees_note_ru": "Тариф Stripe",
        "external_dashboard_url": "https://dashboard.stripe.com/balance/overview",
        "virtus_withdraw_api": True,
        "note_ru": "Earn Rank 1 — после Legal Review / продукта. Пока = тот же Stripe.",
    },
]

# Execution tools — never offer withdraw
_EXECUTION_NOT_PAYOUT: list[dict[str, Any]] = [
    {
        "id": "toloka_requester",
        "name": "Toloka",
        "role": "execution",
        "note_ru": "Execution + Spend. Не выплачивает ферме. ROI — по операции с клиентом.",
    },
    {
        "id": "llm",
        "name": "LLM (OpenAI / Gemini / …)",
        "role": "execution",
        "note_ru": "Execution. Расход на выполнение, не источник вывода.",
    },
    {
        "id": "ocr_browser",
        "name": "OCR / Browser Automation",
        "role": "execution",
        "note_ru": "Execution. Не кошелёк.",
    },
]


def build_payout_manager(
    *,
    finance_snapshot: dict[str, Any] | None = None,
    payout_history: list[dict[str, Any]] | None = None,
    payment_connected: bool = False,
    demo_mode: bool = False,
    sandbox: bool = False,
    farm_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """CEO board: balances per Earn source + official withdraw options."""
    snap = finance_snapshot or {}
    history = payout_history or []
    farm = farm_state or {}

    paid = round(float(snap.get("paid_by_client_eur") or 0), 2)
    pending = round(float(snap.get("pending_settlement_eur") or 0), 2)
    available = round(float(snap.get("available_for_withdrawal_eur") or 0), 2)
    pending_payouts = round(float(snap.get("pending_payouts_eur") or 0), 2)

    llm_cost = round(float(farm.get("llm_cost_eur") or 0), 2)
    verified_spend = round(float(farm.get("verified_spend_eur") or 0), 2)
    execution_cost = round(llm_cost + verified_spend, 2)
    # Infrastructure not always broken out — treat Places/VPS as optional fields later
    infrastructure_cost = round(float(farm.get("infrastructure_cost_eur") or 0), 2)
    real_profit = round(paid - execution_cost - infrastructure_cost, 2)

    sources: list[dict[str, Any]] = []
    for profile in _EARN_PAYOUT_PROFILES:
        row = dict(profile)
        methods = list(profile.get("methods") or [])
        bal_eur = 0.0
        withdrawable = False
        status_ru = "нет средств"

        if profile["id"] in {"stripe_path_a", "own_api_mpp"}:
            if profile["id"] == "stripe_path_a":
                bal_eur = available
                if sandbox or demo_mode:
                    status_ru = "Sandbox / демо — вывод заблокирован"
                    withdrawable = False
                elif not payment_connected and available <= 0:
                    status_ru = "Stripe не подключён или пусто"
                elif available > 0 and not sandbox:
                    status_ru = "доступно к выводу"
                    withdrawable = True
                elif pending > 0:
                    status_ru = f"settlement · ждём ({_eur(pending)})"
                elif paid > 0:
                    status_ru = "оплачено · ждём available"
                else:
                    status_ru = "ожидание первой оплаты"
            else:
                status_ru = "research · тот же Stripe после запуска"
                bal_eur = 0.0
        elif profile["id"] == "rapidapi_provider":
            status_ru = "research · адаптер OFF"
            bal_eur = 0.0

        cta = "disabled"
        cta_label_ru = "Вывод недоступен"
        if withdrawable and profile.get("virtus_withdraw_api"):
            cta = "virtus_api"
            cta_label_ru = "Вывести заработанные"
        elif profile.get("external_dashboard_url") and profile["status"] == "live" and not withdrawable:
            cta = "external"
            cta_label_ru = "Открыть кабинет Stripe"
        elif profile.get("external_dashboard_url") and profile["status"] == "research":
            cta = "external_info"
            cta_label_ru = "Официальный кабинет (пока нет баланса Virtus)"

        sources.append(
            {
                **row,
                "methods": methods,
                "balance_eur": bal_eur,
                "balance_label_ru": _eur(bal_eur),
                "withdraw_status_ru": status_ru,
                "withdrawable": withdrawable,
                "cta": cta,
                "cta_label_ru": cta_label_ru,
            }
        )

    recent = []
    for p in history[-10:]:
        recent.append(
            {
                "at": p.get("at"),
                "amount_eur": round(float(p.get("amount_eur") or 0), 2),
                "amount_label_ru": _eur(float(p.get("amount_eur") or 0)),
                "provider": p.get("provider") or p.get("destination") or "—",
                "status": p.get("status") or "",
                "status_label_ru": p.get("status_label") or p.get("status") or "",
            }
        )
    recent.reverse()

    total_withdrawable = sum(s["balance_eur"] for s in sources if s.get("withdrawable"))

    return {
        "title_ru": "Payout Manager",
        "subtitle_ru": (
            "Где лежат подтверждённые деньги и как их официально вывести. "
            "Ферма не придумывает способ вывода."
        ),
        "rule_ru": (
            "Earn → REAL → Payout. Execution (Toloka, LLM, …) не имеет кнопки вывода. "
            "KPI: Revenue − Execution − Infrastructure = REAL PROFIT."
        ),
        "kpi": {
            "revenue_eur": paid,
            "revenue_label_ru": _eur(paid),
            "execution_cost_eur": execution_cost,
            "execution_cost_label_ru": _eur(execution_cost),
            "infrastructure_cost_eur": infrastructure_cost,
            "infrastructure_cost_label_ru": _eur(infrastructure_cost),
            "real_profit_eur": real_profit,
            "real_profit_label_ru": _eur(real_profit),
            "pending_settlement_eur": pending,
            "pending_payouts_eur": pending_payouts,
            "formula_ru": "Revenue − Execution Cost − Infrastructure Cost = REAL PROFIT",
        },
        "sources": sources,
        "execution_not_payout": _EXECUTION_NOT_PAYOUT,
        "history": recent,
        "summary": {
            "total_withdrawable_eur": round(total_withdrawable, 2),
            "total_withdrawable_label_ru": _eur(total_withdrawable),
            "any_withdrawable": total_withdrawable > 0,
            "sandbox": bool(sandbox),
            "demo_mode": bool(demo_mode),
            "verdict_ru": (
                f"К выводу сейчас: {_eur(total_withdrawable)} (только официальные Earn)."
                if total_withdrawable > 0
                else "Нет доступного к выводу REAL. Toloka/LLM не кошельки."
            ),
        },
    }
