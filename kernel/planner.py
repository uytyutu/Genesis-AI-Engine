from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from kernel.task import Task


@dataclass(frozen=True)
class PlanStep:
    agent_id: str
    action: str
    input: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    task_id: str
    steps: list[PlanStep] = field(default_factory=list)


class Planner(Protocol):
    def plan(self, task: Task) -> Plan: ...


class SimplePlanner:
    """
    Kernel-default planner.

    Task payload formats:
    - {"steps": [{"agent_id", "action", "input"?}, ...]}
    - {"agent_id", "action", "input"?}  → single step
    """

    def plan(self, task: Task) -> Plan:
        payload = task.payload

        if "steps" in payload:
            steps = [_step_from_dict(raw) for raw in payload["steps"]]
            if not steps:
                raise ValueError("steps must not be empty")
            return Plan(task_id=task.id, steps=steps)

        if "agent_id" in payload and "action" in payload:
            step = PlanStep(
                agent_id=str(payload["agent_id"]),
                action=str(payload["action"]),
                input=dict(payload.get("input") or {}),
            )
            return Plan(task_id=task.id, steps=[step])

        raise ValueError(
            "task payload must include either 'steps' or ('agent_id' + 'action')"
        )


def _step_from_dict(raw: dict[str, Any]) -> PlanStep:
    if "agent_id" not in raw or "action" not in raw:
        raise ValueError("each step requires agent_id and action")
    return PlanStep(
        agent_id=str(raw["agent_id"]),
        action=str(raw["action"]),
        input=dict(raw.get("input") or {}),
    )
