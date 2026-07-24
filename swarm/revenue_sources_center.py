"""Revenue Sources v0 — income control center (no web discovery).

Bound by Finance Reality Law (swarm/finance_reality_law.py).
Owner Gate: Virtus never creates accounts or accepts ToS for the CEO.
"""

from __future__ import annotations

from typing import Any

from swarm.finance_reality_law import law_manifest, trial_passed
from swarm.revenue_source import (
    CONFIDENCE_BOOKED,
    CONFIDENCE_CONFIRMED,
    CONFIDENCE_ESTIMATED,
    CONFIDENCE_SIMULATED,
    confidence_label,
)

# Display statuses for the control center
STATUS_ACTIVE = "active"
STATUS_CANDIDATE = "candidate"
STATUS_UNSUPPORTED = "unsupported"
STATUS_COST = "cost"
STATUS_STUB = "stub"

STATUS_LABEL_RU = {
    STATUS_ACTIVE: "Active",
    STATUS_CANDIDATE: "Candidate",
    STATUS_UNSUPPORTED: "Unsupported",
    STATUS_COST: "Cost only",
    STATUS_STUB: "Not wired",
}

STATUS_EMOJI = {
    STATUS_ACTIVE: "🟢",
    STATUS_CANDIDATE: "🟡",
    STATUS_UNSUPPORTED: "🔴",
    STATUS_COST: "⚪",
    STATUS_STUB: "🔴",
}

# Extra display confidences for center (not bookkeeping ladder)
CONF_NOT_CONNECTED = "NOT_CONNECTED"
CONF_UNSUPPORTED = "UNSUPPORTED"
CONF_COST = "COST"


