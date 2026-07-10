"""Phase 2 — real filesystem executors."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.execution.workspace import ExecutionWorkspaceStore


def _safe_relative_path(raw: str) -> str:
    p = (raw or "file.txt").strip().replace("\\", "/").lstrip("/")
    if ".." in p.split("/"):
        raise ValueError("path traversal not allowed")
    return p or "file.txt"


class FilesystemWriteExecutor:
    def __init__(self, workspace_store: ExecutionWorkspaceStore) -> None:
        self._workspaces = workspace_store

    def execute(self, inputs: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        workspace_id = str(inputs.get("workspace_id") or context.get("workspace_id") or "")
        if not workspace_id:
            raise ValueError("workspace_id required")
        rel = _safe_relative_path(str(inputs.get("path") or "file.txt"))
        content = str(inputs.get("content") or "")
        target: Path = self._workspaces.path_for(workspace_id, "files", rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8")
        target.write_bytes(data)
        return {"path": rel, "bytes": len(data), "workspace_id": workspace_id}

    def rollback(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
        workspace_id = str(outputs.get("workspace_id") or inputs.get("workspace_id") or "")
        rel = str(outputs.get("path") or inputs.get("path") or "")
        if not workspace_id or not rel:
            return
        target = self._workspaces.path_for(workspace_id, "files", rel)
        if target.is_file():
            target.unlink()


class FilesystemReadExecutor:
    def __init__(self, workspace_store: ExecutionWorkspaceStore) -> None:
        self._workspaces = workspace_store

    def execute(self, inputs: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        workspace_id = str(inputs.get("workspace_id") or context.get("workspace_id") or "")
        if not workspace_id:
            raise ValueError("workspace_id required")
        rel = _safe_relative_path(str(inputs.get("path") or ""))
        target = self._workspaces.path_for(workspace_id, "files", rel)
        if not target.is_file():
            raise FileNotFoundError(rel)
        text = target.read_text(encoding="utf-8")
        return {"path": rel, "content": text, "bytes": len(text.encode("utf-8"))}
