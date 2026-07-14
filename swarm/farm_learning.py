"""Farm learning ledger — tracks ROI per combiner and prioritizes profitable work."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MIN_OPS_FOR_PRIORITY = 100

_DEFAULT: dict[str, Any] = {
    "total_ops": 0,
    "adapters": {},
}


class FarmLearningLedger:
    """Records pay vs LLM cost vs time — after 100 ops picks «bread» task types."""

    def __init__(self, memory_dir: Path) -> None:
        self._path = Path(memory_dir) / "micro_farm_learning.json"

    def _load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return dict(_DEFAULT)
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            merged = dict(_DEFAULT)
            merged.update(data)
            return merged
        except (json.JSONDecodeError, OSError):
            return dict(_DEFAULT)

    def _save(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def record(
        self,
        *,
        adapter_id: str,
        pay_eur: float,
        llm_cost_eur: float = 0.0,
        duration_ms: float = 0.0,
        cached: bool = False,
    ) -> None:
        data = self._load()
        adapters = data.setdefault("adapters", {})
        row = dict(
            adapters.get(adapter_id)
            or {
                "count": 0,
                "total_pay_eur": 0.0,
                "total_llm_cost_eur": 0.0,
                "total_duration_ms": 0.0,
                "cache_hits": 0,
            }
        )
        row["count"] = int(row.get("count") or 0) + 1
        row["total_pay_eur"] = round(float(row.get("total_pay_eur") or 0) + pay_eur, 6)
        row["total_llm_cost_eur"] = round(float(row.get("total_llm_cost_eur") or 0) + llm_cost_eur, 6)
        row["total_duration_ms"] = round(float(row.get("total_duration_ms") or 0) + duration_ms, 2)
        if cached:
            row["cache_hits"] = int(row.get("cache_hits") or 0) + 1
        adapters[adapter_id] = row
        data["total_ops"] = int(data.get("total_ops") or 0) + 1
        self._save(data)

    def adapter_stats(self) -> list[dict[str, Any]]:
        data = self._load()
        out: list[dict[str, Any]] = []
        for adapter_id, row in (data.get("adapters") or {}).items():
            count = max(1, int(row.get("count") or 0))
            pay = float(row.get("total_pay_eur") or 0)
            cost = float(row.get("total_llm_cost_eur") or 0)
            ms = float(row.get("total_duration_ms") or 0) or 1.0
            net = pay - cost
            out.append(
                {
                    "adapter_id": adapter_id,
                    "count": count,
                    "net_profit_eur": round(net, 4),
                    "avg_net_eur": round(net / count, 4),
                    "eur_per_second": round(net / (ms / 1000), 6),
                    "cache_hits": int(row.get("cache_hits") or 0),
                    "cache_rate": round(int(row.get("cache_hits") or 0) / count, 3),
                }
            )
        out.sort(key=lambda r: r["eur_per_second"], reverse=True)
        return out

    def ready(self) -> bool:
        return int(self._load().get("total_ops") or 0) >= MIN_OPS_FOR_PRIORITY

    def recommend_order(self, fallback: tuple[str, ...]) -> tuple[str, ...]:
        stats = self.adapter_stats()
        if not self.ready() or not stats:
            return fallback
        ranked = [s["adapter_id"] for s in stats]
        tail = [a for a in fallback if a not in ranked]
        return tuple(ranked + tail)

    def snapshot(self) -> dict[str, Any]:
        stats = self.adapter_stats()
        top = stats[0] if stats else None
        return {
            "total_ops": int(self._load().get("total_ops") or 0),
            "min_ops_for_priority": MIN_OPS_FOR_PRIORITY,
            "investor_mode": self.ready(),
            "top_adapter": top["adapter_id"] if top else None,
            "top_eur_per_second": top["eur_per_second"] if top else 0.0,
            "adapters": stats,
            "note": (
                "Ферма сама выбирает самые выгодные комбайны"
                if self.ready()
                else f"Самообучение: {int(self._load().get('total_ops') or 0)}/{MIN_OPS_FOR_PRIORITY} операций"
            ),
        }
