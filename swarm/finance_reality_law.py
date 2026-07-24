"""Finance Reality Law — binding rules for Virtus Core money paths.

Rule №1 — Reality over Simulation:
No income source is "working" until proven by real inflows and confirmed data.
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
LAW_VERSION = "1"

RULES_RU: tuple[str, ...] = (
    "№1 Reality over Simulation — источник не «рабочий», пока нет реальных поступлений "
    "и подтверждённых данных.",
    "Estimate ≠ Revenue. PENDING ≠ CONFIRMED. CONFIRMED ≠ WITHDRAWN. WITHDRAWN ≠ BOOKED.",
    "Никакой симуляции в финансовых отчётах как будто это деньги на счёте.",
    "Никаких обходов ToS платформ — запрещённая автоматизация = источник не используется.",
    "Каждый источник проходит аудит: API · подтверждение дохода · вывод · ROI — до подключения.",
    "Owner Gate: Virtus никогда не создаёт аккаунты, не принимает ToS, не подписывает договоры, "
    "не привязывает банковские счета.",
    "Каждый источник должен быть прибыльным после API+LLM+infra — иначе кандидат на отключение.",
    "Испытательный период: первые N операций или первый месяц — только после этого Candidate → Active.",
)


def law_manifest() -> dict[str, Any]:
    return {
        "id": LAW_ID,
        "version": LAW_VERSION,
        "title_en": "Reality over Simulation",
        "title_ru": "Реальность важнее симуляции",
        "confidence_ladder": list(CONFIDENCE_LADDER),
        "inequalities_ru": [
            "Estimate ≠ Revenue",
            "PENDING ≠ CONFIRMED",
            "CONFIRMED ≠ WITHDRAWN",
            "WITHDRAWN ≠ BOOKED",
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
            "В отчётах для CEO/налога: только CONFIRMED / WITHDRAWN / BOOKED как доход. "
            "SIMULATED и ESTIMATED — отдельно, никогда не суммировать с реальным."
        ),
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
