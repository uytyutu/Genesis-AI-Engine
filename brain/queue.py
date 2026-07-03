from __future__ import annotations

from brain.models import QueuedTaskRecord, TaskLifecycle
from brain.storage.queue_storage import QueueStorage


class TaskQueue:
    """FIFO queue backed by QueueStorage."""

    def __init__(self, storage: QueueStorage) -> None:
        self._storage = storage

    def all_records(self) -> list[QueuedTaskRecord]:
        return self._storage.load_all()

    def replace(self, records: list[QueuedTaskRecord]) -> None:
        self._storage.save_all(records)

    def append(self, record: QueuedTaskRecord) -> None:
        records = self.all_records()
        records.append(record)
        self.replace(records)

    def update_by_id(self, task_id: str, record: QueuedTaskRecord) -> bool:
        records = self.all_records()
        for index, existing in enumerate(records):
            if existing.task_id == task_id:
                records[index] = record
                self.replace(records)
                return True
        return False

    def get_by_id(self, task_id: str) -> QueuedTaskRecord | None:
        for record in self.all_records():
            if record.task_id == task_id:
                return record
        return None

    def first_queued(self) -> QueuedTaskRecord | None:
        for record in self.all_records():
            if record.lifecycle == TaskLifecycle.QUEUED:
                return record
        return None

    def pending_count(self) -> int:
        return sum(
            1 for record in self.all_records()
            if record.lifecycle == TaskLifecycle.QUEUED
        )
