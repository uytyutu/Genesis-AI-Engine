"""Public workspace preview — Product Truth: openable from /site."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from app.execution.workspace import ExecutionWorkspaceStore


def _visitor_map_path(memory_dir: Path) -> Path:
    return memory_dir / "execution" / "visitor_workspaces.json"


def visitor_owns_workspace(memory_dir: Path, visitor_id: str, workspace_id: str) -> bool:
    path = _visitor_map_path(memory_dir)
    if not path.is_file():
        return False
    try:
        mapping = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return mapping.get(visitor_id) == workspace_id


def resolve_preview_file(
    memory_dir: Path,
    workspace_id: str,
    visitor_id: str,
    relative: str = "",
) -> Path:
    if not visitor_id or not workspace_id:
        raise HTTPException(status_code=403, detail="preview_forbidden")
    if not visitor_owns_workspace(memory_dir, visitor_id, workspace_id):
        raise HTTPException(status_code=403, detail="preview_forbidden")
    store = ExecutionWorkspaceStore(memory_dir)
    if not store.get(workspace_id):
        raise HTTPException(status_code=404, detail="workspace_not_found")

    preview_root = store.path_for(workspace_id, "artifacts", "preview")
    if not preview_root.is_dir():
        raise HTTPException(status_code=404, detail="preview_not_ready")

    rel = (relative or "index.html").strip().lstrip("/").replace("\\", "/")
    if ".." in rel.split("/"):
        raise HTTPException(status_code=400, detail="invalid_path")
    target = (preview_root / rel).resolve()
    if not str(target).startswith(str(preview_root.resolve())):
        raise HTTPException(status_code=400, detail="invalid_path")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="file_not_found")
    return target


def serve_preview(
    memory_dir: Path,
    workspace_id: str,
    visitor_id: str,
    relative: str = "",
) -> FileResponse | HTMLResponse:
    target = resolve_preview_file(memory_dir, workspace_id, visitor_id, relative)
    media = "text/html"
    if target.suffix == ".css":
        media = "text/css"
    elif target.suffix == ".js":
        media = "application/javascript"
    elif target.suffix == ".md":
        media = "text/markdown; charset=utf-8"
    return FileResponse(target, media_type=media)
