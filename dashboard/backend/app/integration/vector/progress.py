"""Persist Vector wizard progress — resume after refresh/restart."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe(key: str) -> str:
    return re.sub(r"[^\w\-]", "_", key)[:96] or "anon"


class VectorProgressStore:
    """User Data Protection: progress under memory/vector/progress/ — never invent completion."""

    def __init__(self, memory_dir: Path) -> None:
        self._root = Path(memory_dir) / "vector" / "progress"
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, scope: str, subject_id: str) -> Path:
        return self._root / f"{_safe(scope)}__{_safe(subject_id)}.json"

    def load(self, scope: str, subject_id: str) -> dict[str, Any]:
        path = self._path(scope, subject_id)
        if not path.is_file():
            return {
                "scope": scope,
                "subject_id": subject_id,
                "learning_mode": None,
                "step_id": None,
                "completed_steps": [],
                "updated_at": None,
            }
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return {
                    "scope": scope,
                    "subject_id": subject_id,
                    "learning_mode": raw.get("learning_mode"),
                    "step_id": raw.get("step_id"),
                    "completed_steps": list(raw.get("completed_steps") or []),
                    "updated_at": raw.get("updated_at"),
                }
        except (OSError, json.JSONDecodeError):
            pass
        return {
            "scope": scope,
            "subject_id": subject_id,
            "learning_mode": None,
            "step_id": None,
            "completed_steps": [],
            "updated_at": None,
        }

    def save(
        self,
        scope: str,
        subject_id: str,
        *,
        learning_mode: str | None = None,
        step_id: str | None = None,
        mark_completed: str | None = None,
    ) -> dict[str, Any]:
        cur = self.load(scope, subject_id)
        if learning_mode in ("skip", "show"):
            cur["learning_mode"] = learning_mode
        if step_id is not None:
            cur["step_id"] = step_id or None
        done = list(cur.get("completed_steps") or [])
        if mark_completed and mark_completed not in done:
            done.append(mark_completed)
        cur["completed_steps"] = done
        cur["updated_at"] = _now()
        path = self._path(scope, subject_id)
        path.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
        return cur
