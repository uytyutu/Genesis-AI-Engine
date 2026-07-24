"""Farm task lifecycle — honest RU labels (estimate vs real exchange payout)."""

from __future__ import annotations

from typing import Any

STAGE_ACCEPTED = "task_accepted"
STAGE_COMPLETED = "task_completed"
STAGE_REWARD_ESTIMATE = "reward_estimate"
STAGE_PAYMENT_PENDING = "payment_pending"
STAGE_PAYMENT_CONFIRMED = "payment_confirmed"
STAGE_BALANCE_INCREASED = "balance_increased"
STAGE_FAILED = "task_failed"
STAGE_CYCLE_ACCOUNTED = "cycle_accounted"

STAGE_TITLES_RU: dict[str, str] = {
    STAGE_ACCEPTED: "Задача взята в работу",
    STAGE_COMPLETED: "Задача обработана",
    STAGE_REWARD_ESTIMATE: "Оценка вознаграждения",
    STAGE_PAYMENT_PENDING: "Ожидает подтверждения платформой",
    STAGE_PAYMENT_CONFIRMED: "Платформа подтвердила оплату",
    STAGE_BALANCE_INCREASED: "Баланс биржи обновился",
    STAGE_CYCLE_ACCOUNTED: "Расчётный учёт цикла",
    STAGE_FAILED: "Задача не прошла",
}

# Stages that may show money as withdrawable / real income
REAL_MONEY_STAGES = frozenset({STAGE_PAYMENT_CONFIRMED, STAGE_BALANCE_INCREASED})

WITHDRAW_STEPS_RU = [
    "Реальные деньги копятся только на бирже (Toloka / Scale) — не в локальном журнале фермы.",
    "Когда баланс биржи ≥ порога — алерт в ферме.",
    "Вы заходите на toloka.ai или scale.com → Withdraw → свой Stripe.",
    "Stripe → банковский счёт (SEPA) — вручную, 1–3 дня.",
]


def stage_title(stage: str) -> str:
    return STAGE_TITLES_RU.get(stage, stage)


def detail_for_stage(
    stage: str,
    *,
    task_label: str,
    pay_eur: float = 0.0,
    platform: str = "ферма",
    sandbox: bool = False,
    balance_eur: float | None = None,
    payout_id: str = "",
    real_payout: bool = False,
) -> str:
    if stage == STAGE_ACCEPTED:
        return f"{task_label} · локальный цикл ({platform})"
    if stage == STAGE_COMPLETED:
        return f"{task_label} · обработка завершена локально"
    if stage == STAGE_REWARD_ESTIMATE:
        kind = "учебная оценка" if sandbox else "оценка"
        return (
            f"{task_label} · {kind} +{pay_eur:.4f} € "
            "(ещё не выплата биржи, к выводу на Stripe не доступно)"
        )
    if stage == STAGE_PAYMENT_PENDING:
        return f"{task_label} · ждём ответ Toloka/Scale (API/webhook), не локальную таблицу"
    if stage == STAGE_PAYMENT_CONFIRMED:
        if not real_payout:
            return (
                f"{task_label} · отказ: нет реального подтверждения биржи "
                "(не пишем «оплата подтверждена»)"
            )
        pid = f" · ID {payout_id}" if payout_id else ""
        return f"{task_label} · биржа начислила +{pay_eur:.4f} €{pid} · доступно к выводу на стороне платформы"
    if stage == STAGE_BALANCE_INCREASED:
        bal = f"{balance_eur:.4f}" if balance_eur is not None else "—"
        return f"Баланс биржи (API): {bal} · зафиксировано +{pay_eur:.4f} €"
    if stage == STAGE_CYCLE_ACCOUNTED:
        return (
            f"{task_label} · расчётный учёт цикла +{pay_eur:.4f} € "
            "(не доход к выводу на Stripe)"
        )
    if stage == STAGE_FAILED:
        return f"{task_label} · ошибка или отклонено"
    return task_label


def lifecycle_chain(
    *,
    ok: bool,
    sandbox: bool,
    live_exchange: bool,
    pay_eur: float,
    real_payout: bool = False,
) -> list[str]:
    """Stages after a local task finishes.

    Never invents payment_confirmed. That stage is only returned when
    real_payout=True (exchange API / webhook proof with amount).
    """
    if not ok:
        return [STAGE_FAILED]
    stages = [STAGE_ACCEPTED, STAGE_COMPLETED]
    if pay_eur <= 0:
        return stages
    # Estimated path — honest journal
    stages.append(STAGE_REWARD_ESTIMATE)
    if live_exchange and not sandbox:
        stages.append(STAGE_PAYMENT_PENDING)
    if real_payout:
        stages.append(STAGE_PAYMENT_CONFIRMED)
    return stages


def payout_ui_block(threshold_usd: float = 10.0) -> dict[str, Any]:
    return {
        "title": "Как выводить реальные деньги",
        "steps": WITHDRAW_STEPS_RU,
        "threshold_usd": threshold_usd,
        "auto_payout": False,
        "note": (
            "«Оценка вознаграждения» в журнале ≠ деньги на Stripe. "
            "Вывод только с баланса Toloka/Scale вручную."
        ),
    }
