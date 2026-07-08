"""Daily quota tracking for AI Workforce employees (free-tier limits)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent.parent.parent / "memory"

# Conservative defaults — override via workforce_config.json
DEFAULT_LIMITS: dict[str, int] = {
    "groq": 14_400,
    "gemini": 1_500,
    "openrouter": 200,
    "anthropic": 100,
    "openai": 50,
    "deepseek": 500,
    "ollama": 100_000,
    "genesis-local": 100_000,
}


class WorkforceQuotas:
    """Per-employee daily counters — Genesis picks who still has budget."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        root = (memory_dir or _DEFAULT_MEMORY) / "workforce"
        root.mkdir(parents=True, exist_ok=True)
        self._path = root / "quotas.json"
        self._config_path = root / "config.json"
        self._limits = self._load_limits()

    def _load_limits(self) -> dict[str, int]:
        limits = dict(DEFAULT_LIMITS)
        if self._config_path.is_file():
            try:
                cfg = json.loads(self._config_path.read_text(encoding="utf-8"))
                for k, v in (cfg.get("daily_limits") or {}).items():
                    limits[str(k)] = int(v)
            except (json.JSONDecodeError, OSError, TypeError, ValueError):
                pass
        return limits

    def _load(self) -> dict[str, Any]:
        today = date.today().isoformat()
        if not self._path.is_file():
            return {"date": today, "used": {}}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if data.get("date") != today:
                return {"date": today, "used": {}}
            return data
        except (json.JSONDecodeError, OSError):
            return {"date": today, "used": {}}

    def _save(self, data: dict[str, Any]) -> None:
        try:
            self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def remaining(self, employee_id: str) -> int:
        limit = self._limits.get(employee_id, 0)
        if limit <= 0:
            return 0
        data = self._load()
        used = int((data.get("used") or {}).get(employee_id, 0))
        return max(0, limit - used)

    def has_budget(self, employee_id: str) -> bool:
        limit = self._limits.get(employee_id)
        if limit is None:
            return True
        return self.remaining(employee_id) > 0

    def limit_for(self, employee_id: str) -> int:
        return int(self._limits.get(employee_id, 0))

    def exhaust(self, employee_id: str) -> None:
        """Provider returned 429 — treat daily budget as spent for failover."""
        limit = self.limit_for(employee_id)
        if limit <= 0:
            return
        data = self._load()
        used: dict[str, int] = dict(data.get("used") or {})
        used[employee_id] = limit
        data["used"] = used
        self._save(data)

    def record(self, employee_id: str) -> None:
        data = self._load()
        used: dict[str, int] = dict(data.get("used") or {})
        used[employee_id] = int(used.get(employee_id, 0)) + 1
        data["used"] = used
        self._save(data)

    def snapshot(self) -> dict[str, dict[str, int]]:
        """For dev/debug — remaining budget per employee."""
        data = self._load()
        used_map: dict[str, int] = dict(data.get("used") or {})
        out: dict[str, dict[str, int]] = {}
        for emp, limit in self._limits.items():
            used = used_map.get(emp, 0)
            out[emp] = {"used": used, "limit": limit, "remaining": max(0, limit - used)}
        return out
