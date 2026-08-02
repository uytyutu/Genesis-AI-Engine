"""Finance Reality Law — binding rules for Virtus Core money paths.

Rule №1 — Reality over Simulation:
No income source is "working" until proven by real inflows and confirmed data.

Rule №1c — Hard REAL definition (CEO 2026-08-01):
REAL exists only when External Payout ID + amount + currency + paid_at + source
are all present. Otherwise it is NOT REAL (forecast / estimate / pending).

Rule №2 — Single Source of Truth (CEO 2026-08-02):
Only one write path may increase REAL. Modules may emit Forecast / Estimate /
Expected / Pending; they must never mutate REAL / Profit / Ledger totals directly.

Rule №3 — Live Earn before REAL income (CEO 2026-08-02):
Real income is possible only after at least one Live Earn Connector that passed
Legal Review and has confirmed external payouts. Until then all figures are modeling.
"""

from __future__ import annotations

from typing import Any

# Canonical ladder — never collapse adjacent states
CONFIDENCE_LADDER = (
    "SIMULATED",
    "ESTIMATED",
    "PENDING",
    "CONFIRMED",
    "WITHDRAWN",
    "BOOKED",
)

# Trial before Candidate → Active
DEFAULT_TRIAL_OPS = 100
DEFAULT_TRIAL_DAYS = 30

LAW_ID = "FINANCE_REALITY_OVER_SIMULATION"
LAW_VERSION = "1.4"

# Law №3 — system is modeling-only until Live Earn exists with confirmed payouts
INCOME_PHASE_MODELING = "modeling"
INCOME_PHASE_REAL_ELIGIBLE = "real_eligible"

LIVE_EARN_PRECONDITIONS: tuple[dict[str, str], ...] = (
    {
        "id": "live_earn_connector",
        "title_ru": "Подключён хотя бы один Live Earn Connector",
    },
    {
        "id": "legal_review_pass",
        "title_ru": "Legal Review PASS для этого connector",
    },
    {
        "id": "confirmed_external_payouts",
        "title_ru": "Есть подтверждённые внешние выплаты (Hard REAL)",
    },
)

# Law №2 — sole pipeline that may increase REAL (downstream of Hard REAL gate)
REAL_TRUTH_PIPELINE: tuple[str, ...] = (
    "external_platform",
    "external_payout_id",
    "finance_reality_law",
    "finance_ledger",
    "money_monitor",
    "payout_manager",
    "roi",
)

# Modules may create non-REAL categories only — never mutate REAL totals
MODULES_MAY_EMIT_NON_REAL: tuple[str, ...] = (
    "forecast",
    "estimate",
    "expected_reward",
    "pending_platform_review",
    "approved_platform",
)

# Illustrative forbidden writers (any peer that skips the pipeline)
FORBIDDEN_REAL_MUTATORS_RU: tuple[str, ...] = (
    "Farm Engine → real += …",
    "AI Router → profit += …",
    "Opportunity Scanner → earned_today += …",
    "Revenue Model → money += forecast",
)

# Canonical Earn Connector path (Stripe, RapidAPI, Marketplace, …)
CONNECTOR_INGEST_PIPELINE: tuple[str, ...] = (
    "connector",
    "normalize_payout",
    "is_real_money_event",
    "finance_ledger",
)

# Hard REAL — all five required (missing any → not REAL)
REAL_REQUIRED_FIELDS: tuple[str, ...] = (
    "external_payout_id",
    "amount",
    "currency",
    "paid_at",
    "source_id",
)

