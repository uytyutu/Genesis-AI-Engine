"""Dry-run mode — log potential live profit without spending VPS or exchange fees."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("genesis.farm")

# Projected €/task on live exchanges (Scale-class), minus typical API cost applied separately.
POTENTIAL_PAY_EUR: dict[str, float] = {
    "ai_labeling": 0.15,
    "text_classify": 0.08,
    "data_clean": 0.04,
    "record_verify": 0.02,
}

MILESTONE_STREAK = 100


def is_dry_run_mode(farm_mode: str) -> bool:
    return (farm_mode or "dry_run").lower() != "live"


def potential_profit_eur(*, adapter_id: str, llm_cost_eur: float = 0.0) -> float:
    gross = float(POTENTIAL_PAY_EUR.get(adapter_id, 0.05))
    return round(max(0.0, gross - float(llm_cost_eur or 0)), 2)


def format_log_line(profit_eur: float) -> str:
    return f"[DRY RUN] Potential profit: €{profit_eur:.2f}"


def log_potential_profit(
    *,
    adapter_id: str,
    task_id: str,
    llm_cost_eur: float = 0.0,
    streak: int = 1,
) -> dict[str, Any]:
    """Emit console line CEO watches before buying VPS."""
    profit = potential_profit_eur(adapter_id=adapter_id, llm_cost_eur=llm_cost_eur)
    line = format_log_line(profit)
    logger.info(
        "%s · adapter=%s · task=%s · streak=%s/%s",
        line,
        adapter_id,
        task_id,
        streak,
        MILESTONE_STREAK,
    )
    milestone = streak >= MILESTONE_STREAK
    if milestone:
        logger.info(
            "[DRY RUN] Milestone %s reached — VPS ticket validated (math, not bank payout yet)",
            MILESTONE_STREAK,
        )
    return {
        "log_line": line,
        "potential_profit_eur": profit,
        "adapter_id": adapter_id,
        "task_id": task_id,
        "streak": streak,
        "milestone_reached": milestone,
        "milestone_target": MILESTONE_STREAK,
    }


def explain_task_selection(
    *,
    labeling_workers: int,
    legacy_tasks: list[tuple[str, str]],
    allocation: dict[str, int],
    disabled_adapters: list[str],
    arbitrage_winner: str | None = None,
) -> dict[str, Any]:
    """How the swarm picks work — transparent pipeline for CEO."""
    return {
        "execution": "local",
        "mode": "dry_run",
        "pipeline": [
            {
                "step": 1,
                "name": "Trigger",
                "detail": "asset_scan opportunities → неразмеченные сайты; raw_queue — запасная очередь",
            },
            {
                "step": 2,
                "name": "Priority Manager",
                "detail": (
                    f"Распределение: {allocation}. "
                    f"Отключено self-healing: {disabled_adapters or 'нет'}"
                ),
            },
            {
                "step": 3,
                "name": "AI labeling swarm",
                "detail": f"До {labeling_workers} параллельных комбайнов (async batch)",
            },
            {
                "step": 4,
                "name": "Legacy pipeline",
                "detail": (
                    "data_clean → text_classify → record_verify по meta-флагам"
                    if legacy_tasks
                    else "Очередь пуста — нужен feed/поиск сайтов"
                ),
            },
            {
                "step": 5,
                "name": "Adaptive arbitrage",
                "detail": f"Приоритет потока: {arbitrage_winner or 'labeling (по умолчанию)'}",
            },
        ],
        "legacy_queue": [{"adapter": a, "company": c} for a, c in legacy_tasks[:8]],
        "note": "В dry_run деньги не на счёт — только [DRY RUN] Potential profit в консоли",
    }
