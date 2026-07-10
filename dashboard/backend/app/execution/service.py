"""Owner-facing Execution Layer facade — does not touch Genesis Brain."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.execution.capabilities import ExecutionCapabilityRegistry, EXECUTION_LAYER_VERSION
from app.execution.planner import TaskPlannerV2
from app.execution.workspace import ExecutionWorkspaceStore


class ExecutionLayerService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory_dir = memory_dir
        self._registry = ExecutionCapabilityRegistry()
        self._planner = TaskPlannerV2(self._registry)
        self._workspaces = ExecutionWorkspaceStore(memory_dir)

    def capabilities_snapshot(self) -> dict[str, Any]:
        snap = self._registry.snapshot()
        snap["phase"] = 1
        snap["brain_integration"] = "not_wired"
        return snap

    def plan_preview(self, goal: str, *, workspace_id: str = "", owner_id: str = "owner") -> dict[str, Any]:
        wid = workspace_id
        if not wid:
            ws = self._workspaces.create(owner_id=owner_id, title=goal[:48] or "Execution")
            wid = ws.workspace_id
        plan = self._planner.plan(goal, workspace_id=wid)
        return {
            "version": EXECUTION_LAYER_VERSION,
            "workspace_id": wid,
            "plan": plan.to_dict(),
            "note": "Preview only — ExecutionManager not invoked from public chat in Phase 1",
        }
