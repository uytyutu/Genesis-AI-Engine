"""Integration demo: Queue → Brain → Kernel → Audit."""

from __future__ import annotations

from pathlib import Path

from agents.echo_agent import EchoAgent
from brain.brain import Brain
from kernel.agent import AgentRegistry
from kernel.kernel import GenesisKernel
from kernel.task import Task


def main() -> None:
    registry = AgentRegistry()
    registry.register(EchoAgent())
    kernel = GenesisKernel(registry=registry)

    memory = Path("memory")
    brain = Brain.create(kernel, memory_dir=str(memory))

    print("=== Genesis Brain Demo ===\n")

    for index in range(3):
        task = Task(
            name=f"demo-job-{index}",
            payload={
                "agent_id": "echo",
                "action": "ping",
                "input": {"step": index},
            },
        )
        task_id = brain.enqueue(task)
        print(f"Enqueued: {task_id[:8]}... ({task.name})")

    print(f"\nPending: {brain.pending_count()}")
    print("Running all...\n")

    results = brain.run_all()

    for result in results:
        status = "OK" if result.kernel_ok else "FAIL"
        print(
            f"  {result.task_id[:8]}... {result.task_name} "
            f"— {status} — {result.duration_ms} ms"
        )

    print(f"\nPending after run: {brain.pending_count()}")
    print(f"Audit file: {brain.config.audit_path}")
    print(f"Queue file: {brain.config.queue_path}")


if __name__ == "__main__":
    main()
