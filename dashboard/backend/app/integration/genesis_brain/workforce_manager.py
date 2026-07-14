"""Workforce Manager — Planner-driven task routing (single analyze_turn per turn)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.genesis_brain.workforce_director import (
    WorkforceDirector,
    WorkforcePlan,
    WorkforceTask,
)
from app.integration.genesis_brain.workforce_performance import EmployeeScoreBreakdown

_PREMIUM_EMPLOYEES = frozenset({"openai", "anthropic"})


class WorkforceManager:
    """Facade — task classification + Workforce Director dispatch."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory_dir = memory_dir
        self._director = WorkforceDirector(memory_dir)

    def classify_task(
        self,
        last_user: str,
        thinking: Any,
        *,
        executive_action: str = "answer",
        messages: list[dict[str, str]] | None = None,
        has_attachments: bool = False,
        visitor_id: str | None = None,
        memory_dir: Path | None = None,
    ) -> WorkforceTask:
        from app.integration.vector_intelligence.client_life_context import build_client_life_context
        from app.integration.vector_intelligence.pipeline import analyze_turn

        life = None
        vid = (visitor_id or "").strip()[:64]
        mem = memory_dir or self._memory_dir
        if vid and mem:
            life = build_client_life_context(vid, memory_dir=mem)

        analysis = analyze_turn(
            last_user,
            history=messages,
            life=life,
            has_attachments=has_attachments,
        )
        return analysis.workforce_task

    def plan(
        self,
        last_user: str,
        thinking: Any,
        *,
        executive_action: str = "answer",
        premium_allowed: bool = False,
        available_employees: list[str] | None = None,
        preferred_employees: list[str] | None = None,
        messages: list[dict[str, str]] | None = None,
        has_attachments: bool = False,
        workforce_task: WorkforceTask | None = None,
        visitor_id: str | None = None,
        memory_dir: Path | None = None,
    ) -> WorkforcePlan:
        task = workforce_task or self.classify_task(
            last_user,
            thinking,
            executive_action=executive_action,
            messages=messages,
            has_attachments=has_attachments,
            visitor_id=visitor_id,
            memory_dir=memory_dir,
        )
        return self._director.plan(
            task,
            premium_allowed=premium_allowed,
            available_employees=available_employees,
            preferred_employees=preferred_employees,
        )

    def record_success(self, employee_id: str) -> None:
        self._director.record_success(employee_id)

    def on_rate_limit(self, employee_id: str) -> None:
        self._director.on_rate_limit(employee_id)

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
        return self._director.record_outcome(
            employee_id,
            task,
            latency_ms=latency_ms,
            calibration_passed=calibration_passed,
            rewritten_heavily=rewritten_heavily,
            error=error,
        )

    def quota_snapshot(self) -> dict[str, dict[str, int]]:
        return self._director.quota_snapshot()

    def performance_snapshot(self) -> dict[str, Any]:
        return self._director.performance_snapshot()

    def director_snapshot(self) -> dict[str, Any]:
        return self._director.director_snapshot()

    def sort_providers(self, providers: list[Any], plan: WorkforcePlan) -> list[Any]:
        by_id = {getattr(p, "provider_id", ""): p for p in providers}
        ordered: list[Any] = []
        for eid in plan.employee_order:
            p = by_id.get(eid)
            if p is not None:
                ordered.append(p)
        for p in providers:
            if p not in ordered:
                ordered.append(p)
        return ordered

    def explain_not_chosen(
        self,
        plan: WorkforcePlan,
        chosen_id: str,
        *,
        available_employees: list[str],
    ) -> list[dict[str, Any]]:
        score_by_id = {s.employee_id: s for s in plan.scores}
        chosen_score = score_by_id[chosen_id].total if chosen_id in score_by_id else None
        out: list[dict[str, Any]] = []
        for eid in available_employees:
            if eid == chosen_id:
                continue
            s = score_by_id.get(eid)
            if s is None:
                out.append(
                    {
                        "employee_id": eid,
                        "score": None,
                        "why": "нет бюджета / недоступен / Director исключил",
                    }
                )
                continue
            if s.quota_remaining <= 0 and eid != "genesis-local":
                why = "дневной лимит исчерпан"
            elif chosen_score is not None and s.total < chosen_score:
                why = f"ниже Director Score ({s.total:.0f} < {chosen_score:.0f})"
            else:
                why = "не выбран после эскалации"
            out.append(
                {
                    "employee_id": eid,
                    "score": round(s.total, 1),
                    "quality": round(s.quality, 1),
                    "quota_remaining": s.quota_remaining,
                    "why": why,
                }
            )
        return out

    def score_for(self, plan: WorkforcePlan, employee_id: str) -> float | None:
        return self._director.score_for(plan, employee_id)
