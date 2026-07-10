"""Isolated execution workspaces — files, logs, tasks, artifacts."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WorkspaceMeta:
    workspace_id: str
    owner_id: str
    title: str
    created_at: str
    updated_at: str
    project_id: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutionWorkspaceStore:
    """File-backed workspace roots under GENESIS_MEMORY_DIR/execution/workspaces/."""

    def __init__(self, memory_dir: Path) -> None:
        self._root = memory_dir / "execution" / "workspaces"
        self._root.mkdir(parents=True, exist_ok=True)

    def create(self, *, owner_id: str, title: str, project_id: str | None = None) -> WorkspaceMeta:
        wid = f"ws-{uuid.uuid4().hex[:12]}"
        now = _utc_now()
        meta = WorkspaceMeta(
            workspace_id=wid,
            owner_id=owner_id,
            title=title.strip() or "Workspace",
            created_at=now,
            updated_at=now,
            project_id=project_id,
        )
        base = self._workspace_path(wid)
        for sub in ("files", "logs", "tasks", "artifacts", "memory"):
            (base / sub).mkdir(parents=True, exist_ok=True)
        self._write_meta(meta)
        return meta

    def get(self, workspace_id: str) -> WorkspaceMeta | None:
        path = self._meta_path(workspace_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return WorkspaceMeta(**data)
        except (json.JSONDecodeError, TypeError, OSError):
            return None

    def touch(self, workspace_id: str) -> None:
        meta = self.get(workspace_id)
        if not meta:
            return
        meta.updated_at = _utc_now()
        self._write_meta(meta)

    def path_for(self, workspace_id: str, area: str, relative: str = "") -> Path:
        base = self._workspace_path(workspace_id) / area
        base.mkdir(parents=True, exist_ok=True)
        return base / relative if relative else base

    def _workspace_path(self, workspace_id: str) -> Path:
        return self._root / workspace_id

    def _meta_path(self, workspace_id: str) -> Path:
        return self._workspace_path(workspace_id) / "workspace.json"

    def _write_meta(self, meta: WorkspaceMeta) -> None:
        path = self._meta_path(meta.workspace_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(meta.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
