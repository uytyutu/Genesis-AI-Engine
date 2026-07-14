"""Self-healing loop — disable unprofitable adapters/nodes automatically."""

from __future__ import annotations

from typing import Any

from swarm.farm_learning import FarmLearningLedger
from swarm.node_monitor import NodeMonitor

DEFAULT_MIN_EUR_PER_HOUR = 0.01


def _adapter_eur_per_hour(ledger: FarmLearningLedger, adapter_id: str) -> float:
    for row in ledger.adapter_stats():
        if row["adapter_id"] == adapter_id:
            return round(float(row["eur_per_second"]) * 3600, 6)
    return 0.0


class SelfHealingLoop:
    """If ROI drops below threshold — pause adapter and log action."""

    def __init__(self, *, min_eur_per_hour: float = DEFAULT_MIN_EUR_PER_HOUR) -> None:
        self._min_rate = max(0.0, float(min_eur_per_hour))

    def evaluate(
        self,
        ledger: FarmLearningLedger,
        nodes: NodeMonitor,
        *,
        disabled_adapters: set[str] | None = None,
        disabled_nodes: set[str] | None = None,
    ) -> dict[str, Any]:
        disabled_adapters = set(disabled_adapters or set())
        disabled_nodes = set(disabled_nodes or set())
        actions: list[dict[str, Any]] = []
        healed: list[dict[str, Any]] = []

        if not ledger.ready():
            return {
                "active": False,
                "reason": f"Нужно ≥{ledger.snapshot()['min_ops_for_priority']} ops для self-healing",
                "actions": actions,
                "disabled_adapters": sorted(disabled_adapters),
                "disabled_nodes": sorted(disabled_nodes),
            }

        for row in ledger.adapter_stats():
            adapter_id = str(row["adapter_id"])
            rate = float(row["eur_per_second"]) * 3600
            count = int(row["count"])
            if count < 5:
                continue
            if rate < self._min_rate and adapter_id not in disabled_adapters:
                disabled_adapters.add(adapter_id)
                actions.append(
                    {
                        "action": "disable_adapter",
                        "target": adapter_id,
                        "eur_per_hour": round(rate, 4),
                        "threshold": self._min_rate,
                        "reason": "Доходность ниже порога рентабельности",
                    }
                )
            elif rate >= self._min_rate * 1.5 and adapter_id in disabled_adapters:
                disabled_adapters.discard(adapter_id)
                healed.append(
                    {
                        "action": "enable_adapter",
                        "target": adapter_id,
                        "eur_per_hour": round(rate, 4),
                        "reason": "Доходность восстановилась",
                    }
                )

        node_snap = nodes.snapshot()
        node_rate = float(node_snap.get("projected_eur_per_hour") or 0)
        if node_snap.get("effective_nodes", 0) > 0 and node_rate < self._min_rate:
            for node in node_snap.get("nodes") or []:
                nid = str(node.get("id") or "")
                if nid and nid not in disabled_nodes:
                    disabled_nodes.add(nid)
                    actions.append(
                        {
                            "action": "disable_node",
                            "target": nid,
                            "eur_per_hour": node_rate,
                            "threshold": self._min_rate,
                            "reason": "Пассивная нода нерентабельна",
                        }
                    )

        return {
            "active": True,
            "min_eur_per_hour": self._min_rate,
            "actions": actions,
            "healed": healed,
            "disabled_adapters": sorted(disabled_adapters),
            "disabled_nodes": sorted(disabled_nodes),
            "note": (
                "Self-healing: невыгодные комбайны отключены автоматически"
                if actions
                else "Все активные потоки выше порога рентабельности"
            ),
        }
