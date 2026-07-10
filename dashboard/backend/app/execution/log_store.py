"""Persistent execution step logs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.execution.models import ExecutionResult, StepExecutionRecord


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionLogStore:
    def __init__(self, memory_dir: Path) -> None:
        self._root = memory_dir / "execution" / "runs"
        self._root.mkdir(parents=True, exist_ok=True)

    def save_run(self, result: ExecutionResult) -> Path:
        path = self._root / f"{result.plan_id}.json"
        payload = result.to_dict()
        payload["saved_at"] = _utc_now()
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load_run(self, plan_id: str) -> dict[str, Any] | None:
        path = self._root / f"{plan_id}.json"
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def append_step_log(self, workspace_id: str, record: StepExecutionRecord) -> None:
        log_dir = self._root.parent / "workspaces" / workspace_id / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record.to_dict(), ensure_ascii=False) + "\n"
        with (log_dir / "execution.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(line)
