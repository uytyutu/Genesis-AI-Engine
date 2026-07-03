from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.task import StepContext


@dataclass
class EchoAgent:
    """Test agent — echoes input and proves step context works."""

    id: str = "echo"
    calls: list[dict[str, Any]] = field(default_factory=list, repr=False)

    def run(
        self,
        action: str,
        input: dict[str, Any],
        context: StepContext,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "action": action,
                "input": input,
                "step_index": context.step_index,
                "had_previous": context.previous is not None,
            }
        )
        if action == "fail":
            raise RuntimeError(input.get("reason", "forced failure"))

        result: dict[str, Any] = {
            "agent": self.id,
            "action": action,
            "echo": input,
            "step_index": context.step_index,
        }
        if context.previous is not None:
            result["previous_step"] = context.previous
        return result