# Display categories (UI / Farm / connectors) — only external_payout_received is REAL
MONEY_CATEGORIES: tuple[dict[str, Any], ...] = (
    {
        "id": "forecast",
        "label_en": "Forecast",
        "label_ru": "Прогноз",
        "show": True,
        "is_real": False,
    },
    {
        "id": "estimate",
        "label_en": "Estimate",
        "label_ru": "Оценка",
        "show": True,
        "is_real": False,
    },
    {
        "id": "expected_reward",
        "label_en": "Expected reward",
        "label_ru": "Ожидаемое вознаграждение",
        "show": True,
        "is_real": False,
    },
    {
        "id": "pending_platform_review",
        "label_en": "Pending platform review",
        "label_ru": "Ожидает проверки платформой",
        "show": True,
        "is_real": False,
    },
    {
        "id": "approved_platform",
        "label_en": "Approved platform",
        "label_ru": "Одобрено платформой",
        "show": True,
        "is_real": False,
        "note_ru": "Ещё не REAL — нет внешней выплаты",
    },
    {
        "id": "external_payout_received",
        "label_en": "External payout received",
        "label_ru": "Внешняя выплата получена",
        "show": True,
        "is_real": True,
        "note_ru": "Единственная категория, допускаемая в REAL / Profit / Ledger / Payout / ROI",
    },
)

RULES_RU: tuple[str, ...] = (
    "№1 Reality over Simulation — источник не «рабочий», пока нет реальных поступлений "
    "и подтверждённых данных.",
    "№1b External Payout ID — любая сумма становится доходом (REAL) только после внешнего "
    "подтверждения выплаты с payout ID. До этого: прогноз / ожидание / оценка — не доход.",
    "№1c Hard REAL — REAL существует только при всех пяти полях: External Payout ID · "
    "Amount · Currency · Paid at · Source. Иначе это НЕ REAL.",
    "№2 Источник истины один — REAL увеличивается только по цепочке External Platform → "
    "External Payout ID → Finance Reality Law → Finance Ledger → Money Monitor → "
    "Payout Manager → ROI. Никакой другой модуль не вправе сам менять REAL.",
    "№2b Connector ingest — Connector → normalize_payout → is_real_money_event → Ledger. "
    "Неважно, Stripe, RapidAPI, Marketplace или Farm Earn — путь один.",
    "№3 Live Earn before REAL — реальный доход возможен только после подключения хотя бы "
    "одного Live Earn Connector с Legal Review PASS и подтверждёнными внешними выплатами. "
    "До этого все оценки — моделирование, не доход.",
    "Estimate ≠ Revenue. PENDING ≠ CONFIRMED. CONFIRMED ≠ WITHDRAWN. WITHDRAWN ≠ BOOKED.",
    "≈0.15 € ожидается → только Estimate. Platform approved → только Pending Payout. "
    "В REAL/Profit/Ledger/Payout Manager/ROI — только запись с полным паспортом выплаты.",
    "Симуляции (Forecast 12 500 €/мес, Expected 0.32 €) можно показывать сколько угодно — "
    "Profit/REAL/ROI/Withdraw остаются 0, пока нет Live Earn + настоящего payout.",
    "LLM/dry_run/«потенциал» никогда не пишутся в REAL как заработанные деньги.",
    "Никакой симуляции в финансовых отчётах как будто это деньги на счёте.",
    "Никаких обходов ToS платформ — запрещённая автоматизация = источник не используется.",
    "Каждый источник проходит аудит: API · подтверждение дохода · вывод · ROI — до подключения.",
    "Owner Gate: Virtus никогда не создаёт аккаунты, не принимает ToS, не подписывает договоры, "
    "не привязывает банковские счета.",
    "Каждый источник должен быть прибыльным после API+LLM+infra — иначе кандидат на отключение.",
    "Испытательный период: первые N операций или первый месяц — только после этого Candidate → Active.",
)


def _field_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    return bool(str(value).strip())


