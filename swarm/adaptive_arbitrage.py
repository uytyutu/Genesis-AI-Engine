"""Adaptive arbitrage — shift resources to the higher €/hour stream."""

from __future__ import annotations

from typing import Any

from swarm.farm_learning import FarmLearningLedger


def _eur_per_hour_from_labeling(ledger: FarmLearningLedger) -> float:
    stats = ledger.adapter_stats()
    if not stats:
        return 0.0
    # Best adapter net €/sec → €/hour
    best = stats[0]["eur_per_second"]
    return round(float(best) * 3600, 4)


def compare_streams(
    *,
    labeling_eur_per_hour: float,
    node_eur_per_day: float,
) -> dict[str, Any]:
    node_eur_per_hour = node_eur_per_day / 24.0
    if labeling_eur_per_hour >= node_eur_per_hour:
        winner = "labeling"
        margin = labeling_eur_per_hour - node_eur_per_hour
    else:
        winner = "passive_nodes"
        margin = node_eur_per_hour - labeling_eur_per_hour
    total = labeling_eur_per_hour + node_eur_per_hour
    if total <= 0:
        alloc_labeling = 80
        alloc_nodes = 20
    elif winner == "labeling":
        alloc_labeling = min(95, max(55, int(100 * labeling_eur_per_hour / total)))
        alloc_nodes = 100 - alloc_labeling
    else:
        alloc_nodes = min(95, max(55, int(100 * node_eur_per_hour / total)))
        alloc_labeling = 100 - alloc_nodes
    return {
        "winner": winner,
        "labeling_eur_per_hour": round(labeling_eur_per_hour, 4),
        "node_eur_per_hour": round(node_eur_per_hour, 4),
        "node_eur_per_day": round(node_eur_per_day, 4),
        "margin_eur_per_hour": round(margin, 4),
        "allocation_labeling_pct": alloc_labeling,
        "allocation_nodes_pct": alloc_nodes,
        "decision": (
            f"Приоритет: {'разметка' if winner == 'labeling' else 'пассивные ноды'} "
            f"({max(alloc_labeling, alloc_nodes)}% мощности)"
        ),
    }


class AdaptiveArbitrage:
    """Uses live ledger + node monitor to pick the better hypothesis."""

    def decide(
        self,
        ledger: FarmLearningLedger,
        *,
        node_eur_per_day: float = 0.0,
        fallback_labeling_eur_per_hour: float = 0.0,
    ) -> dict[str, Any]:
        measured = _eur_per_hour_from_labeling(ledger)
        labeling_rate = measured if measured > 0 else fallback_labeling_eur_per_hour
        result = compare_streams(
            labeling_eur_per_hour=labeling_rate,
            node_eur_per_day=node_eur_per_day,
        )
        result["source"] = "measured" if measured > 0 else "fallback"
        result["ready"] = ledger.ready()
        return result
