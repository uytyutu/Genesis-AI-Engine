from __future__ import annotations

from dataclasses import dataclass

from app.integration.brain_adapter import BrainAdapter
from app.integration.task_service import TaskService
from app.schemas import CreateTaskRequest


@dataclass
class DemoRunResult:
    tasks_created: int
    tasks_completed: int
    tasks_failed: int
    task_ids: list[str]


class DemoService:
    """Creates sample tasks and runs the queue — for owner onboarding and demos."""

    def __init__(self, tasks: TaskService, adapter: BrainAdapter) -> None:
        self._tasks = tasks
        self._adapter = adapter

    def run_demo(self, count: int = 5) -> DemoRunResult:
        if self._adapter.is_paused:
            self._adapter.resume()

        task_ids: list[str] = []
        for index in range(count):
            task_id = self._tasks.create_task(
                CreateTaskRequest(
                    name=f"demo-task-{index + 1}",
                    action="ping",
                    input={"demo": True, "index": index + 1},
                )
            )
            task_ids.append(task_id)

        completed = 0
        failed = 0
        for _ in range(count):
            result = self._tasks.run_next()
            if result is None:
                break
            if result.result == "ok":
                completed += 1
            else:
                failed += 1

        return DemoRunResult(
            tasks_created=len(task_ids),
            tasks_completed=completed,
            tasks_failed=failed,
            task_ids=task_ids,
        )
