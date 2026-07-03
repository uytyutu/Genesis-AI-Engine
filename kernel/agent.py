from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from kernel.task import StepContext


@runtime_checkable
class Agent(Protocol):
    """Minimal agent contract — plugins implement this."""

    id: str

    def run(
        self,
        action: str,
        input: dict[str, Any],
        context: StepContext,
    ) -> dict[str, Any]:
        """Execute one action and return structured output."""
        ...


@dataclass
class AgentRegistry:
    """Register agents by id. Kernel resolves agents at runtime."""

    _agents: dict[str, Agent] = field(default_factory=dict)

    def register(self, agent: Agent) -> None:
        if not agent.id.strip():
            raise ValueError("agent id must not be empty")
        if agent.id in self._agents:
            raise ValueError(f"agent already registered: {agent.id}")
        self._agents[agent.id] = agent

    def get(self, agent_id: str) -> Agent:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            registered = ", ".join(sorted(self._agents)) or "(none)"
            raise KeyError(
                f"unknown agent {agent_id!r}; registered: {registered}"
            ) from exc

    def list_ids(self) -> list[str]:
        return sorted(self._agents)
