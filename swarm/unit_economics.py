"""Unit economics per adapter — estimates vs real confirmed income.

Honest: local _ADAPTER_PAY_EUR is ESTIMATED revenue, not bank money.
"""

from __future__ import annotations

from typing import Any

from swarm.revenue_source import (
    CONFIDENCE_CONFIRMED,
    CONFIDENCE_ESTIMATED,
    CONFIDENCE_SIMULATED,
    confidence_label,
)

# Mirror of micro_farm_service._ADAPTER_PAY_EUR — keep in sync intentionally.
LOCAL_ADAPTER_GROSS_EUR: dict[str, float] = {
    "ai_labeling": 0.05,
    "data_clean": 0.02,
    "text_classify": 0.03,
    "record_verify": 0.01,
}

# Conservative defaults when no measured LLM cost per task yet
DEFAULT_LLM_EUR_PER_TASK = 0.004
DEFAULT_API_EUR_PER_TASK = 0.0
DEFAULT_INFRA_EUR_PER_TASK = 0.001


def unit_row(
    *,
    source_id: str,
    name: str,
    gross_eur: float,
    api_eur: float,
    llm_eur: float,
    infra_eur: float,
    confidence: str,
    automation: str,
    notes_ru: str,
) -> dict[str, Any]:
    cost = round(api_eur + llm_eur + infra_eur, 4)
    net = round(gross_eur - cost, 4)
    roi = None
    if cost > 0:
        roi = round(net / cost, 2)
    elif gross_eur > 0:
        roi = None  # infinite on paper — mark honestly
    return {
        "source_id": source_id,
        "name": name,
        "avg_gross_eur": round(gross_eur, 4),
        "avg_api_cost_eur": round(api_eur, 4),
        "avg_llm_cost_eur": round(llm_eur, 4),
        "avg_infra_cost_eur": round(infra_eur, 4),
        "avg_total_cost_eur": cost,
        "avg_net_eur": net,
        "roi": roi,
        "roi_note_ru": (
            "ROI = net / cost; null если cost=0 (не делим на ноль)"
            if cost == 0
            else "ROI = net / cost"
        ),
        "confidence": confidence,
        "confidence_label_ru": confidence_label(confidence),
        "automation": automation,
        "notes_ru": notes_ru,
        "is_real_income": confidence == CONFIDENCE_CONFIRMED,
    }


def build_unit_economics(
    *,
    farm_state: dict[str, Any] | None = None,
    confirmed_payouts_eur: float = 0.0,
    stripe_avg_order_eur: float = 0.0,
) -> dict[str, Any]:
    state = farm_state or {}
    tasks = max(1, int(state.get("total_tasks_done") or 0) or 1)
    llm_total = float(state.get("llm_cost_eur") or 0.0)
    measured_llm = round(llm_total / tasks, 4) if int(state.get("total_tasks_done") or 0) > 0 else DEFAULT_LLM_EUR_PER_TASK

    rows: list[dict[str, Any]] = []
    for adapter_id, gross in LOCAL_ADAPTER_GROSS_EUR.items():
        rows.append(
            unit_row(
                source_id=adapter_id,
                name=f"Internal · {adapter_id}",
                gross_eur=gross,
                api_eur=DEFAULT_API_EUR_PER_TASK,
                llm_eur=measured_llm if adapter_id in {"ai_labeling", "text_classify"} else 0.0,
                infra_eur=DEFAULT_INFRA_EUR_PER_TASK,
                confidence=CONFIDENCE_ESTIMATED,
                automation="full_local",
                notes_ru=(
                    "Gross из локальной таблицы _ADAPTER_PAY_EUR — не выплата биржи. "
                    "Чистая «прибыль» здесь учебная."
                ),
            )
        )

    rows.append(
        unit_row(
            source_id="toloka",
            name="Toloka Pipeline (requester)",
            gross_eur=0.0,
            api_eur=0.0,
            llm_eur=0.0,
            infra_eur=DEFAULT_INFRA_EUR_PER_TASK,
            confidence=CONFIDENCE_SIMULATED,
            automation="submit_only",
            notes_ru=(
                "В коде Virtus — заказчик: submit labels. "
                "Доход performer = 0 в этой интеграции. Pipeline может быть расходом (billing)."
            ),
        )
    )
    rows.append(
        unit_row(
            source_id="scale_ai",
            name="Scale AI (customer)",
            gross_eur=0.0,
            api_eur=0.0,
            llm_eur=0.0,
            infra_eur=DEFAULT_INFRA_EUR_PER_TASK,
            confidence=CONFIDENCE_SIMULATED,
            automation="probe_only",
            notes_ru="Адаптер: connection + list tasks. Заработка performer в коде нет.",
        )
    )

    stripe_gross = float(stripe_avg_order_eur or 0.0)
    rows.append(
        unit_row(
            source_id="stripe",
            name="Stripe B2B order",
            gross_eur=stripe_gross,
            api_eur=round(stripe_gross * 0.014 + 0.25, 4) if stripe_gross > 0 else 0.25,
            llm_eur=0.0,
            infra_eur=0.0,
            confidence=CONFIDENCE_CONFIRMED if stripe_gross > 0 else CONFIDENCE_ESTIMATED,
            automation="webhook",
            notes_ru=(
                "Реальный доход при webhook checkout.completed. "
                "Комиссия ~1.4% + 0.25 € (EU card approx). "
                f"confirmed_payouts_seen={confirmed_payouts_eur:.2f} €"
            ),
        )
    )

    real_rows = [r for r in rows if r["is_real_income"]]
    est_rows = [r for r in rows if r["confidence"] == CONFIDENCE_ESTIMATED]
    return {
        "title": "Unit Economics — Virtus Core farm / revenue adapters",
        "disclaimer_ru": (
            "Оценки внутренней фермы ≠ деньги на счёте. "
            "Реальный доход сегодня: Stripe (и будущие CONFIRMED payout_id). "
            "Toloka/Scale в текущей роли не дают performer revenue."
        ),
        "measured": {
            "total_tasks_done": int(state.get("total_tasks_done") or 0),
            "llm_cost_eur_total": round(llm_total, 4),
            "llm_eur_per_task_measured": measured_llm,
            "today_earned_eur_estimate": float(state.get("today_earned_eur") or 0),
            "total_earned_eur_estimate": float(state.get("total_earned_eur") or 0),
        },
        "rows": rows,
        "summary": {
            "adapters_with_real_income": len(real_rows),
            "adapters_estimate_only": len(est_rows),
            "best_real_source": real_rows[0]["source_id"] if real_rows else None,
            "verdict_ru": (
                "Деньги приносит Stripe (B2B). "
                "Внутренняя ферма создаёт активность и estimate. "
                "Toloka/Scale как подключены сейчас — не источник performer-выплат."
            ),
        },
    }
