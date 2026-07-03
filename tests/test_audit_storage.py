from __future__ import annotations

import json

import pytest

from brain.models import BrainEventType, QueuedTaskRecord, TaskLifecycle, make_brain_event
from brain.storage.audit_storage import JsonlAuditStorage
from kernel.task import Task


@pytest.fixture
def audit_path(tmp_path):
    return tmp_path / "audit.jsonl"


@pytest.fixture
def audit(audit_path):
    return JsonlAuditStorage(audit_path)


def test_append_creates_file(audit: JsonlAuditStorage, audit_path) -> None:
    audit.append_event({"event": "task.created", "task_id": "1"})

    assert audit_path.exists()
    assert audit_path.read_text(encoding="utf-8").endswith("\n")


def test_each_line_is_valid_json(audit: JsonlAuditStorage) -> None:
    audit.append_events(
        [
            {"event": "task.created", "task_id": "a"},
            {"event": "task.queued", "task_id": "a"},
        ]
    )

    for line in audit.path.read_text(encoding="utf-8").splitlines():
        parsed = json.loads(line)
        assert "event" in parsed


def test_events_preserve_order(audit: JsonlAuditStorage) -> None:
    events = [
        {"event": "task.created", "order": 1},
        {"event": "task.queued", "order": 2},
        {"event": "task.started", "order": 3},
        {"event": "task.completed", "order": 4},
    ]
    audit.append_events(events)

    loaded = audit.read_all()
    assert [e["order"] for e in loaded] == [1, 2, 3, 4]


def test_task_started_event_shape(audit: JsonlAuditStorage) -> None:
    task = Task(name="analyze-bots")
    record = QueuedTaskRecord.from_task(task, lifecycle=TaskLifecycle.RUNNING)
    event = make_brain_event(BrainEventType.TASK_STARTED, record)

    audit.append_event(event)
    loaded = audit.read_all()[0]

    assert loaded["event"] == "task.started"
    assert loaded["task_id"] == task.id
    assert loaded["task_name"] == "analyze-bots"
    assert loaded["lifecycle"] == "running"
    assert "at" in loaded


def test_read_all_empty_when_file_missing(audit_path) -> None:
    storage = JsonlAuditStorage(audit_path)
    assert storage.read_all() == []


def test_append_events_empty_list_is_noop(audit: JsonlAuditStorage, audit_path) -> None:
    audit.append_events([])
    assert audit_path.exists() is False


def test_multiple_batches_append_in_order(audit: JsonlAuditStorage) -> None:
    audit.append_event({"event": "batch", "n": 1})
    audit.append_events([{"event": "batch", "n": 2}, {"event": "batch", "n": 3}])

    loaded = audit.read_all()
    assert [e["n"] for e in loaded] == [1, 2, 3]


def test_append_only_does_not_truncate_existing(audit: JsonlAuditStorage) -> None:
    audit.append_event({"event": "first"})
    audit.append_event({"event": "second"})

    assert len(audit.read_all()) == 2
    assert audit.read_all()[0]["event"] == "first"
