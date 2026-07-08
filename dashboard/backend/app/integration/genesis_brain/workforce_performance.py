"""
Employee Performance — learned ratings, daily history, Employee Score (0–100).

Genesis law: no model is best forever. Scores update after every calibration outcome.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Literal

from app.integration.genesis_brain.workforce_quotas import WorkforceQuotas

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent.parent.parent / "memory"

WorkforceTask = Literal["code", "search", "conversation", "simple", "complex", "sales"]

# Baseline quality per task (0–10) — starting priors, overridden by learned stats
_BASELINE_QUALITY: dict[str, dict[str, float]] = {
    "code": {
        "anthropic": 9.8,
        "openai": 9.5,
        "deepseek": 8.8,
        "groq": 8.0,
        "gemini": 8.2,
        "openrouter": 8.0,
        "ollama": 6.5,
        "genesis-local": 5.0,
    },
    "search": {
        "gemini": 9.5,
        "openai": 9.2,
        "anthropic": 8.8,
        "groq": 8.0,
        "openrouter": 8.5,
        "deepseek": 8.0,
        "ollama": 6.0,
        "genesis-local": 5.0,
    },
    "conversation": {
        "groq": 8.7,
        "gemini": 9.0,
        "anthropic": 9.2,
        "openai": 9.3,
        "openrouter": 8.5,
        "deepseek": 8.5,
        "ollama": 7.0,
        "genesis-local": 6.0,
    },
    "simple": {
        "ollama": 8.5,
        "groq": 9.0,
        "gemini": 8.5,
        "openrouter": 8.0,
        "anthropic": 8.5,
        "openai": 8.5,
        "genesis-local": 7.5,
    },
    "sales": {
        "gemini": 9.2,
        "openai": 9.4,
        "anthropic": 9.3,
        "groq": 8.5,
        "openrouter": 8.5,
        "deepseek": 8.5,
        "ollama": 6.5,
        "genesis-local": 6.5,
    },
    "complex": {
        "openai": 9.9,
        "anthropic": 9.8,
        "gemini": 9.2,
        "deepseek": 8.8,
        "groq": 8.0,
        "openrouter": 8.5,
        "ollama": 6.0,
        "genesis-local": 5.5,
    },
}

_SPEED: dict[str, float] = {
    "groq": 10.0,
    "gemini": 8.0,
    "anthropic": 8.0,
    "openai": 7.0,
    "deepseek": 8.5,
    "openrouter": 7.5,
    "ollama": 6.0,
    "genesis-local": 9.0,
}

_COST: dict[str, float] = {
    "groq": 10.0,
    "gemini": 10.0,
    "ollama": 10.0,
    "openrouter": 9.0,
    "deepseek": 9.5,
    "anthropic": 5.0,
    "openai": 4.0,
    "genesis-local": 10.0,
}


@dataclass(frozen=True)
class EmployeeScoreBreakdown:
    employee_id: str
    total: float
    quality: float
    speed: float
    cost: float
    availability: float
    success_rate: float = 85.0
    quota_remaining: int = 0
    quota_limit: int = 0
    learned_quality: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "total": round(self.total, 1),
            "quality": round(self.quality, 1),
            "speed": round(self.speed, 1),
            "cost": round(self.cost, 1),
            "availability": round(self.availability, 1),
            "success_rate": round(self.success_rate, 1),
            "quota_remaining": self.quota_remaining,
            "quota_limit": self.quota_limit,
            "learned_quality": self.learned_quality,
        }


@dataclass
class _EmpStats:
    requests: int = 0
    errors: int = 0
    latency_sum_ms: float = 0.0
    quality_sum: float = 0.0
    quality_count: int = 0
    by_task: dict[str, dict[str, float]] = field(default_factory=dict)

    def avg_latency_ms(self) -> float:
        return self.latency_sum_ms / self.requests if self.requests else 0.0

    def avg_quality(self) -> float:
        return self.quality_sum / self.quality_count if self.quality_count else 0.0


class WorkforcePerformance:
    """Tracks employee quality over time — Employee Score, not fixed priority lists."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        root = (memory_dir or _DEFAULT_MEMORY) / "workforce"
        root.mkdir(parents=True, exist_ok=True)
        self._ratings_path = root / "employee_ratings.json"
        self._daily_path = root / "daily_stats.json"
        self._quotas = WorkforceQuotas(memory_dir)

    def _load_ratings(self) -> dict[str, Any]:
        if not self._ratings_path.is_file():
            return {"employees": {}}
        try:
            data = json.loads(self._ratings_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"employees": {}}
        except (json.JSONDecodeError, OSError):
            return {"employees": {}}

    def _save_ratings(self, data: dict[str, Any]) -> None:
        try:
            self._ratings_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass

    def _load_daily(self) -> dict[str, Any]:
        today = date.today().isoformat()
        if not self._daily_path.is_file():
            return {"date": today, "employees": {}}
        try:
            data = json.loads(self._daily_path.read_text(encoding="utf-8"))
            if data.get("date") != today:
                return {"date": today, "employees": {}}
            return data
        except (json.JSONDecodeError, OSError):
            return {"date": today, "employees": {}}

    def _save_daily(self, data: dict[str, Any]) -> None:
        try:
            self._daily_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass

    def learned_quality(self, employee_id: str, task: str) -> float | None:
        data = self._load_ratings()
        emp = (data.get("employees") or {}).get(employee_id) or {}
        by_task = emp.get("by_task") or {}
        bucket = by_task.get(task)
        if not bucket:
            global_b = emp.get("global")
            if global_b and global_b.get("count", 0) >= 5:
                return float(global_b["sum"]) / float(global_b["count"])
            return None
        count = int(bucket.get("count", 0))
        if count < 3:
            return None
        return float(bucket["sum"]) / float(count)

    def _today_success_rate(self, employee_id: str) -> float:
        row = (self._load_daily().get("employees") or {}).get(employee_id) or {}
        reqs = int(row.get("requests", 0))
        errs = int(row.get("errors", 0))
        if reqs < 3:
            return 85.0
        return max(20.0, min(100.0, ((reqs - errs) / reqs) * 100.0))

    def score_employee(self, employee_id: str, task: WorkforceTask) -> EmployeeScoreBreakdown:
        baseline = (_BASELINE_QUALITY.get(task) or {}).get(employee_id, 7.5)
        learned = self.learned_quality(employee_id, task)
        if learned is not None:
            quality_10 = 0.55 * learned + 0.45 * baseline
        else:
            quality_10 = baseline

        speed_10 = _SPEED.get(employee_id, 7.0)
        cost_10 = _COST.get(employee_id, 7.0)
        limit = self._quotas.limit_for(employee_id)
        remaining = self._quotas.remaining(employee_id)
        if employee_id == "genesis-local":
            avail = 100.0
        elif limit <= 0:
            avail = 100.0 if self._quotas.has_budget(employee_id) else 0.0
        else:
            avail = 0.0 if remaining <= 0 else min(100.0, (remaining / limit) * 100.0)

        success = self._today_success_rate(employee_id)

        q100 = quality_10 * 10.0
        s100 = speed_10 * 10.0
        c100 = cost_10 * 10.0
        # Workforce Director weights: quality, speed, cost, quota headroom, success rate
        total = (
            0.35 * q100
            + 0.18 * s100
            + 0.07 * c100
            + 0.22 * avail
            + 0.18 * success
        )

        return EmployeeScoreBreakdown(
            employee_id=employee_id,
            total=total,
            quality=q100,
            speed=s100,
            cost=c100,
            availability=avail,
            success_rate=success,
            quota_remaining=remaining,
            quota_limit=limit,
            learned_quality=learned,
        )

    def rank_employees(
        self,
        task: WorkforceTask,
        candidate_ids: list[str],
    ) -> list[EmployeeScoreBreakdown]:
        scores = [self.score_employee(eid, task) for eid in candidate_ids]
        scores.sort(key=lambda s: s.total, reverse=True)
        return scores

    def record_outcome(
        self,
        employee_id: str,
        task: str,
        *,
        latency_ms: float,
        calibration_passed: bool,
        rewritten_heavily: bool = False,
        error: bool = False,
    ) -> float:
        """Update ratings after Genesis Calibration. Returns quality delta applied."""
        if error:
            delta = -1.5
        elif rewritten_heavily:
            delta = -2.0
        elif calibration_passed:
            delta = +1.0
        else:
            delta = -1.0

        self._apply_rating_delta(employee_id, task, delta)
        self._update_daily(employee_id, latency_ms, delta, error=error)
        return delta

    def _apply_rating_delta(self, employee_id: str, task: str, delta: float) -> None:
        data = self._load_ratings()
        employees: dict[str, Any] = dict(data.get("employees") or {})
        emp = dict(employees.get(employee_id) or {})
        global_b = dict(emp.get("global") or {"sum": 70.0, "count": 10})
        by_task: dict[str, Any] = dict(emp.get("by_task") or {})

        current_global = (
            float(global_b["sum"]) / float(global_b["count"])
            if global_b.get("count")
            else 7.0
        )
        new_global = max(5.0, min(10.0, current_global + delta * 0.15))
        global_b["sum"] = float(global_b.get("sum", 70.0)) + new_global
        global_b["count"] = int(global_b.get("count", 10)) + 1

        bucket = dict(by_task.get(task) or {"sum": 0.0, "count": 0})
        if bucket["count"]:
            current = float(bucket["sum"]) / float(bucket["count"])
        else:
            current = (_BASELINE_QUALITY.get(task) or {}).get(employee_id, 7.5)
        new_q = max(5.0, min(10.0, current + delta * 0.25))
        bucket["sum"] = float(bucket.get("sum", 0)) + new_q
        bucket["count"] = int(bucket.get("count", 0)) + 1

        by_task[task] = bucket
        emp["global"] = global_b
        emp["by_task"] = by_task
        employees[employee_id] = emp
        data["employees"] = employees
        self._save_ratings(data)

    def _update_daily(
        self,
        employee_id: str,
        latency_ms: float,
        quality_delta: float,
        *,
        error: bool,
    ) -> None:
        data = self._load_daily()
        employees: dict[str, Any] = dict(data.get("employees") or {})
        row = dict(employees.get(employee_id) or {})
        row["requests"] = int(row.get("requests", 0)) + 1
        row["latency_sum_ms"] = float(row.get("latency_sum_ms", 0)) + latency_ms
        if error:
            row["errors"] = int(row.get("errors", 0)) + 1
        q_sum = float(row.get("quality_sum", 0))
        q_count = int(row.get("quality_count", 0))
        baseline = 7.5 + quality_delta
        row["quality_sum"] = q_sum + max(5.0, min(10.0, baseline))
        row["quality_count"] = q_count + 1
        employees[employee_id] = row
        data["employees"] = employees
        self._save_daily(data)

    def daily_snapshot(self) -> dict[str, dict[str, Any]]:
        """Today's employee history for dev / owner."""
        data = self._load_daily()
        out: dict[str, dict[str, Any]] = {}
        for emp, row in (data.get("employees") or {}).items():
            reqs = int(row.get("requests", 0))
            lat_sum = float(row.get("latency_sum_ms", 0))
            q_sum = float(row.get("quality_sum", 0))
            q_count = int(row.get("quality_count", 0))
            out[emp] = {
                "requests": reqs,
                "errors": int(row.get("errors", 0)),
                "avg_latency_sec": round(lat_sum / reqs / 1000, 2) if reqs else 0,
                "avg_quality": round(q_sum / q_count, 2) if q_count else None,
            }
        return out

    def ratings_snapshot(self) -> dict[str, Any]:
        data = self._load_ratings()
        return data.get("employees") or {}


class LatencyTimer:
    def __init__(self) -> None:
        self._start = 0.0

    def __enter__(self) -> LatencyTimer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    @property
    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self._start) * 1000.0
