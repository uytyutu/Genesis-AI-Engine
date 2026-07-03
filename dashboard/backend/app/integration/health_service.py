from __future__ import annotations

from app.integration.brain_adapter import BrainAdapter


class HealthService:
    """Live health checks for core modules."""

    def __init__(self, adapter: BrainAdapter) -> None:
        self._adapter = adapter

    def check_component(self, component_id: str) -> str:
        checks = self.check_all()
        return checks.get(component_id, "offline")

    def check_all(self) -> dict[str, str]:
        adapter = self._adapter
        status: dict[str, str] = {}

        status["kernel"] = "online"
        status["brain"] = "online" if adapter.brain is not None else "offline"

        try:
            adapter.list_records()
            status["queue"] = "online"
        except OSError:
            status["queue"] = "offline"

        try:
            adapter.read_audit()
            status["audit"] = "online"
        except OSError:
            status["audit"] = "offline"

        if adapter.is_paused:
            status["brain"] = "degraded"

        return status
