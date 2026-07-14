"""Honest revenue forecast — math model, not a promise of income."""

from __future__ import annotations

from typing import Any

USD_TO_EUR = 0.92

# Ir's reference assumptions (tunable via API params).
DEFAULT_LABEL_PAY_USD = 0.05
DEFAULT_TASKS_PER_HOUR_PER_NODE = 5.0
DEFAULT_INFRA_USD_PER_DAY_50_NODES = 20.0
DEFAULT_NODE_PASSIVE_USD_PER_DAY = 0.07


def _usd_to_eur(usd: float) -> float:
    return round(usd * USD_TO_EUR, 4)


def forecast_labeling_swarm(
    *,
    nodes: int = 50,
    tasks_per_hour_per_node: float = DEFAULT_TASKS_PER_HOUR_PER_NODE,
    pay_usd_per_task: float = DEFAULT_LABEL_PAY_USD,
    hours: float = 10.0,
    infra_usd_per_day: float = DEFAULT_INFRA_USD_PER_DAY_50_NODES,
) -> dict[str, Any]:
    nodes = max(1, int(nodes))
    gross_usd = nodes * tasks_per_hour_per_node * pay_usd_per_task * hours
    infra_usd = infra_usd_per_day * (hours / 24.0)
    net_usd = max(0.0, gross_usd - infra_usd)
    return {
        "model": "labeling_swarm",
        "nodes": nodes,
        "tasks_per_hour_per_node": tasks_per_hour_per_node,
        "pay_usd_per_task": pay_usd_per_task,
        "hours": hours,
        "gross_usd": round(gross_usd, 2),
        "gross_eur": _usd_to_eur(gross_usd),
        "infra_usd": round(infra_usd, 2),
        "infra_eur": _usd_to_eur(infra_usd),
        "net_usd": round(net_usd, 2),
        "net_eur": _usd_to_eur(net_usd),
        "formula": "nodes × tasks/h × $/task × hours − infra",
    }


def forecast_passive_nodes(
    *,
    nodes: int = 500,
    usd_per_node_per_day: float = DEFAULT_NODE_PASSIVE_USD_PER_DAY,
) -> dict[str, Any]:
    nodes = max(0, int(nodes))
    gross_usd = nodes * usd_per_node_per_day
    return {
        "model": "passive_nodes",
        "nodes": nodes,
        "usd_per_node_per_day": usd_per_node_per_day,
        "gross_usd_per_day": round(gross_usd, 2),
        "gross_eur_per_day": _usd_to_eur(gross_usd),
        "formula": "nodes × $/node/day",
    }


def forecast_phases() -> list[dict[str, str]]:
    """Honest timeline — depends on market tasks and your keys."""
    return [
        {
            "phase": "week_1",
            "label": "Неделя 1 (тест)",
            "eur_per_day": "0",
            "note": "Настройка VPS, ключи бирж, отладка роя — дохода нет",
        },
        {
            "phase": "week_2",
            "label": "Неделя 2 (старт)",
            "eur_per_day": "5–10",
            "note": "Первая живая нода + Scale/Toloka при наличии задач",
        },
        {
            "phase": "month_1",
            "label": "Месяц 1 (масштаб)",
            "eur_per_day": "50–100+",
            "note": "Только если есть задачи на биржах и ≥50 нод в remote",
        },
    ]


def forecast_from_measured(
    *,
    measured_pay_eur_per_task: float,
    measured_tasks_per_hour: float,
    nodes: int,
    hours: float = 10.0,
    infra_usd_per_day: float = DEFAULT_INFRA_USD_PER_DAY_50_NODES,
) -> dict[str, Any]:
    """Blend Ir's model with YOUR battle-test numbers."""
    pay_usd = measured_pay_eur_per_task / USD_TO_EUR if measured_pay_eur_per_task else DEFAULT_LABEL_PAY_USD
    base = forecast_labeling_swarm(
        nodes=nodes,
        tasks_per_hour_per_node=measured_tasks_per_hour or DEFAULT_TASKS_PER_HOUR_PER_NODE,
        pay_usd_per_task=pay_usd,
        hours=hours,
        infra_usd_per_day=infra_usd_per_day * (nodes / 50.0),
    )
    base["source"] = "measured_blend"
    base["measured_pay_eur_per_task"] = round(measured_pay_eur_per_task, 4)
    base["measured_tasks_per_hour"] = round(measured_tasks_per_hour, 2)
    return base


def full_forecast(
    *,
    labeling_nodes: int = 50,
    passive_nodes: int = 0,
    measured_pay_eur_per_task: float = 0.0,
    measured_tasks_per_hour: float = 0.0,
) -> dict[str, Any]:
    labeling = (
        forecast_from_measured(
            measured_pay_eur_per_task=measured_pay_eur_per_task,
            measured_tasks_per_hour=measured_tasks_per_hour,
            nodes=labeling_nodes,
        )
        if measured_pay_eur_per_task > 0
        else forecast_labeling_swarm(nodes=labeling_nodes)
    )
    passive = forecast_passive_nodes(nodes=passive_nodes) if passive_nodes > 0 else None
    return {
        "disclaimer": (
            "Прогноз — математика при допущениях. Реальный доход = задачи на биржах × твои ключи × аптайм. "
            "Genesis не гарантирует € — только считает и оптимизирует."
        ),
        "labeling_swarm_10h": labeling,
        "labeling_swarm_per_day": forecast_labeling_swarm(nodes=labeling_nodes, hours=24.0),
        "passive_nodes": passive,
        "phases": forecast_phases(),
        "scaling_note": (
            "Доход ∝ числу нод в FARM_EXECUTION_MODE=remote. "
            "Мульти-регион и RL — после стабильного боевого теста 1 ноды."
        ),
    }
