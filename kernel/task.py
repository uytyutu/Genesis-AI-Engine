from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from kernel.goal import Goal


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Unit of work submitted to the kernel."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    goal: Goal | None = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("task name must not be empty")


@dataclass(frozen=True)
class StepContext:
    """What each agent sees from earlier steps in the same task."""

    task_id: str
    task_name: str
    step_index: int
    goal: Goal | None
    previous_outputs: tuple[dict[str, Any], ...] = ()

    @property
    def previous(self) -> dict[str, Any] | None:
        if not self.previous_outputs:
            return None
        return self.previous_outputs[-1]


@dataclass
class StepResult:
    agent_id: str
    action: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0
    started_at: str = ""
    finished_at: str = ""


@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    plan_steps: list[dict[str, Any]] = field(default_factory=list)
    step_results: list[StepResult] = field(default_factory=list)
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0
    started_at: str = ""
    finished_at: str = ""

    @property
    def ok(self) -> bool:
        return self.status == TaskStatus.COMPLETED
