from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from brain.config import BrainConfig
from brain.models import (
    BrainEventType,
    BrainRunResult,
    QueuedTaskRecord,
    TaskLifecycle,
    make_brain_event,
)
from brain.queue import TaskQueue
from brain.storage.audit_storage import AuditStorage, JsonlAuditStorage
from brain.storage.queue_storage import JsonQueueStorage, QueueStorage
from kernel.kernel import GenesisKernel
from kernel.task import Task


@dataclass
class Brain:
    """
    Brain v0.1 — dispatcher only.

    enqueue → queue → run_next → Kernel.submit → audit → result
  No AI, no strategy, no internet.
    """

    kernel: GenesisKernel
    queue_storage: QueueStorage
    audit_storage: AuditStorage
    config: BrainConfig = field(default_factory=BrainConfig)
    _paused: bool = field(default=False, repr=False)

    def __post_init__(self) -> None:
        self._queue = TaskQueue(self.queue_storage)
        self.config.memory_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def create(
        cls,
        kernel: GenesisKernel,
        *,
        memory_dir: str | None = None,
    ) -> Brain:
        config = BrainConfig(
            memory_dir=Path(memory_dir) if memory_dir else BrainConfig().memory_dir
        )
        return cls(
            kernel=kernel,
            queue_storage=JsonQueueStorage(config.queue_path),
            audit_storage=JsonlAuditStorage(config.audit_path),
            config=config,
        )

    @property
    def is_paused(self) -> bool:
        return self._paused

    def pause(self) -> None:
        """Stop processing new tasks. Dashboard will use this later."""
        self._paused = True

    def resume(self) -> None:
        """Resume processing queued tasks."""
        self._paused = False

    def enqueue(self, task: Task) -> str:
        created = QueuedTaskRecord.from_task(task, lifecycle=TaskLifecycle.NEW)
        self.audit_storage.append_event(
            make_brain_event(BrainEventType.TASK_CREATED, created)
        )
        queued = created.with_lifecycle(TaskLifecycle.QUEUED)
        self.audit_storage.append_event(
            make_brain_event(BrainEventType.TASK_QUEUED, queued)
        )
        self._queue.append(queued)
        return queued.task_id

    def run_next(self) -> BrainRunResult | None:
        if self._paused:
            return None

        record = self._queue.first_queued()
        if record is None:
            return None

        running = record.with_lifecycle(TaskLifecycle.RUNNING)
        self._queue.update_by_id(record.task_id, running)
        self.audit_storage.append_event(
            make_brain_event(BrainEventType.TASK_STARTED, running)
        )

        kernel_result = self.kernel.submit(running.to_task())

        kernel_events = [
            {**entry, "brain_task_id": running.task_id}
            for entry in self.kernel.audit_log
        ]
        self.audit_storage.append_events(kernel_events)

        if kernel_result.ok:
            final = running.with_lifecycle(TaskLifecycle.COMPLETED)
            self.audit_storage.append_event(
                make_brain_event(
                    BrainEventType.TASK_COMPLETED,
                    final,
                    duration_ms=kernel_result.duration_ms,
                    kernel_ok=True,
                )
            )
        else:
            final = running.with_lifecycle(TaskLifecycle.FAILED)
            self.audit_storage.append_event(
                make_brain_event(
                    BrainEventType.TASK_FAILED,
                    final,
                    duration_ms=kernel_result.duration_ms,
                    kernel_ok=False,
                    error=kernel_result.error,
                )
            )

        self._queue.update_by_id(record.task_id, final)

        return BrainRunResult(
            task_id=final.task_id,
            task_name=final.task_name,
            lifecycle=final.lifecycle,
            kernel_ok=kernel_result.ok,
            duration_ms=kernel_result.duration_ms,
            error=kernel_result.error,
        )

    def run_all(self) -> list[BrainRunResult]:
        results: list[BrainRunResult] = []
        while True:
            result = self.run_next()
            if result is None:
                break
            results.append(result)
        return results

    def cancel(self, task_id: str) -> bool:
        record = self._queue.get_by_id(task_id)
        if record is None or record.lifecycle != TaskLifecycle.QUEUED:
            return False
        cancelled = record.with_lifecycle(TaskLifecycle.CANCELLED)
        self._queue.update_by_id(task_id, cancelled)
        self.audit_storage.append_event(
            make_brain_event(BrainEventType.TASK_CANCELLED, cancelled)
        )
        return True

    def pending_count(self) -> int:
        return self._queue.pending_count()

    def list_tasks(self) -> list[QueuedTaskRecord]:
        """All task records in queue storage (any lifecycle)."""
        return self._queue.all_records()
