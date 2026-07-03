from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from kernel.agent import AgentRegistry
from kernel.planner import Planner, SimplePlanner
from kernel.task import StepContext, StepResult, Task, TaskResult, TaskStatus


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class GenesisKernel:
    """
    Genesis Kernel — four responsibilities only:

    1. Accept a task
    2. Plan
    3. Run agents
    4. Return a result
    """

    registry: AgentRegistry
    planner: Planner = field(default_factory=SimplePlanner)
    _log: list[dict[str, Any]] = field(default_factory=list, repr=False)

    def submit(self, task: Task) -> TaskResult:
        task_started = time.perf_counter()
        task_started_at = _utc_now()
        self._record("task.accepted", task_id=task.id, name=task.name)

        try:
            plan = self.planner.plan(task)
        except Exception as exc:  # noqa: BLE001 — kernel boundary
            finished_at = _utc_now()
            duration_ms = (time.perf_counter() - task_started) * 1000
            self._record(
                "plan.failed",
                task_id=task.id,
                error=str(exc),
                duration_ms=round(duration_ms, 2),
            )
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=f"planning failed: {exc}",
                duration_ms=round(duration_ms, 2),
                started_at=task_started_at,
                finished_at=finished_at,
            )

        self._record(
            "plan.created",
            task_id=task.id,
            steps=[_step_dict(s) for s in plan.steps],
        )

        step_results: list[StepResult] = []
        merged_output: dict[str, Any] = {"task_name": task.name}
        previous_outputs: list[dict[str, Any]] = []

        if task.goal is not None:
            merged_output["goal"] = str(task.goal)

        for index, step in enumerate(plan.steps):
            step_started = time.perf_counter()
            step_started_at = _utc_now()
            self._record(
                "agent.start",
                task_id=task.id,
                step=index,
                agent_id=step.agent_id,
                action=step.action,
            )

            context = StepContext(
                task_id=task.id,
                task_name=task.name,
                step_index=index,
                goal=task.goal,
                previous_outputs=tuple(previous_outputs),
            )

            try:
                agent = self.registry.get(step.agent_id)
                output = agent.run(step.action, dict(step.input), context)
                step_duration_ms = (time.perf_counter() - step_started) * 1000
                step_finished_at = _utc_now()
                result = StepResult(
                    agent_id=step.agent_id,
                    action=step.action,
                    success=True,
                    output=output,
                    duration_ms=round(step_duration_ms, 2),
                    started_at=step_started_at,
                    finished_at=step_finished_at,
                )
                previous_outputs.append(output)
                merged_output[f"step_{index}"] = output
                self._record(
                    "agent.done",
                    task_id=task.id,
                    step=index,
                    agent_id=step.agent_id,
                    action=step.action,
                    success=True,
                    duration_ms=result.duration_ms,
                )
            except Exception as exc:  # noqa: BLE001 — kernel boundary
                step_duration_ms = (time.perf_counter() - step_started) * 1000
                step_finished_at = _utc_now()
                result = StepResult(
                    agent_id=step.agent_id,
                    action=step.action,
                    success=False,
                    error=str(exc),
                    duration_ms=round(step_duration_ms, 2),
                    started_at=step_started_at,
                    finished_at=step_finished_at,
                )
                self._record(
                    "agent.failed",
                    task_id=task.id,
                    step=index,
                    agent_id=step.agent_id,
                    action=step.action,
                    success=False,
                    duration_ms=result.duration_ms,
                    error=str(exc),
                )
                step_results.append(result)
                task_duration_ms = (time.perf_counter() - task_started) * 1000
                finished_at = _utc_now()
                self._record(
                    "task.failed",
                    task_id=task.id,
                    duration_ms=round(task_duration_ms, 2),
                )
                return TaskResult(
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    plan_steps=[_step_dict(s) for s in plan.steps],
                    step_results=step_results,
                    output=merged_output,
                    error=f"step {index} failed: {exc}",
                    duration_ms=round(task_duration_ms, 2),
                    started_at=task_started_at,
                    finished_at=finished_at,
                )

            step_results.append(result)

        task_duration_ms = (time.perf_counter() - task_started) * 1000
        finished_at = _utc_now()
        self._record(
            "task.completed",
            task_id=task.id,
            duration_ms=round(task_duration_ms, 2),
        )
        return TaskResult(
            task_id=task.id,
            status=TaskStatus.COMPLETED,
            plan_steps=[_step_dict(s) for s in plan.steps],
            step_results=step_results,
            output=merged_output,
            duration_ms=round(task_duration_ms, 2),
            started_at=task_started_at,
            finished_at=finished_at,
        )

    @property
    def audit_log(self) -> list[dict[str, Any]]:
        return list(self._log)

    def _record(self, event: str, **fields: Any) -> None:
        self._log.append({"event": event, "at": _utc_now(), **fields})


def _step_dict(step) -> dict[str, Any]:
    return {"agent_id": step.agent_id, "action": step.action, "input": step.input}
