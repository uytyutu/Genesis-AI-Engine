"""Shared project context — workspace, preview, accumulated dialog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.execution.workspace import ExecutionWorkspaceStore
from app.integration.product_line import SERVICE_WEBSITE


def visitor_map_path(memory_dir: Path) -> Path:
    return memory_dir / "execution" / "visitor_workspaces.json"


def existing_workspace_id(memory_dir: Path, visitor_id: str) -> str | None:
    path = visitor_map_path(memory_dir)
    if not path.is_file():
        return None
    try:
        mapping = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    ws_id = mapping.get(visitor_id)
    if not ws_id:
        return None
    if ExecutionWorkspaceStore(memory_dir).get(ws_id):
        return ws_id
    return None


def workspace_for_visitor(
    memory_dir: Path,
    visitor_id: str,
    *,
    title: str = "Vector Workspace",
) -> str:
    path = visitor_map_path(memory_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, str] = {}
    if path.is_file():
        try:
            mapping = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            mapping = {}
    ws_id = mapping.get(visitor_id)
    store = ExecutionWorkspaceStore(memory_dir)
    if ws_id and store.get(ws_id):
        return ws_id
    ws = store.create(owner_id=visitor_id, title=title)
    mapping[visitor_id] = ws.workspace_id
    path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws.workspace_id


def preview_href(workspace_id: str, visitor_id: str) -> str:
    q = quote((visitor_id or "anonymous").strip()[:64], safe="")
    return f"/api/public/execution/preview/{workspace_id}?visitor_id={q}"


def workspace_file_href(workspace_id: str, visitor_id: str, rel: str) -> str:
    q = quote((visitor_id or "anonymous").strip()[:64], safe="")
    rel = (rel or "").lstrip("/")
    return f"/api/public/execution/workspace/{workspace_id}/files/{rel}?visitor_id={q}"


def project_record(memory_dir: Path, visitor_id: str):
    ws_id = existing_workspace_id(memory_dir, visitor_id)
    if not ws_id:
        return None, None
    try:
        from app.integration.project_platform.store import ProjectStore

        record = ProjectStore(memory_dir).load(ws_id)
        return ws_id, record
    except Exception:
        return ws_id, None


def project_service_id(memory_dir: Path, visitor_id: str) -> str | None:
    _, record = project_record(memory_dir, visitor_id)
    if not record:
        return None
    return str(record.service_id or SERVICE_WEBSITE)


def workspace_has_deliverable_preview(memory_dir: Path, workspace_id: str) -> bool:
    """True when project has a reviewable first version — any service."""
    try:
        from app.integration.project_platform.store import ProjectStore

        record = ProjectStore(memory_dir).load(workspace_id)
    except Exception:
        record = None
    if record:
        for ver in record.versions or []:
            for art in ver.artifacts or []:
                if art.kind == "preview" and art.href:
                    return True
    store = ExecutionWorkspaceStore(memory_dir)
    preview = store.path_for(workspace_id, "artifacts", "preview")
    if preview.is_dir():
        for name in ("index.html", "concept.md", "brief.md"):
            if (preview / name).is_file():
                return True
    files_index = store.path_for(workspace_id, "files", "index.html")
    if files_index.is_file():
        return True
    return False


def primary_preview_href(
    memory_dir: Path,
    workspace_id: str,
    visitor_id: str,
    *,
    service_id: str,
) -> str:
    store = ExecutionWorkspaceStore(memory_dir)
    preview_index = store.path_for(workspace_id, "artifacts", "preview/index.html")
    files_index = store.path_for(workspace_id, "files", "index.html")
    if service_id == SERVICE_WEBSITE and (preview_index.is_file() or files_index.is_file()):
        return preview_href(workspace_id, visitor_id)
    concept_preview = store.path_for(workspace_id, "artifacts", "preview/concept.md")
    if concept_preview.is_file():
        return workspace_file_href(workspace_id, visitor_id, "concept.md")
    return preview_href(workspace_id, visitor_id)


def accumulated_project_text(memory_dir: Path, visitor_id: str) -> str:
    _, record = project_record(memory_dir, visitor_id)
    if not record:
        return ""
    parts: list[str] = []
    if record.description.strip():
        parts.append(record.description.strip())
    for event in record.timeline or []:
        detail = (event.detail or "").strip()
        if detail and detail not in parts:
            parts.append(detail)
    return "\n".join(parts).strip()


def combined_project_dialog(
    text: str,
    *,
    visitor_id: str,
    memory_dir: Path,
    history: list[dict[str, str]] | None = None,
) -> str:
    chunks: list[str] = []
    project_text = accumulated_project_text(memory_dir, visitor_id)
    if project_text:
        chunks.append(project_text)
    if history:
        user_bits = [
            str(m.get("content") or "").strip()
            for m in history
            if str(m.get("role") or "") == "user" and str(m.get("content") or "").strip()
        ]
        if user_bits:
            chunks.append("\n".join(user_bits[-6:]))
    if text.strip():
        chunks.append(text.strip())
    return "\n".join(chunks).strip()


def record_project_execution(
    *,
    visitor_id: str,
    workspace_id: str,
    capability_id: str,
    outputs: dict[str, Any],
    goal: str = "",
    memory_dir: Path,
) -> None:
    try:
        from app.integration.project_platform.service import ProjectPlatformService

        ProjectPlatformService(memory_dir).record_execution(
            visitor_id=visitor_id,
            workspace_id=workspace_id,
            capability_id=capability_id,
            outputs=outputs,
            goal=goal,
        )
    except Exception:
        pass
