"""Genesis AI Hub — task orchestration (Stage 1). Plan → Approve → Cursor dispatch."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.integration.cursor_handoff_service import CursorHandoffService


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _detect_project_id(text: str) -> str:
    lower = text.lower()
    if "perfect pallet" in lower or "perfect-pallet" in lower or "паллет" in lower:
        return "perfect-pallet"
    return "genesis"


def _build_plan(input_text: str, project_id: str) -> list[dict]:
    """Rule-based plan until LLM routing (Stage 2)."""
    steps: list[dict] = [
        {
            "id": "analyze",
            "title": "Анализ проекта и контекста",
            "capability": "chat",
            "provider_id": "genesis-rules",
            "requires_approve": False,
            "status": "done",
        },
        {
            "id": "plan",
            "title": "План изменений для CEO",
            "capability": "chat",
            "provider_id": "genesis-rules",
            "requires_approve": False,
            "status": "done",
        },
    ]

    lower = input_text.lower()
    if any(w in lower for w in ("добав", "add", "создай", "create", "implement", "fix", "исправ")):
        steps.append(
            {
                "id": "implement",
                "title": "Реализация через Development Provider (Cursor)",
                "capability": "code",
                "provider_id": "cursor-tool",
                "tool_id": "cursor-tool",
                "requires_approve": True,
                "status": "pending",
            }
        )
    steps.extend(
        [
            {
                "id": "verify",
                "title": "Проверка (pytest + system check)",
                "capability": "tool",
                "provider_id": "genesis-rules",
                "requires_approve": False,
                "status": "pending",
            },
            {
                "id": "report",
                "title": "Отчёт CEO в Virtus Core",
                "capability": "chat",
                "provider_id": "genesis-rules",
                "requires_approve": False,
                "status": "pending",
            },
        ]
    )
    return steps


def _plan_summary(input_text: str, project_id: str) -> str:
    proj = "Perfect Pallet" if project_id == "perfect-pallet" else "Virtus Core"
    lines = [
        f"Проект: {proj}",
        "",
        "Задача:",
        input_text.strip(),
        "",
        "Предлагаемые шаги:",
        "1. Собрать контекст (docs, PROJECT_STATE, связанные файлы)",
        "2. Сформировать промпт для Development Provider",
        "3. После вашего ✔ — передать в Cursor",
        "4. Проверить тесты и показать отчёт",
    ]
    if project_id == "perfect-pallet":
        lines.append("5. Учесть Unity-сцены, gameplay scripts и North Star docs")
    return "\n".join(lines)


class AiHubService:
    def __init__(self, memory_dir: Path, cursor: CursorHandoffService) -> None:
        self._memory = memory_dir
        self._cursor = cursor
        self._memory.mkdir(parents=True, exist_ok=True)

    def _path(self) -> Path:
        return self._memory / "ai_hub_tasks.json"

    def _load(self) -> list[dict]:
        path = self._path()
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, tasks: list[dict]) -> None:
        self._path().write_text(
            json.dumps(tasks[-40:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _upsert(self, task: dict) -> dict:
        tasks = self._load()
        tasks = [t for t in tasks if t.get("id") != task.get("id")]
        tasks.append(task)
        self._save(tasks)
        return self._enrich(task)

    def _enrich(self, task: dict) -> dict:
        cursor_id = task.get("cursor_task_id")
        cursor_task = self._cursor.get_task(cursor_id) if cursor_id else None
        if not cursor_task and task.get("phase") in ("dispatch", "executing", "verify", "report"):
            cursor_task = self._cursor.active_task()
            if cursor_task and cursor_task.get("task_note") == task.get("input_text"):
                task["cursor_task_id"] = cursor_task.get("task_id")

        phase = task.get("phase", "intake")
        if cursor_task:
            cstate = cursor_task.get("state", "")
            if cstate == "ready":
                phase = "report"
                task["phase"] = phase
            elif cstate == "failed":
                phase = "failed"
                task["phase"] = phase
            elif cstate in ("verifying",):
                phase = "verify"
                task["phase"] = phase
            elif cstate in ("awaiting_cursor", "cursor_opened", "clipboard_ready", "prompt_ready"):
                phase = "executing"
                task["phase"] = phase

        return {
            **task,
            "phase": phase,
            "cursor_task": cursor_task,
            "plan_summary": task.get("plan_summary") or "",
        }

    def create_task(
        self,
        input_text: str,
        *,
        locale: str = "ru",
        project_id: str | None = None,
        input_type: str = "text",
    ) -> dict:
        text = input_text.strip()
        if not text:
            raise ValueError("input_text required")
        pid = project_id or _detect_project_id(text)
        task_id = f"hub-{uuid.uuid4().hex[:12]}"
        plan = _build_plan(text, pid)
        task = {
            "id": task_id,
            "input_text": text,
            "input_type": input_type,
            "locale": locale,
            "project_id": pid,
            "phase": "awaiting_approve",
            "plan": plan,
            "plan_summary": _plan_summary(text, pid),
            "approved_at": None,
            "cursor_task_id": None,
            "error": None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        return self._upsert(task)

    def approve_task(self, task_id: str, *, auto_open: bool = True) -> dict:
        tasks = self._load()
        raw = next((t for t in tasks if t.get("id") == task_id), None)
        if not raw:
            raise ValueError("task not found")
        if raw.get("phase") not in ("awaiting_approve", "plan_ready"):
            raise ValueError("task not awaiting approve")

        note = raw.get("plan_summary") or raw.get("input_text", "")
        handoff = self._cursor.submit_task(note, auto_open=auto_open)
        cursor_task = handoff.get("task") or {}
        raw["approved_at"] = _now()
        raw["phase"] = "executing"
        raw["cursor_task_id"] = cursor_task.get("task_id")
        raw["updated_at"] = _now()
        for step in raw.get("plan", []):
            if step.get("id") == "implement":
                step["status"] = "active"
        return self._upsert(raw)

    def verify_task(self, task_id: str) -> dict:
        raw = next((t for t in self._load() if t.get("id") == task_id), None)
        if not raw:
            raise ValueError("task not found")
        cid = raw.get("cursor_task_id")
        result = self._cursor.verify_task(cid)
        raw["updated_at"] = _now()
        if result.get("ok"):
            raw["phase"] = "report"
            for step in raw.get("plan", []):
                if step.get("id") in ("verify", "report"):
                    step["status"] = "done"
        else:
            raw["phase"] = "failed"
            raw["error"] = result.get("message")
        self._upsert(raw)
        return {**result, "hub_task": self.get_task(task_id)}

    def get_task(self, task_id: str) -> dict | None:
        for t in self._load():
            if t.get("id") == task_id:
                return self._enrich(t)
        return None

    def active_task(self) -> dict | None:
        tasks = self._load()
        for t in reversed(tasks):
            if t.get("phase") not in ("report", "failed", "cancelled"):
                return self._enrich(t)
        return self._enrich(tasks[-1]) if tasks else None

    def list_tasks(self, limit: int = 20) -> list[dict]:
        tasks = self._load()
        return [self._enrich(t) for t in reversed(tasks[-limit:])]

    def cancel_task(self, task_id: str) -> dict:
        raw = next((t for t in self._load() if t.get("id") == task_id), None)
        if not raw:
            raise ValueError("task not found")
        raw["phase"] = "cancelled"
        raw["updated_at"] = _now()
        return self._upsert(raw)
