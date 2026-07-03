from __future__ import annotations

from app.integration.health_service import HealthService

# Modules not yet built stay offline. Factory ships with backend (v0.1).
_FUTURE_MODULES = [
    ("opportunity", "Opportunity"),
    ("revenue", "Revenue"),
    ("ceo", "CEO"),
]


class ModuleStatusService:
    """Maps health checks to Command Center module list."""

    def __init__(self, health: HealthService) -> None:
        self._health = health

    def list_modules(self) -> list[dict[str, str]]:
        live = self._health.check_all()
        modules = [
            {"id": "kernel", "label": "Kernel", "status": live.get("kernel", "offline")},
            {"id": "brain", "label": "Brain", "status": live.get("brain", "offline")},
            {"id": "queue", "label": "Queue", "status": live.get("queue", "offline")},
            {"id": "audit", "label": "Audit", "status": live.get("audit", "offline")},
            {
                "id": "factory",
                "label": "Factory",
                "status": "online" if live.get("kernel") == "online" else "offline",
            },
        ]
        for module_id, label in _FUTURE_MODULES:
            modules.append({"id": module_id, "label": label, "status": "offline"})
        return modules
