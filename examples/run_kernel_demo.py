"""Demonstrates Kernel: timing, audit log, and context between steps."""

from __future__ import annotations

import json

from agents.echo_agent import EchoAgent
from kernel.agent import AgentRegistry
from kernel.goal import Goal, GoalType
from kernel.kernel import GenesisKernel
from kernel.task import Task


def main() -> None:
    registry = AgentRegistry()
    registry.register(EchoAgent())
    kernel = GenesisKernel(registry=registry)

    task = Task(
        name="warehouse-bot-pipeline",
        goal=Goal(type=GoalType.REVENUE, target=100, unit="EUR/day"),
        payload={
            "steps": [
                {
                    "agent_id": "echo",
                    "action": "analyze",
                    "input": {"topic": "warehouse telegram bots"},
                },
                {
                    "agent_id": "echo",
                    "action": "summarize",
                    "input": {"format": "owner_brief"},
                },
            ]
        },
    )

    result = kernel.submit(task)

    print("=== Genesis Kernel Demo ===\n")
    print(f"Task:     {task.name}")
    print(f"Status:   {result.status.value}")
    print(f"Duration: {result.duration_ms} ms")
    print(f"Goal:     {result.output.get('goal', 'none')}\n")

    for index, step in enumerate(result.step_results):
        print(f"Step {index}: {step.agent_id}.{step.action}")
        print(f"  Status:   {'Success' if step.success else 'Failed'}")
        print(f"  Duration: {step.duration_ms} ms")
        if step.success and "previous_step" in step.output:
            prev = step.output["previous_step"]
            print(f"  Saw previous step output: action={prev.get('action')}")

    print("\n--- Audit log (last 3 events) ---")
    for entry in kernel.audit_log[-3:]:
        event = entry["event"]
        at = entry.get("at", "")
        duration = entry.get("duration_ms")
        extra = f" · {duration} ms" if duration is not None else ""
        print(f"  [{at}] {event}{extra}")

    print("\n--- Full result JSON ---")
    print(
        json.dumps(
            {
                "ok": result.ok,
                "duration_ms": result.duration_ms,
                "steps": [
                    {
                        "agent": s.agent_id,
                        "action": s.action,
                        "duration_ms": s.duration_ms,
                        "success": s.success,
                    }
                    for s in result.step_results
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
