"""Project persistence — project.json in workspace memory (no kernel changes)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.execution.workspace import ExecutionWorkspaceStore, WorkspaceMeta
from app.integration.project_platform.schema import (
    ProjectArtifact,
    ProjectRecord,
    ProjectVersion,
    TimelineEvent,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectStore:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._workspaces = ExecutionWorkspaceStore(memory_dir)

    def _project_path(self, workspace_id: str) -> Path:
        return self._workspaces.path_for(workspace_id, "memory", "project.json")

    def load(self, workspace_id: str) -> ProjectRecord | None:
        path = self._project_path(workspace_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return _record_from_dict(data)

    def save(self, record: ProjectRecord) -> None:
        path = self._project_path(record.workspace_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._workspaces.touch(record.workspace_id)

    def ensure_for_workspace(
        self,
        meta: WorkspaceMeta,
        *,
        visitor_id: str,
        title: str | None = None,
        service_id: str | None = None,
        activate_project: bool = False,
    ) -> ProjectRecord:
        existing = self.load(meta.workspace_id)
        if existing:
            if activate_project and existing.mode == "conversation":
                existing.mode = "project"
                existing.service_id = service_id or existing.service_id
                if title:
                    existing.title = title
                existing.updated_at = _utc_now()
                self.save(existing)
            return existing

        now = _utc_now()
        record = ProjectRecord(
            project_id=f"proj-{uuid.uuid4().hex[:12]}",
            workspace_id=meta.workspace_id,
            visitor_id=visitor_id,
            title=title or meta.title or "Мой проект",
            service_id=service_id,
            mode="project" if activate_project else "conversation",
            lifecycle_phase="dialog",
            created_at=now,
            updated_at=now,
            timeline=[
                TimelineEvent(
                    id=f"tl-{uuid.uuid4().hex[:8]}",
                    type="created",
                    label="Проект создан",
                    at=now,
                    detail="Virtus Core начала вести вашу работу как проект.",
                )
            ],
        )
        self.save(record)
        return record


def _record_from_dict(data: dict) -> ProjectRecord:
    timeline = [
        TimelineEvent(**e) if isinstance(e, dict) else e
        for e in data.get("timeline") or []
    ]
    versions: list[ProjectVersion] = []
    for v in data.get("versions") or []:
        if not isinstance(v, dict):
            continue
        arts = [
            ProjectArtifact(**a) if isinstance(a, dict) else a
            for a in v.get("artifacts") or []
        ]
        versions.append(
            ProjectVersion(
                version=int(v.get("version") or 1),
                label=str(v.get("label") or "Версия 1"),
                created_at=str(v.get("created_at") or ""),
                summary=str(v.get("summary") or ""),
                artifacts=arts,
            )
        )
    return ProjectRecord(
        project_id=str(data.get("project_id") or ""),
        workspace_id=str(data.get("workspace_id") or ""),
        visitor_id=str(data.get("visitor_id") or ""),
        title=str(data.get("title") or "Проект"),
        service_id=data.get("service_id"),
        mode=data.get("mode") or "conversation",
        lifecycle_phase=data.get("lifecycle_phase") or "dialog",
        active_section=str(data.get("active_section") or "website"),
        created_at=str(data.get("created_at") or ""),
        updated_at=str(data.get("updated_at") or ""),
        next_step_hint=str(data.get("next_step_hint") or ""),
        description=str(data.get("description") or ""),
        market=str(data.get("market") or ""),
        brief=dict(data.get("brief") or {}) if isinstance(data.get("brief"), dict) else {},
        timeline=timeline,
        versions=versions,
    )