def is_real_money_event(payload: dict[str, Any] | None) -> bool:
    """True only when all REAL_REQUIRED_FIELDS are present and amount is finite."""
    if not isinstance(payload, dict):
        return False
    # Accept common aliases used across ledger / Stripe / farm
    aliases = {
        "external_payout_id": (
            payload.get("external_payout_id")
            or payload.get("payout_id")
            or payload.get("stripe_payout_id")
        ),
        "amount": payload.get("amount")
        if payload.get("amount") is not None
        else payload.get("amount_eur"),
        "currency": payload.get("currency") or payload.get("currency_code"),
        "paid_at": (
            payload.get("paid_at")
            or payload.get("settlement_date")
            or payload.get("booked_at")
        ),
        "source_id": (
            payload.get("source_id")
            or payload.get("connector")
            or payload.get("platform")
            or payload.get("source")
        ),
    }
    for key in REAL_REQUIRED_FIELDS:
        if not _field_present(aliases.get(key)):
            return False
    try:
        float(aliases["amount"])
    except (TypeError, ValueError):
        return False
    return True


def real_money_missing_fields(payload: dict[str, Any] | None) -> list[str]:
    """Which REAL fields are missing (for CEO / connector diagnostics)."""
    if not isinstance(payload, dict):
        return list(REAL_REQUIRED_FIELDS)
    check = {
        "external_payout_id": (
            payload.get("external_payout_id")
            or payload.get("payout_id")
            or payload.get("stripe_payout_id")
        ),
        "amount": payload.get("amount")
        if payload.get("amount") is not None
        else payload.get("amount_eur"),
        "currency": payload.get("currency") or payload.get("currency_code"),
        "paid_at": (
            payload.get("paid_at")
            or payload.get("settlement_date")
            or payload.get("booked_at")
        ),
        "source_id": (
            payload.get("source_id")
            or payload.get("connector")
            or payload.get("platform")
            or payload.get("source")
        ),
    }
    missing: list[str] = []
    for key in REAL_REQUIRED_FIELDS:
        if not _field_present(check.get(key)):
            missing.append(key)
        elif key == "amount":
            try:
                float(check["amount"])
            except (TypeError, ValueError):
                missing.append(key)
    return missing


def module_may_mutate_real(module_id: str | None) -> bool:
    """Law №2: only the Finance Ledger write path may increase REAL.

    Callers identify as the ledger ingest gate. Everything else returns False.
    """
    mid = str(module_id or "").strip().lower()
    return mid in {"finance_ledger", "ledger", "finance_ledger_ingest"}


def income_phase(
    *,
    live_earn_connector: bool = False,
    legal_review_pass: bool = False,
    confirmed_external_payouts: bool = False,
) -> dict[str, Any]:
    """Law №3: modeling until Live Earn + Legal + confirmed external payouts."""
    checks = {
        "live_earn_connector": bool(live_earn_connector),
        "legal_review_pass": bool(legal_review_pass),
        "confirmed_external_payouts": bool(confirmed_external_payouts),
    }
    ready = all(checks.values())
    phase = INCOME_PHASE_REAL_ELIGIBLE if ready else INCOME_PHASE_MODELING
    return {
        "phase": phase,
        "is_modeling": not ready,
        "real_income_possible": ready,
        "checks": checks,
        "preconditions": list(LIVE_EARN_PRECONDITIONS),
        "law_ru": (
            "Реальный доход возможен только после подключения хотя бы одного "
            "Live Earn Connector с Legal Review PASS и подтверждёнными внешними "
            "выплатами. До этого все оценки — моделирование."
        ),
    }


def is_modeling_only(
    *,
    live_earn_connector: bool = False,
    legal_review_pass: bool = False,
    confirmed_external_payouts: bool = False,
) -> bool:
    """True when the system must treat all money figures as modeling."""
    return bool(
        income_phase(
            live_earn_connector=live_earn_connector,
            legal_review_pass=legal_review_pass,
            confirmed_external_payouts=confirmed_external_payouts,
        )["is_modeling"]
    )


