"""Farm task lifecycle — honest RU labels (Spend ≠ Earn ≠ REAL).

Toloka Pipeline / Scale as requester = Spend success (dataset accepted).
That is NOT «platform will pay Virtus 0.05 €».
"""

from __future__ import annotations

from typing import Any, Literal

STAGE_ACCEPTED = "task_accepted"
STAGE_COMPLETED = "task_completed"
STAGE_REWARD_ESTIMATE = "reward_estimate"
STAGE_PAYMENT_PENDING = "payment_pending"
STAGE_PAYMENT_CONFIRMED = "payment_confirmed"
STAGE_BALANCE_INCREASED = "balance_increased"
STAGE_FAILED = "task_failed"
STAGE_CYCLE_ACCOUNTED = "cycle_accounted"
STAGE_SPEND_ACCEPTED = "spend_accepted"

MoneyDirection = Literal["spend", "earn_model", "earn_live"]

STAGE_TITLES_RU: dict[str, str] = {
    STAGE_ACCEPTED: "Задача взята в работу",
    STAGE_COMPLETED: "Задача обработана",
    STAGE_SPEND_ACCEPTED: "Spend OK · dataset/pipeline принят (мы платим / заказчик)",
    STAGE_REWARD_ESTIMATE: "Оценка вознаграждения (моделирование)",
    STAGE_PAYMENT_PENDING: "Ожидает выплаты Earn Connector (не Spend)",
    STAGE_PAYMENT_CONFIRMED: "Платформа подтвердила оплату",
    STAGE_BALANCE_INCREASED: "Баланс Earn-платформы обновился",
    STAGE_CYCLE_ACCOUNTED: "Расчётный учёт цикла (не REAL)",
    STAGE_FAILED: "Задача не прошла",
}

# Stages that may show money as withdrawable / real income
REAL_MONEY_STAGES = frozenset({STAGE_PAYMENT_CONFIRMED, STAGE_BALANCE_INCREASED})

# Adapters that are requester/Spend — Pipeline OK ≠ Earn payout
SPEND_ADAPTER_IDS = frozenset(
    {
        "toloka",
        "toloka_probe",
        "toloka_submit",
        "scale_ai",
        "scale",
    }
)

WITHDRAW_STEPS_RU = [
    "REAL растёт только после Live Earn Connector + External Payout ID (Finance Reality Law).",
    "Toloka Pipeline / Scale Requester = Spend: dataset принят ≠ Virtus получил €.",
    "Первый Live Earn Connector (свой API+Stripe, RapidAPI Provider…) → Hard REAL → Ledger.",
    "Path A Stripe (B2B) — отдельный Commercial Engine, не «доход фермы Toloka».",
]


def stage_title(stage: str) -> str:
    return STAGE_TITLES_RU.get(stage, stage)


def money_direction_for_adapter(adapter_id: str | None) -> MoneyDirection:
    aid = str(adapter_id or "").strip().lower()
    if aid in SPEND_ADAPTER_IDS or aid.startswith("toloka"):
        return "spend"
    return "earn_model"


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
    if stage == STAGE_SPEND_ACCEPTED:
        return (
            f"{task_label} · платформа приняла dataset/pipeline (Spend/Requester). "
            "Это не начисление вознаграждения Virtus — External Payout ID не ожидается."
        )
    if stage == STAGE_REWARD_ESTIMATE:
        kind = "учебная оценка" if sandbox else "моделирование"
        return (
            f"{task_label} · {kind} ≈{pay_eur:.4f} € "
            "(не выплата; REAL не растёт без Live Earn + payout ID)"
        )
    if stage == STAGE_PAYMENT_PENDING:
        return (
            f"{task_label} · ждём Earn-выплату с External Payout ID "
            "(не Toloka Requester Pipeline OK)"
        )
    if stage == STAGE_PAYMENT_CONFIRMED:
        if not real_payout:
            return (
                f"{task_label} · отказ: нет реального подтверждения биржи "
                "(не пишем «оплата подтверждена»)"
            )
        pid = f" · ID {payout_id}" if payout_id else ""
        return (
            f"{task_label} · биржа начислила +{pay_eur:.4f} €{pid} · "
            "доступно к выводу на стороне платформы"
        )
    if stage == STAGE_BALANCE_INCREASED:
        bal = f"{balance_eur:.4f}" if balance_eur is not None else "—"
        return f"Баланс Earn-платформы (API): {bal} · зафиксировано +{pay_eur:.4f} €"
    if stage == STAGE_CYCLE_ACCOUNTED:
        return (
            f"{task_label} · расчётный учёт цикла ≈{pay_eur:.4f} € "
            "(моделирование, не доход к выводу)"
        )
    if stage == STAGE_FAILED:
        return f"{task_label} · ошибка или отклонено"
    return task_label


def lifecycle_chain(
    *,
    ok: bool,
    sandbox: bool,
    pay_eur: float,
    money_direction: MoneyDirection | str = "earn_model",
    real_payout: bool = False,
    earn_payout_awaited: bool = False,
    live_exchange: bool | None = None,
) -> list[str]:
    """Stages after a local task finishes.

    money_direction:
      spend      — Requester/Pipeline (Toloka…): success ≠ Virtus paid
      earn_model — local estimate / dry_run modeling only
      earn_live  — true Earn Connector path (may await payout)

    Never invents payment_confirmed without real_payout.
    payment_pending only when earn_live and earn_payout_awaited (not Spend).
    """
    if not ok:
        return [STAGE_FAILED]

    direction = str(money_direction or "earn_model").strip().lower()
    # Legacy: live_exchange=True used to append payment_pending even for Spend — forbidden.
    if live_exchange is True and direction == "earn_model" and earn_payout_awaited:
        direction = "earn_live"

    stages = [STAGE_ACCEPTED, STAGE_COMPLETED]

    if direction == "spend":
        stages.append(STAGE_SPEND_ACCEPTED)
        return stages

    if pay_eur <= 0:
        return stages

    stages.append(STAGE_REWARD_ESTIMATE)

    if direction == "earn_live" and not sandbox and earn_payout_awaited:
        stages.append(STAGE_PAYMENT_PENDING)

    if real_payout:
        stages.append(STAGE_PAYMENT_CONFIRMED)

    return stages


def payout_ui_block(threshold_usd: float = 10.0) -> dict[str, Any]:
    return {
        "title": "Как появляется реальный доход фермы",
        "steps": WITHDRAW_STEPS_RU,
        "threshold_usd": threshold_usd,
        "auto_payout": False,
        "note": (
            "«Оценка вознаграждения» и Toloka Pipeline OK ≠ деньги на Stripe. "
            "Нужен Live Earn Connector + External Payout ID (Hard REAL)."
        ),
    }
