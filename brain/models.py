from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from kernel.goal import Goal, GoalType
from kernel.task import Task


class TaskLifecycle(str, Enum):
    """Brain-side task lifecycle — separate from Kernel TaskStatus."""

    NEW = "new"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BrainEventType(str, Enum):
    """Internal events Brain emits (logged via AuditStorage in later steps)."""

    TASK_CREATED = "task.created"
    TASK_QUEUED = "task.queued"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def goal_to_dict(goal: Goal | None) -> dict[str, Any] | None:
    if goal is None:
        return None
    return {
        "type": goal.type.value,
        "target": goal.target,
        "unit": goal.unit,
        "horizon_days": goal.horizon_days,
    }


def goal_from_dict(data: dict[str, Any] | None) -> Goal | None:
    if data is None:
        return None
    return Goal(
        type=GoalType(data["type"]),
        target=float(data["target"]),
        unit=str(data["unit"]),
        horizon_days=data.get("horizon_days"),
    )


@dataclass
class QueuedTaskRecord:
    task_id: str
    task_name: str
    payload: dict[str, Any]
    goal: dict[str, Any] | None
    lifecycle: TaskLifecycle
    created_at: str
    updated_at: str

    @classmethod
    def from_task(
        cls,
        task: Task,
        *,
        lifecycle: TaskLifecycle = TaskLifecycle.NEW,
    ) -> QueuedTaskRecord:
        now = utc_now_iso()
        return cls(
            task_id=task.id,
            task_name=task.name,
            payload=dict(task.payload),
            goal=goal_to_dict(task.goal),
            lifecycle=lifecycle,
            created_at=now,
            updated_at=now,
        )

    def to_task(self) -> Task:
        return Task(
            id=self.task_id,
            name=self.task_name,
            payload=dict(self.payload),
            goal=goal_from_dict(self.goal),
        )

    def with_lifecycle(self, lifecycle: TaskLifecycle) -> QueuedTaskRecord:
        return QueuedTaskRecord(
            task_id=self.task_id,
            task_name=self.task_name,
            payload=dict(self.payload),
            goal=self.goal,
            lifecycle=lifecycle,
            created_at=self.created_at,
            updated_at=utc_now_iso(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "payload": self.payload,
            "goal": self.goal,
            "lifecycle": self.lifecycle.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueuedTaskRecord:
        return cls(
            task_id=str(data["task_id"]),
            task_name=str(data["task_name"]),
            payload=dict(data.get("payload") or {}),
            goal=data.get("goal"),
            lifecycle=TaskLifecycle(str(data["lifecycle"])),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
        )


def make_brain_event(
    event_type: BrainEventType,
    record: QueuedTaskRecord,
    **extra: Any,
) -> dict[str, Any]:
    """Build a standard Brain event dict for AuditStorage (Step 2+)."""
    return {
        "at": utc_now_iso(),
        "event": event_type.value,
        "task_id": record.task_id,
        "task_name": record.task_name,
        "lifecycle": record.lifecycle.value,
        **extra,
    }


@dataclass
class BrainRunResult:
    """Summary returned by Brain.run_next() — for tests and future Dashboard."""

    task_id: str
    task_name: str
    lifecycle: TaskLifecycle
    kernel_ok: bool
    duration_ms: float
    error: str | None = None
