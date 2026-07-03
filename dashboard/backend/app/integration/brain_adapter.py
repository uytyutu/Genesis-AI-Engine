from __future__ import annotations

import sys
from pathlib import Path

# Genesis core packages (kernel, brain, agents) live at repo root.
def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(8):
        if (cur / "kernel").is_dir() and (cur / "brain").is_dir():
            return cur
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return start.resolve().parents[4]


_REPO_ROOT = _find_repo_root(Path(__file__))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agents.echo_agent import EchoAgent  # noqa: E402
from brain.brain import Brain  # noqa: E402
from brain.models import BrainRunResult, QueuedTaskRecord  # noqa: E402
from kernel.agent import AgentRegistry  # noqa: E402
from kernel.kernel import GenesisKernel  # noqa: E402
from kernel.task import Task  # noqa: E402


class BrainAdapter:
    """Thin wrapper around Brain — Integration Layer entry to dispatcher."""

    def __init__(self, memory_dir: Path) -> None:
        registry = AgentRegistry()
        registry.register(EchoAgent())
        kernel = GenesisKernel(registry=registry)
        self._brain = Brain.create(kernel, memory_dir=str(memory_dir))

    @property
    def brain(self) -> Brain:
        return self._brain

    def enqueue(self, task: Task) -> str:
        return self._brain.enqueue(task)

    def enqueue_echo(self, name: str, action: str = "ping", input: dict | None = None) -> str:
        task = Task(
            name=name,
            payload={
                "agent_id": "echo",
                "action": action,
                "input": input or {},
            },
        )
        return self._brain.enqueue(task)

    def run_next(self) -> BrainRunResult | None:
        return self._brain.run_next()

    def cancel(self, task_id: str) -> bool:
        return self._brain.cancel(task_id)

    def pause(self) -> None:
        self._brain.pause()

    def resume(self) -> None:
        self._brain.resume()

    @property
    def is_paused(self) -> bool:
        return self._brain.is_paused

    def list_records(self) -> list[QueuedTaskRecord]:
        return self._brain.list_tasks()

    def read_audit(self) -> list[dict]:
        return self._brain.audit_storage.read_all()
