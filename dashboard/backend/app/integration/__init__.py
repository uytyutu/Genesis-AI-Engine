"""Integration Layer — Command Center ↔ internal modules.

UI and FastAPI routes must use this layer only, never Brain/Kernel directly.
"""

from app.integration.brain_adapter import BrainAdapter
from app.integration.health_service import HealthService
from app.integration.module_status_service import ModuleStatusService
from app.integration.task_service import TaskService

__all__ = [
    "BrainAdapter",
    "HealthService",
    "ModuleStatusService",
    "TaskService",
]
