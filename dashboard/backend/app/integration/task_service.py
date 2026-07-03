from __future__ import annotations

from datetime import datetime, timezone

from brain.models import TaskLifecycle

from app.integration.brain_adapter import BrainAdapter
from app.schemas import ActivityEvent, CreateTaskRequest, QueueStats, TaskItem


class TaskService:
    """Task operations for Command Center — uses BrainAdapter only."""

    def __init__(self, adapter: BrainAdapter) -> None:
        self._adapter = adapter

    def create_task(self, request: CreateTaskRequest) -> str:
        return self._adapter.enqueue_echo(
            name=request.name,
            action=request.action,
            input=request.input,
        )

    def run_next(self) -> TaskItem | None:
        result = self._adapter.run_next()
        if result is None:
            return None
        return self._record_to_item(
            self._find_record(result.task_id),
            audit_hint=result,
        )

    def cancel(self, task_id: str) -> bool:
        return self._adapter.cancel(task_id)

    def list_tasks(self) -> list[TaskItem]:
        records = self._adapter.list_records()
        audit_by_task = self._audit_summary_by_task()
        items = [
            self._record_to_item(record, audit_hint=audit_by_task.get(record.task_id))
            for record in records
        ]
        return sorted(items, key=lambda t: t.updated_at, reverse=True)

    def queue_stats(self) -> QueueStats:
        counts = {lifecycle: 0 for lifecycle in TaskLifecycle}
        for record in self._adapter.list_records():
            counts[record.lifecycle] += 1
        return QueueStats(
            pending=counts[TaskLifecycle.QUEUED],
            running=counts[TaskLifecycle.RUNNING],
            completed=counts[TaskLifecycle.COMPLETED],
            failed=counts[TaskLifecycle.FAILED],
        )

    def stats_today(self) -> dict[str, int]:
        today = datetime.now(timezone.utc).date()
        completed = 0
        failed = 0
        for record in self._adapter.list_records():
            updated = record.updated_at[:10] if record.updated_at else ""
            try:
                record_day = datetime.fromisoformat(updated).date()
            except ValueError:
                continue
            if record_day != today:
                continue
            if record.lifecycle == TaskLifecycle.COMPLETED:
                completed += 1
            elif record.lifecycle == TaskLifecycle.FAILED:
                failed += 1
        return {"completed_today": completed, "failed_today": failed}

    def recent_activity(self, limit: int = 20) -> list[ActivityEvent]:
        events = self._adapter.read_audit()
        brain_events = [e for e in reversed(events) if e.get("event", "").startswith("task.")]
        activity: list[ActivityEvent] = []
        for event in brain_events[:limit]:
            at = str(event.get("at", ""))
            short_at = at[11:16] if len(at) >= 16 else at
            message = event.get("event", "event").replace("task.", "Task ").replace("_", " ")
            activity.append(
                ActivityEvent(
                    at=short_at,
                    message=message.capitalize(),
                    task_id=event.get("task_id"),
                )
            )
        return activity

    def _find_record(self, task_id: str):
        for record in self._adapter.list_records():
            if record.task_id == task_id:
                return record
        raise KeyError(task_id)

    def _audit_summary_by_task(self) -> dict[str, dict]:
        summary: dict[str, dict] = {}
        for event in self._adapter.read_audit():
            task_id = event.get("task_id")
            if not task_id:
                continue
            if event.get("event") in ("task.completed", "task.failed"):
                summary[task_id] = event
        return summary

    def _record_to_item(self, record, audit_hint=None) -> TaskItem:
        duration_ms = None
        error = None
        result = record.lifecycle.value

        if audit_hint is not None:
            if hasattr(audit_hint, "duration_ms"):
                duration_ms = audit_hint.duration_ms
                error = getattr(audit_hint, "error", None)
                result = "ok" if audit_hint.kernel_ok else "failed"
            elif isinstance(audit_hint, dict):
                duration_ms = audit_hint.get("duration_ms")
                error = audit_hint.get("error")
                result = "ok" if audit_hint.get("kernel_ok") else "failed"

        if record.lifecycle == TaskLifecycle.CANCELLED:
            result = "cancelled"
        elif record.lifecycle == TaskLifecycle.QUEUED:
            result = "queued"
        elif record.lifecycle == TaskLifecycle.RUNNING:
            result = "running"

        return TaskItem(
            task_id=record.task_id,
            name=record.task_name,
            status=record.lifecycle.value,
            started_at=record.created_at,
            finished_at=record.updated_at if record.lifecycle in (
                TaskLifecycle.COMPLETED,
                TaskLifecycle.FAILED,
                TaskLifecycle.CANCELLED,
            ) else None,
            duration_ms=duration_ms,
            result=result,
            error=error,
            updated_at=record.updated_at,
        )
