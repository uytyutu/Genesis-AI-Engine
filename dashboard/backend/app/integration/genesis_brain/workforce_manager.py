"""
AI Workforce Manager — delegates to Workforce Director (score + quota failover).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.integration.genesis_brain.workforce_director import (
    WorkforceDirector,
    WorkforcePlan,
    WorkforceTask,
)
from app.integration.genesis_brain.workforce_performance import EmployeeScoreBreakdown

_CODE = re.compile(
    r"\b(?:код|python|javascript|typescript|react|ошибк|exception|debug|"
    r"функци|class\s|import\s|api\s|sql|regex)\b",
    re.I,
)
_SEARCH = re.compile(
    r"\b(?:найди|поиск|новост|актуальн|что\s+происходит|google|"
    r"источник|ссылк|факт\s+о)\b",
    re.I,
)
_SALES = re.compile(
    r"\b(?:сайт|лендинг|заказ|под\s+ключ|цена|стоимость|бот|магазин|услуг)\b",
    re.I,
)

_PREMIUM_EMPLOYEES = frozenset({"openai", "anthropic"})


class WorkforceManager:
    """Facade — task classification + Workforce Director dispatch."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._director = WorkforceDirector(memory_dir)

    def classify_task(
        self,
        last_user: str,
        thinking: Any,
        *,
        executive_action: str = "answer",
    ) -> WorkforceTask:
        low = (last_user or "").strip().lower()
        if not low:
            return "conversation"

        if _CODE.search(low):
            return "code"
        if _SEARCH.search(low):
            return "search"
        if _SALES.search(low):
            return "sales"

        conf = float(getattr(thinking, "confidence", 0.5) or 0.5)
        if len(low) < 35 and "?" not in low and conf > 0.7:
            return "simple"
        if len(low) > 400 or conf < 0.42:
            return "complex"
        return "conversation"

    def plan(
        self,
        last_user: str,
        thinking: Any,
        *,
        executive_action: str = "answer",
        premium_allowed: bool = False,
        available_employees: list[str] | None = None,
    ) -> WorkforcePlan:
        task = self.classify_task(last_user, thinking, executive_action=executive_action)
        return self._director.plan(
            task,
            premium_allowed=premium_allowed,
            available_employees=available_employees,
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