def law_manifest() -> dict[str, Any]:
    return {
        "id": LAW_ID,
        "version": LAW_VERSION,
        "title_en": "Reality over Simulation",
        "title_ru": "Реальность важнее симуляции",
        "confidence_ladder": list(CONFIDENCE_LADDER),
        "real_required_fields": list(REAL_REQUIRED_FIELDS),
        "real_definition_ru": (
            "REAL = существует только при: External Payout ID · Amount · Currency · "
            "Paid at · Source. Иначе это НЕ REAL."
        ),
        "law_2_ru": (
            "Источник истины один — REAL меняет только цепочка с is_real_money_event "
            "и записью в Finance Ledger. Farm / AI Router / Scanner / Revenue Model "
            "могут писать только Forecast / Estimate / Expected / Pending."
        ),
        "law_3_ru": (
            "Реальный доход возможен только после Live Earn Connector + Legal Review "
            "и подтверждённых внешних выплат. До этого все оценки — моделирование."
        ),
        "live_earn_preconditions": list(LIVE_EARN_PRECONDITIONS),
        "income_phases": [INCOME_PHASE_MODELING, INCOME_PHASE_REAL_ELIGIBLE],
        "real_truth_pipeline": list(REAL_TRUTH_PIPELINE),
        "connector_ingest_pipeline": list(CONNECTOR_INGEST_PIPELINE),
        "modules_may_emit_non_real": list(MODULES_MAY_EMIT_NON_REAL),
        "forbidden_real_mutators_ru": list(FORBIDDEN_REAL_MUTATORS_RU),
        "money_categories": list(MONEY_CATEGORIES),
        "inequalities_ru": [
            "Estimate ≠ Revenue",
            "No External Payout ID ≠ REAL income",
            "Approved platform ≠ REAL (until payout)",
            "Modeling ≠ REAL income",
            "No Live Earn Connector ≠ REAL income",
            "PENDING ≠ CONFIRMED",
            "CONFIRMED ≠ WITHDRAWN",
            "WITHDRAWN ≠ BOOKED",
            "Module estimate ≠ Ledger REAL",
        ],
        "rules_ru": list(RULES_RU),
        "owner_gate_ru": (
            "Virtus Core никогда сама не создаёт аккаунты, не принимает ToS, "
            "не подписывает договоры и не привязывает банковские счета."
        ),
        "trial": {
            "ops": DEFAULT_TRIAL_OPS,
            "days": DEFAULT_TRIAL_DAYS,
            "note_ru": (
                "Новый источник остаётся Candidate, пока не пройдёт испытание "
                f"({DEFAULT_TRIAL_OPS} операций или {DEFAULT_TRIAL_DAYS} дней) "
                "с подтверждёнными поступлениями."
            ),
        },
        "report_rule_ru": (
            "В отчётах для CEO/налога: только CONFIRMED / WITHDRAWN / BOOKED как доход, "
            "и только если выполнен Hard REAL (5 полей) и фаза real_eligible (Law №3). "
            "SIMULATED и ESTIMATED — отдельно, никогда не суммировать с реальным. "
            "Пока modeling — все цифры помечать как моделирование."
        ),
        "real_destinations_ru": [
            "REAL",
            "Profit",
            "Ledger",
            "Payout Manager",
            "ROI",
        ],
    }


def states_must_not_collapse(a: str, b: str) -> bool:
    """True if a and b are distinct ladder steps that must stay unequal."""
    if a not in CONFIDENCE_LADDER or b not in CONFIDENCE_LADDER:
        return a != b
    return a != b


def is_reportable_revenue(confidence: str) -> bool:
    """Only these may appear as real income in financial reports."""
    return confidence in {"CONFIRMED", "WITHDRAWN", "BOOKED"}


def trial_passed(*, confirmed_ops: int = 0, active_days: int = 0) -> bool:
    return int(confirmed_ops or 0) >= DEFAULT_TRIAL_OPS or int(active_days or 0) >= DEFAULT_TRIAL_DAYS


def profitability_gate(*, net_eur: float) -> str:
    """Return keep | watch | disconnect_candidate."""
    if net_eur > 0:
        return "keep"
    if net_eur == 0:
        return "watch"
    return "disconnect_candidate"
