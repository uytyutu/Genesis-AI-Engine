from __future__ import annotations

import uuid

import pytest

from agents.echo_agent import EchoAgent
from brain.brain import Brain
from brain.models import TaskLifecycle
from brain.storage.audit_storage import JsonlAuditStorage
from brain.storage.queue_storage import JsonQueueStorage
from kernel.agent import AgentRegistry
from kernel.kernel import GenesisKernel
from kernel.task import Task


@pytest.fixture
def memory_dir(tmp_path):
    return tmp_path / "memory"


@pytest.fixture
def kernel() -> GenesisKernel:
    registry = AgentRegistry()
    registry.register(EchoAgent())
    return GenesisKernel(registry=registry)


@pytest.fixture
def brain(kernel: GenesisKernel, memory_dir) -> Brain:
    return Brain(
        kernel=kernel,
        queue_storage=JsonQueueStorage(memory_dir / "queue.json"),
        audit_storage=JsonlAuditStorage(memory_dir / "audit.jsonl"),
    )


def test_enqueue_assigns_uuid_and_increases_pending(brain: Brain) -> None:
    task = Task(name="job-a", payload={"agent_id": "echo", "action": "ping", "input": {}})
    task_id = brain.enqueue(task)

    uuid.UUID(task_id)
    assert brain.pending_count() == 1


def test_enqueue_writes_created_and_queued_events(brain: Brain, memory_dir) -> None:
    task = Task(name="events-test", payload={"agent_id": "echo", "action": "ping"})
    brain.enqueue(task)

    events = JsonlAuditStorage(memory_dir / "audit.jsonl").read_all()
    event_names = [e["event"] for e in events]
    assert "task.created" in event_names
    assert "task.queued" in event_names


def test_run_next_executes_via_kernel(brain: Brain) -> None:
    task = Task(
        name="run-one",
        payload={"agent_id": "echo", "action": "ping", "input": {"x": 1}},
    )
    task_id = brain.enqueue(task)

    result = brain.run_next()

    assert result is not None
    assert result.task_id == task_id
    assert result.kernel_ok is True
    assert result.lifecycle == TaskLifecycle.COMPLETED
    assert brain.pending_count() == 0


def test_fifo_order_three_tasks(brain: Brain) -> None:
    ids = []
    for index in range(3):
        task = Task(
            name=f"fifo-{index}",
            payload={"agent_id": "echo", "action": "ping", "input": {"n": index}},
        )
        ids.append(brain.enqueue(task))

    first = brain.run_next()
    second = brain.run_next()
    third = brain.run_next()

    assert [r.task_id for r in (first, second, third) if r] == ids


def test_failed_kernel_task_sets_failed_lifecycle(brain: Brain) -> None:
    task = Task(
        name="will-fail",
        payload={"agent_id": "echo", "action": "fail", "input": {"reason": "boom"}},
    )
    brain.enqueue(task)

    result = brain.run_next()

    assert result is not None
    assert result.kernel_ok is False
    assert result.lifecycle == TaskLifecycle.FAILED


def test_cancel_queued_task(brain: Brain, memory_dir) -> None:
    task = Task(name="cancel-me", payload={"agent_id": "echo", "action": "ping"})
    task_id = brain.enqueue(task)

    assert brain.cancel(task_id) is True
    assert brain.pending_count() == 0
    assert brain.run_next() is None

    events = JsonlAuditStorage(memory_dir / "audit.jsonl").read_all()
    assert any(e["event"] == "task.cancelled" for e in events)


def test_pause_blocks_run_next(brain: Brain) -> None:
    brain.enqueue(Task(name="paused", payload={"agent_id": "echo", "action": "ping"}))
    brain.pause()

    assert brain.is_paused is True
    assert brain.run_next() is None
    assert brain.pending_count() == 1

    brain.resume()
    result = brain.run_next()
    assert result is not None
    assert result.kernel_ok is True


def test_run_next_empty_queue_returns_none(brain: Brain) -> None:
    assert brain.run_next() is None


def test_queue_persists_across_brain_restart(
    kernel: GenesisKernel, memory_dir
) -> None:
    storage_path = memory_dir / "queue.json"
    audit_path = memory_dir / "audit.jsonl"

    brain_a = Brain(
        kernel=kernel,
        queue_storage=JsonQueueStorage(storage_path),
        audit_storage=JsonlAuditStorage(audit_path),
    )
    task_id = brain_a.enqueue(
        Task(name="persist", payload={"agent_id": "echo", "action": "ping"})
    )

    brain_b = Brain(
        kernel=kernel,
        queue_storage=JsonQueueStorage(storage_path),
        audit_storage=JsonlAuditStorage(audit_path),
    )

    assert brain_b.pending_count() == 1
    result = brain_b.run_next()
    assert result is not None
    assert result.task_id == task_id


def test_integration_queue_brain_kernel_audit(brain: Brain, memory_dir) -> None:
    """Full pipeline: Queue → Brain → Kernel → Audit."""
    for index in range(2):
        brain.enqueue(
            Task(
                name=f"integration-{index}",
                payload={"agent_id": "echo", "action": "ping", "input": {"i": index}},
            )
        )

    results = brain.run_all()
    audit = JsonlAuditStorage(memory_dir / "audit.jsonl").read_all()
    queue = JsonQueueStorage(memory_dir / "queue.json").load_all()

    assert len(results) == 2
    assert all(r.kernel_ok for r in results)
    assert brain.pending_count() == 0
    assert any(e["event"] == "task.completed" for e in audit)
    assert any(e["event"] == "task.started" for e in audit)
    assert any(e["event"] == "agent.done" for e in audit)
    assert all(r.lifecycle == TaskLifecycle.COMPLETED for r in queue)
