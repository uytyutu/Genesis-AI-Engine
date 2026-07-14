"""Node monitor — passive infrastructure income (uptime) tracking."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ENV_NODE_COUNT = "FARM_NODE_COUNT"
ENV_NODE_DAILY_USD = "FARM_NODE_DAILY_USD"


class NodeMonitor:
    """Tracks remote nodes — projected until real network payouts are wired."""

    def __init__(
        self,
        memory_dir: Path,
        *,
        env_getter: Callable[[str], str] | None = None,
    ) -> None:
        self._path = Path(memory_dir) / "micro_farm_nodes.json"
        self._env = env_getter or (lambda key: os.getenv(key, "").strip())

    def _load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return {"nodes": [], "last_probe_at": None}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"nodes": [], "last_probe_at": None}

    def _save(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def configured_count(self) -> int:
        raw = self._env(ENV_NODE_COUNT) or "0"
        try:
            return max(0, int(raw))
        except ValueError:
            return 0

    def usd_per_node_per_day(self) -> float:
        raw = self._env(ENV_NODE_DAILY_USD) or "0.07"
        try:
            return max(0.0, float(raw))
        except ValueError:
            return 0.07

    def register_heartbeat(self, *, node_id: str, region: str = "default", online: bool = True) -> None:
        data = self._load()
        nodes = [n for n in data.get("nodes", []) if n.get("id") != node_id]
        nodes.append(
            {
                "id": node_id,
                "region": region,
                "online": online,
                "last_seen": datetime.now(timezone.utc).isoformat(),
            }
        )
        data["nodes"] = nodes[-200:]
        data["last_probe_at"] = datetime.now(timezone.utc).isoformat()
        self._save(data)

    def snapshot(self) -> dict[str, Any]:
        data = self._load()
        live = [n for n in data.get("nodes", []) if n.get("online")]
        configured = self.configured_count()
        count = max(configured, len(live))
        usd_day = self.usd_per_node_per_day()
        eur_day = round(count * usd_day * 0.92, 4)
        return {
            "configured_nodes": configured,
            "live_nodes": len(live),
            "effective_nodes": count,
            "usd_per_node_per_day": usd_day,
            "projected_eur_per_day": eur_day,
            "projected_eur_per_hour": round(eur_day / 24.0, 4),
            "nodes": live[:20],
            "honesty": (
                "Пассивный доход — прогноз по FARM_NODE_COUNT. "
                "Реальные выплаты только после подключения сети."
            ),
            "env_vars": {ENV_NODE_COUNT: "число нод", ENV_NODE_DAILY_USD: "USD/нода/день"},
        }
