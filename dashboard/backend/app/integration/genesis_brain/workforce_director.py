"""
Workforce Director — multi-provider failover, quota-aware dispatch, learned quality.

Not «Groq first» — «who is best for this task right now?»
Failover chain (automatic, invisible to user):
  Groq → Gemini → OpenRouter → Ollama → Genesis Local
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.integration.genesis_brain.workforce_performance import (
    EmployeeScoreBreakdown,
    WorkforcePerformance,
    WorkforceTask,
)
from app.integration.genesis_brain.workforce_quotas import WorkforceQuotas

WorkforceTask = WorkforceTask

_FAILOVER_CHAIN: tuple[str, ...] = (
    "groq",
    "gemini",
    "openrouter",
    "ollama",
    "genesis-local",
)

_PREMIUM = frozenset({"openai", "anthropic", "deepseek"})

_ALL = (
    "groq",
    "gemini",
    "openrouter",
    "ollama",
    "openai",
    "anthropic",
    "deepseek",
    "genesis-local",
)


@dataclass(frozen=True)
class WorkforcePlan:
    task: WorkforceTask
    employee_order: tuple[str, ...]
    scores: tuple[EmployeeScoreBreakdown, ...]
    selected: str
    reason: str
    failover_chain: tuple[str, ...] = _FAILOVER_CHAIN


class WorkforceDirector:
    """Director layer — quotas, success rate, specialization, auto-exclude."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._quotas = WorkforceQuotas(memory_dir)
        self._performance = WorkforcePerformance(memory_dir)

    def plan(
        self,
        task: WorkforceTask,
        *,
        premium_allowed: bool = False,
        available_employees: list[str] | None = None,
    ) -> WorkforcePlan:
        candidates = list(available_employees or _ALL)
        if not premium_allowed:
            candidates = [e for e in candidates if e not in _PREMIUM]

        # Only employees with quota budget (Director excludes exhausted providers)
        with_budget = [e for e in candidates if self._quotas.has_budget(e)]
        if not with_budget:
            with_budget = ["genesis-local"]

        ranked = self._performance.rank_employees(task, with_budget)
        order = tuple(s.employee_id for s in ranked)
        selected = order[0] if order else "genesis-local"
        top = ranked[0] if ranked else None

        if top:
            reason = (
                f"Director: task={task}; best={top.employee_id} score={top.total:.0f} "
                f"(q={top.quality:.0f} quota={top.quota_remaining} success={top.success_rate:.0f}%)"
            )
        else:
            reason = f"task={task}; fallback=genesis-local"

        return WorkforcePlan(
            task=task,
            employee_order=order,
            scores=tuple(ranked),
            selected=selected,
            reason=reason,
            failover_chain=_FAILOVER_CHAIN,
        )

    def on_rate_limit(self, employee_id: str) -> None:
        """429 from provider — mark exhausted, Director picks next on retry."""
        self._quotas.exhaust(employee_id)

    def quota_snapshot(self) -> dict[str, dict[str, int]]:
        return self._quotas.snapshot()

    def performance_snapshot(self) -> dict[str, Any]:
        return {
            "today": self._performance.daily_snapshot(),
            "learned_ratings": self._performance.ratings_snapshot(),
        }

    def record_success(self, employee_id: str) -> None:
        self._quotas.record(employee_id)

    def record_outcome(self, employee_id: str, task: str, **kwargs: Any) -> float:
        return self._performance.record_outcome(employee_id, task, **kwargs)

    def score_for(self, plan: WorkforcePlan, employee_id: str) -> float | None:
        for s in plan.scores:
            if s.employee_id == employee_id:
                return s.total
        return None

    def director_snapshot(self) -> dict[str, Any]:
        quotas = self._quotas.snapshot()
        chain_status: list[dict[str, Any]] = []
        for eid in _FAILOVER_CHAIN:
            q = quotas.get(eid, {})
            chain_status.append(
                {
                    "employee_id": eid,
                    "remaining": q.get("remaining", 0),
                    "limit": q.get("limit", 0),
                    "has_budget": self._quotas.has_budget(eid),
                }
            )
        return {
            "failover_chain": list(_FAILOVER_CHAIN),
            "chain_status": chain_status,
            "policy": (
                "Genesis Director picks best score per task. "
                "When quota runs out or provider errors, next employee in chain — user sees only Genesis."
            ),
            "learning": "Good dialogues saved to training_candidates.jsonl for future local improvement.",
        }