def build_revenue_sources_center(
    *,
    stripe_income_eur: float = 0.0,
    stripe_connected: bool = False,
    ledger_real_eur: float = 0.0,
    farm_estimate_eur: float = 0.0,
    stripe_confirmed_ops: int = 0,
    stripe_active_days: int = 0,
) -> dict[str, Any]:
    """Curated catalog — candidates added manually, never auto-scraped."""
    law = law_manifest()
    stripe_amt = round(float(stripe_income_eur or 0) + float(ledger_real_eur or 0), 2)
    if stripe_income_eur > 0:
        stripe_amt = round(float(stripe_income_eur), 2)

    stripe_trial_ok = trial_passed(
        confirmed_ops=stripe_confirmed_ops,
        active_days=stripe_active_days,
    )
    # Proven inflows → Active. Connected without money stays Candidate until trial/proof.
    stripe_active = stripe_amt > 0 or (stripe_connected and stripe_trial_ok)
    sources = [
        _row(
            source_id="stripe",
            name="Stripe",
            status=STATUS_ACTIVE if stripe_active else STATUS_CANDIDATE,
            income_type="Merchant",
            income_eur=stripe_amt,
            income_label=_money_or_dash(stripe_amt),
            roi_label="+" if stripe_amt > 0 else ("?" if not stripe_connected else "0"),
            confidence=CONFIDENCE_BOOKED if stripe_amt > 0 else (
                CONF_NOT_CONNECTED if not stripe_connected else CONFIDENCE_CONFIRMED
            ),
            automation_score=100,
            why_ru=(
                (
                    "Реальные платежи клиентов через Checkout/webhook. "
                    "Единственный подтверждённый денежный вход продукта сегодня. "
                    "Вывод на банк — через Stripe Dashboard / payout schedule. "
                    + str(law["trial"]["note_ru"])
                )
                if stripe_amt > 0 or stripe_connected
                else "Кандидат: нужен STRIPE_SECRET_KEY + webhook. Пока нет оплат — доход 0."
            ),
            action_ru="Работает" if stripe_active else "Подключить ключи Stripe / пройти испытание",
            scalable=True,
            trial_passed_flag=bool(stripe_amt > 0 or stripe_trial_ok),
        ),
        _row(
            source_id="awin",
            name="Awin",
            status=STATUS_CANDIDATE,
            income_type="Affiliate",
            income_eur=None,
            income_label="—",
            roi_label="?",
            confidence=CONF_NOT_CONNECTED,
            automation_score=90,
            why_ru=(
                "Партнёрская сеть с официальным reporting API. "
                "Комиссии реальные после продаж; вывод обычно SEPA/кабинет. "
                "Не подключён: нет ключа и адаптера. Owner gate — регистрация только CEO."
            ),
            action_ru="Подключить (нужен API-ключ владельца)",
            scalable=True,
        ),
        _row(
            source_id="digistore24",
            name="Digistore24",
            status=STATUS_CANDIDATE,
            income_type="Affiliate",
            income_eur=None,
            income_label="—",
            roi_label="?",
            confidence=CONF_NOT_CONNECTED,
            automation_score=90,
            why_ru=(
                "Партнёрские комиссии (часто DE/EU). IPN/API для учёта конверсий. "
                "Кандидат вручную — без автопоиска. Ключ и ToS только владелец."
            ),
            action_ru="Подключить (нужен API-ключ владельца)",
            scalable=True,
        ),
        _row(
            source_id="toloka",
            name="Toloka Pipeline",
            status=STATUS_UNSUPPORTED,
            income_type="Requester",
            income_eur=0.0,
            income_label="0 €",
            roi_label="—",
            confidence=CONF_UNSUPPORTED,
            automation_score=10,
            why_ru=(
                "В Virtus подключён Pipeline API как заказчик (submit datasets/runs), "
                "не performer-кошелёк. Баланса выплат в API нет. "
                "Не использовать как источник дохода исполнителя."
            ),
            action_ru="Не использовать как доход",
            scalable=False,
        ),
        _row(
            source_id="scale_ai",
            name="Scale AI",
            status=STATUS_UNSUPPORTED,
            income_type="Requester",
            income_eur=0.0,
            income_label="0 €",
            roi_label="—",
            confidence=CONF_UNSUPPORTED,
            automation_score=5,
            why_ru=(
                "Адаптер — probe + список задач customer API. "
                "Submit/performer earnings в коде отсутствуют. Не источник дохода Virtus."
            ),
            action_ru="Не использовать как доход",
            scalable=False,
        ),
        _row(
            source_id="internal_queue",
            name="Внутренняя ферма",
            status=STATUS_STUB,
            income_type="Simulator",
            income_eur=round(float(farm_estimate_eur or 0), 4),
            income_label=f"~{float(farm_estimate_eur or 0):.2f} € est.",
            roi_label="est.",
            confidence=CONFIDENCE_ESTIMATED,
            automation_score=95,
            why_ru=(
                "Локальные комбайны + таблица estimate. Высокая автоматизация, "
                "но Confidence=ESTIMATED — это не деньги на счёте и не Stripe."
            ),
            action_ru="Только обучение / оценка",
            scalable=False,
        ),
        _row(
            source_id="groq",
            name="Groq",
            status=STATUS_COST,
            income_type="Infrastructure",
            income_eur=None,
            income_label="расход",
            roi_label="—",
            confidence=CONF_COST,
            automation_score=100,
            why_ru="LLM API — стоимость разметки/ответов. Не источник дохода.",
            action_ru="Игнорировать как доход",
            scalable=False,
        ),
        _row(
            source_id="kimi",
            name="Kimi / Moonshot",
            status=STATUS_COST,
            income_type="Infrastructure",
            income_eur=None,
            income_label="расход",
            roi_label="—",
            confidence=CONF_COST,
            automation_score=100,
            why_ru="LLM API — инфраструктурный расход. Не источник дохода.",
            action_ru="Игнорировать как доход",
            scalable=False,
        ),
    ]

    active = [s for s in sources if s["status"] == STATUS_ACTIVE]
    candidates = [s for s in sources if s["status"] == STATUS_CANDIDATE]
    unsupported = [s for s in sources if s["status"] in {STATUS_UNSUPPORTED, STATUS_STUB, STATUS_COST}]

    return {
        "title": "Revenue Sources",
        "subtitle_ru": "Центр управления доходами — только подтверждённые и вручную добавленные кандидаты",
        "law": law,
        "owner_gate_ru": law["owner_gate_ru"],
        "discovery_ru": (
            "Revenue Discovery (автопоиск по интернету) — отложен. "
            "v0 = ядро каталога + оценка. Кандидаты добавляются вручную."
        ),
        "reality_law_ru": law["title_ru"] + " — " + law["rules_ru"][0],
        "columns": [
            "source",
            "status",
            "type",
            "income",
            "roi",
            "confidence",
            "automation",
            "why",
            "action",
        ],
        "sources": sources,
        "summary": {
            "active": len(active),
            "candidates": len(candidates),
            "blocked_or_cost": len(unsupported),
            "real_income_eur": stripe_amt,
            "verdict_ru": (
                "Масштабировать: Stripe (Active) и affiliate-кандидаты после ключей. "
                "Toloka/Scale — Unsupported как доход. Внутренняя ферма — только estimate."
            ),
        },
    }


def _money_or_dash(amount: float) -> str:
    if amount <= 0:
        return "0 €"
    return f"{amount:.2f} €"


def _row(
    *,
    source_id: str,
    name: str,
    status: str,
    income_type: str,
    income_eur: float | None,
    income_label: str,
    roi_label: str,
    confidence: str,
    automation_score: int,
    why_ru: str,
    action_ru: str,
    scalable: bool,
    trial_passed_flag: bool = False,
) -> dict[str, Any]:
    conf_display = confidence
    if confidence in {
        CONFIDENCE_BOOKED,
        CONFIDENCE_CONFIRMED,
        CONFIDENCE_ESTIMATED,
        CONFIDENCE_SIMULATED,
    }:
        conf_label_ru = confidence_label(confidence)
    else:
        conf_label_ru = confidence

    return {
        "id": source_id,
        "name": name,
        "status": status,
        "status_emoji": STATUS_EMOJI.get(status, "⚪"),
        "status_label": STATUS_LABEL_RU.get(status, status),
        "type": income_type,
        "income_eur": income_eur,
        "income_label": income_label,
        "roi_label": roi_label,
        "confidence": conf_display,
        "confidence_label_ru": conf_label_ru,
        "automation_score": int(automation_score),
        "automation_label": f"{int(automation_score)}%",
        "why_ru": why_ru,
        "action_ru": action_ru,
        "scalable": scalable,
        "trial_passed": trial_passed_flag,
    }
