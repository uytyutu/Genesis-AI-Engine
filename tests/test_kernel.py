from __future__ import annotations

import pytest

from agents.echo_agent import EchoAgent
from kernel.agent import AgentRegistry
from kernel.goal import Goal, GoalType
from kernel.kernel import GenesisKernel
from kernel.task import Task, TaskStatus


@pytest.fixture
def kernel() -> GenesisKernel:
    registry = AgentRegistry()
    registry.register(EchoAgent())
    return GenesisKernel(registry=registry)


def test_kernel_single_step(kernel: GenesisKernel) -> None:
    task = Task(
        name="single",
        payload={
            "agent_id": "echo",
            "action": "ping",
            "input": {"message": "hello"},
        },
    )

    result = kernel.submit(task)

    assert result.ok
    assert result.status == TaskStatus.COMPLETED
    assert result.step_results[0].output["echo"]["message"] == "hello"
    assert result.duration_ms >= 0
    assert result.started_at
    assert result.finished_at
    assert any(e["event"] == "task.completed" for e in kernel.audit_log)


def test_kernel_multi_step_with_goal(kernel: GenesisKernel) -> None:
    task = Task(
        name="multi",
        goal=Goal(type=GoalType.USERS, target=5000, unit="count"),
        payload={
            "steps": [
                {"agent_id": "echo", "action": "a", "input": {"n": 1}},
                {"agent_id": "echo", "action": "b", "input": {"n": 2}},
            ]
        },
    )

    result = kernel.submit(task)

    assert result.ok
    assert len(result.step_results) == 2
    assert "goal" in result.output
    assert "users: 5000 count" in result.output["goal"]


def test_step_context_passes_previous_output(kernel: GenesisKernel) -> None:
    task = Task(
        name="context-chain",
        payload={
            "steps": [
                {"agent_id": "echo", "action": "first", "input": {"value": 1}},
                {"agent_id": "echo", "action": "second", "input": {"value": 2}},
            ]
        },
    )

    result = kernel.submit(task)

    assert result.ok
    assert "previous_step" not in result.step_results[0].output
    assert result.step_results[1].output["previous_step"]["action"] == "first"
    assert result.step_results[1].output["previous_step"]["echo"]["value"] == 1


def test_audit_log_has_timestamps_and_step_duration(kernel: GenesisKernel) -> None:
    task = Task(
        name="metrics",
        payload={"agent_id": "echo", "action": "ping", "input": {}},
    )

    kernel.submit(task)

    done_events = [e for e in kernel.audit_log if e["event"] == "agent.done"]
    assert len(done_events) == 1
    assert "at" in done_events[0]
    assert "duration_ms" in done_events[0]
    assert done_events[0]["duration_ms"] >= 0


def test_kernel_unknown_agent_fails(kernel: GenesisKernel) -> None:
    task = Task(
        name="bad-agent",
        payload={"agent_id": "missing", "action": "ping"},
    )

    result = kernel.submit(task)

    assert not result.ok
    assert result.status == TaskStatus.FAILED
    assert "unknown agent" in (result.error or "").lower()


def test_kernel_agent_failure_stops_pipeline(kernel: GenesisKernel) -> None:
    task = Task(
        name="fail-fast",
        payload={
            "steps": [
                {"agent_id": "echo", "action": "ok", "input": {}},
                {"agent_id": "echo", "action": "fail", "input": {"reason": "boom"}},
                {"agent_id": "echo", "action": "never", "input": {}},
            ]
        },
    )

    result = kernel.submit(task)

    assert not result.ok
    assert len(result.step_results) == 2
    assert result.step_results[1].success is False
    assert any(e["event"] == "task.failed" for e in kernel.audit_log)


def test_planning_failure_returns_failed_result(kernel: GenesisKernel) -> None:
    task = Task(name="bad-plan", payload={})

    result = kernel.submit(task)

    assert not result.ok
    assert "planning failed" in (result.error or "")
    assert any(e["event"] == "plan.failed" for e in kernel.audit_log)


def test_empty_task_name_rejected() -> None:
    with pytest.raises(ValueError, match="task name"):
        Task(name="   ")


def test_empty_steps_rejected(kernel: GenesisKernel) -> None:
    task = Task(name="empty-steps", payload={"steps": []})

    result = kernel.submit(task)

    assert not result.ok
    assert "planning failed" in (result.error or "")


def test_goal_types_are_universal() -> None:
    revenue = Goal(type=GoalType.REVENUE, target=100, unit="EUR/day")
    leads = Goal(type=GoalType.LEADS, target=50, unit="count")

    assert "revenue" in str(revenue)
    assert "leads" in str(leads)


def test_registry_rejects_duplicate_agent() -> None:
    registry = AgentRegistry()
    registry.register(EchoAgent())
    with pytest.raises(ValueError, match="already registered"):
        registry.register(EchoAgent())
