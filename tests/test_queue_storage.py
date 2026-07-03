from __future__ import annotations

import json

import pytest

from brain.models import QueuedTaskRecord, TaskLifecycle, goal_from_dict, goal_to_dict
from brain.storage.queue_storage import JsonQueueStorage
from kernel.goal import Goal, GoalType
from kernel.task import Task


@pytest.fixture
def storage_path(tmp_path):
    return tmp_path / "queue.json"


@pytest.fixture
def storage(storage_path):
    return JsonQueueStorage(storage_path)


def test_load_empty_when_file_missing(storage: JsonQueueStorage) -> None:
    assert storage.load_all() == []


def test_save_and_load_round_trip(storage: JsonQueueStorage) -> None:
    task = Task(name="test-job", payload={"agent_id": "echo", "action": "ping"})
    record = QueuedTaskRecord.from_task(task, lifecycle=TaskLifecycle.QUEUED)

    storage.save_all([record])
    loaded = storage.load_all()

    assert len(loaded) == 1
    assert loaded[0].task_id == record.task_id
    assert loaded[0].task_name == "test-job"
    assert loaded[0].lifecycle == TaskLifecycle.QUEUED


def test_fifo_order_preserved(storage: JsonQueueStorage) -> None:
    records = []
    for index in range(3):
        task = Task(name=f"job-{index}", payload={"n": index})
        records.append(
            QueuedTaskRecord.from_task(task, lifecycle=TaskLifecycle.QUEUED)
        )

    storage.save_all(records)
    loaded = storage.load_all()

    assert [r.task_name for r in loaded] == ["job-0", "job-1", "job-2"]


@pytest.mark.parametrize(
    "lifecycle",
    list(TaskLifecycle),
)
def test_all_lifecycle_states_persist(
    storage: JsonQueueStorage, lifecycle: TaskLifecycle
) -> None:
    task = Task(name="lifecycle-test")
    record = QueuedTaskRecord.from_task(task, lifecycle=lifecycle)

    storage.save_all([record])
    loaded = storage.load_all()[0]

    assert loaded.lifecycle == lifecycle


@pytest.mark.parametrize("goal_type", list(GoalType))
def test_goal_serialization_round_trip(goal_type: GoalType) -> None:
    goal = Goal(type=goal_type, target=100, unit="count", horizon_days=7)
    data = goal_to_dict(goal)
    restored = goal_from_dict(data)

    assert restored is not None
    assert restored.type == goal_type
    assert restored.target == 100
    assert restored.horizon_days == 7


def test_from_task_to_task_round_trip() -> None:
    task = Task(
        name="round-trip",
        payload={"steps": [{"agent_id": "echo", "action": "a"}]},
        goal=Goal(type=GoalType.REVENUE, target=50, unit="EUR/day"),
    )
    record = QueuedTaskRecord.from_task(task, lifecycle=TaskLifecycle.NEW)
    restored = record.to_task()

    assert restored.id == task.id
    assert restored.name == task.name
    assert restored.payload == task.payload
    assert restored.goal == task.goal


def test_atomic_write_produces_valid_json(storage_path) -> None:
    storage = JsonQueueStorage(storage_path)
    task = Task(name="atomic")
    storage.save_all([QueuedTaskRecord.from_task(task, lifecycle=TaskLifecycle.QUEUED)])

    parsed = json.loads(storage_path.read_text(encoding="utf-8"))
    assert parsed["version"] == 1
    assert len(parsed["records"]) == 1
    assert storage_path.with_suffix(".json.tmp").exists() is False


def test_with_lifecycle_updates_state_and_timestamp() -> None:
    task = Task(name="transition")
    record = QueuedTaskRecord.from_task(task, lifecycle=TaskLifecycle.NEW)
    queued = record.with_lifecycle(TaskLifecycle.QUEUED)

    assert queued.lifecycle == TaskLifecycle.QUEUED
    assert queued.updated_at >= record.updated_at
    assert queued.created_at == record.created_at
