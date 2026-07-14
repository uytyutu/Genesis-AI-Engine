"""Farm task lifecycle — Russian UI labels for journal and earnings."""

from __future__ import annotations

from typing import Any

STAGE_ACCEPTED = "task_accepted"
STAGE_COMPLETED = "task_completed"
STAGE_PAYMENT_CONFIRMED = "payment_confirmed"
STAGE_BALANCE_INCREASED = "balance_increased"
STAGE_PAYMENT_PENDING = "payment_pending"
STAGE_FAILED = "task_failed"

STAGE_TITLES_RU: dict[str, str] = {
    STAGE_ACCEPTED: "Задача принята",
    STAGE_COMPLETED: "Задача выполнена",
    STAGE_PAYMENT_PENDING: "Ожидает подтверждения платформы",
    STAGE_PAYMENT_CONFIRMED: "Платформа подтвердила оплату",
    STAGE_BALANCE_INCREASED: "Баланс увеличился",
    STAGE_FAILED: "Задача не прошла",
}

WITHDRAW_STEPS_RU = [
    "Деньги копятся на бирже (Toloka / Scale) — не в Genesis автоматически.",
    "Когда баланс ≥ порога — алерт в ферме.",
    "Ты заходишь на toloka.ai или scale.com → Withdraw → свой Stripe.",
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
) -> str:
    if stage == STAGE_ACCEPTED:
        return f"{task_label} · взята в работу ({platform})"
    if stage == STAGE_COMPLETED:
        return f"{task_label} · разметка/обработка завершена"
    if stage == STAGE_PAYMENT_PENDING:
        return f"{task_label} · отправлено на проверку биржи"
    if stage == STAGE_PAYMENT_CONFIRMED:
        if sandbox:
            return f"{task_label} · учебное начисление +{pay_eur:.4f} € (sandbox)"
        return f"{task_label} · +{pay_eur:.4f} € подтверждено ({platform})"
    if stage == STAGE_BALANCE_INCREASED:
        bal = f"{balance_eur:.4f} €" if balance_eur is not None else "—"
        return f"Счёт фермы: {bal} · +{pay_eur:.4f} € за цикл"
    if stage == STAGE_FAILED:
        return f"{task_label} · ошибка или отклонено"
    return task_label


def lifecycle_chain(
    *,
    ok: bool,
    sandbox: bool,
    live_exchange: bool,
    pay_eur: float,
) -> list[str]:
    """Ordered stages to emit after a task finishes."""
    if not ok:
        return [STAGE_FAILED]
    stages = [STAGE_ACCEPTED, STAGE_COMPLETED]
    if pay_eur <= 0:
        return stages
    if live_exchange:
        stages.extend([STAGE_PAYMENT_PENDING, STAGE_PAYMENT_CONFIRMED])
    elif sandbox:
        stages.append(STAGE_PAYMENT_CONFIRMED)
    else:
        stages.append(STAGE_PAYMENT_CONFIRMED)
    return stages


def payout_ui_block(threshold_usd: float = 10.0) -> dict[str, Any]:
    return {
        "title": "Как выводить деньги",
        "steps": WITHDRAW_STEPS_RU,
        "threshold_usd": threshold_usd,
        "auto_payout": False,
        "note": "Genesis не трогает Stripe — только показывает, когда пора вывести с биржи.",
    }
