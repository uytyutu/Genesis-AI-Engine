"""Development Workspace — projects, files, build history (read-only scaffold)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.integration.ai_hub.ai_hub_service import AiHubService
    from app.integration.cursor_handoff_service import CursorHandoffService

_SKIP_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "target",
    "Library",
    "Temp",
    "Logs",
}
_SKIP_EXT = {".pyc", ".dll", ".exe", ".bin", ".png", ".jpg", ".webp"}


def _find_genesis_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / "PROJECT_STATE.md").exists() and (candidate / "dashboard").exists():
            return candidate
    return None


def _resolve_perfect_pallet() -> Path | None:
    env = os.getenv("GENESIS_PERFECT_PALLET_PATH", "").strip()
    if env:
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    guess = Path("D:/Games/Perfect Pallet")
    return guess if guess.is_dir() else None


class DevWorkspaceService:
    def __init__(
        self,
        cursor: CursorHandoffService,
        ai_hub: AiHubService | None = None,
    ) -> None:
        self._cursor = cursor
        self._ai_hub = ai_hub
        self._root = _find_genesis_root(Path(__file__).resolve())

    def list_projects(self) -> list[dict]:
        rows: list[dict] = []
        if self._root:
            rows.append(
                {
                    "id": "genesis",
                    "name": "Genesis AI Engine",
                    "kind": "platform",
                    "path_label": str(self._root),
                    "available": True,
                }
            )
        pp = _resolve_perfect_pallet()
        rows.append(
            {
                "id": "perfect-pallet",
                "name": "Perfect Pallet",
                "kind": "game",
                "path_label": str(pp) if pp else "(set GENESIS_PERFECT_PALLET_PATH)",
                "available": pp is not None,
            }
        )
        return rows

    def list_files(self, project_id: str, *, limit: int = 60) -> list[dict]:
        root = self._project_root(project_id)
        if not root:
            return []
        out: list[dict] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            rel_dir = Path(dirpath).relative_to(root)
            for name in sorted(filenames):
                if Path(name).suffix.lower() in _SKIP_EXT:
                    continue
                rel = rel_dir / name
                out.append(
                    {
                        "path": str(rel).replace("\\", "/"),
                        "name": name,
                        "is_dir": False,
                    }
                )
                if len(out) >= limit:
                    return out
        return out

    def list_docs(self, project_id: str) -> list[dict]:
        root = self._project_root(project_id)
        if not root:
            return []
        patterns = ["**/*.md", "**/README*"]
        docs: list[dict] = []
        for pattern in patterns:
            for p in root.glob(pattern):
                if any(part in _SKIP_DIRS for part in p.parts):
                    continue
                try:
                    rel = p.relative_to(root)
                except ValueError:
                    continue
                if len(docs) >= 30:
                    break
                docs.append(
                    {
                        "path": str(rel).replace("\\", "/"),
                        "name": p.name,
                    }
                )
        return sorted(docs, key=lambda x: x["path"])[:30]

    def build_history(self, limit: int = 15) -> list[dict]:
        rows: list[dict] = []
        for t in self._cursor.list_tasks(limit):
            rows.append(
                {
                    "at": t.get("updated_at") or t.get("created_at"),
                    "task_id": t.get("task_id"),
                    "label": t.get("task_note") or t.get("state_label"),
                    "state": t.get("state"),
                    "state_label": t.get("state_label"),
                    "verify_summary": t.get("verify_summary"),
                }
            )
        if self._ai_hub:
            for t in self._ai_hub.list_tasks(limit):
                rows.append(
                    {
                        "at": t.get("updated_at") or t.get("created_at"),
                        "task_id": t.get("id"),
                        "label": t.get("input_text", "")[:120],
                        "state": t.get("phase"),
                        "state_label": t.get("phase"),
                        "verify_summary": t.get("error"),
                    }
                )
        rows.sort(key=lambda r: r.get("at") or "", reverse=True)
        return rows[:limit]

    def suggestions(self) -> list[dict]:
        active = self._cursor.active_task()
        out: list[dict] = []
        if active and active.get("state") not in ("ready", "failed"):
            out.append(
                {
                    "id": "verify-cursor",
                    "title": "Проверить результат Cursor",
                    "detail": "Запустить pytest после правок в Cursor",
                    "action": "verify",
                }
            )
        if self._ai_hub:
            hub = self._ai_hub.active_task()
            if hub and hub.get("phase") == "awaiting_approve":
                out.append(
                    {
                        "id": "approve-plan",
                        "title": "Утвердить план AI Hub",
                        "detail": hub.get("input_text", "")[:80],
                        "action": "approve",
                        "task_id": hub.get("id"),
                    }
                )
        pp = _resolve_perfect_pallet()
        if pp:
            out.append(
                {
                    "id": "open-perfect-pallet",
                    "title": "Задача для Perfect Pallet",
                    "detail": "Создать handoff с контекстом игры",
                    "action": "new_task",
                    "project_id": "perfect-pallet",
                }
            )
        return out

    def _project_root(self, project_id: str) -> Path | None:
        if project_id == "genesis":
            return self._root
        if project_id == "perfect-pallet":
            return _resolve_perfect_pallet()
        return None

    def snapshot(self) -> dict:
        return {
            "projects": self.list_projects(),
            "suggestions": self.suggestions(),
            "build_history": self.build_history(),
        }
