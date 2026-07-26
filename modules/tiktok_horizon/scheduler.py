"""Scheduler — Stage 1 queue only (no publish execution)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Scheduler:
    """Generated → Review → Approve → Queue. Publish is a no-op in Stage 1."""

    def __init__(self, root: Path) -> None:
        self._path = root / "queue.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("", encoding="utf-8")

    def list_queue(self) -> list[dict[str, Any]]:
        rows = _read_jsonl(self._path)
        rows.sort(key=lambda r: r.get("queued_at") or "", reverse=True)
        return rows

    def enqueue(self, draft: dict[str, Any]) -> dict[str, Any]:
        if draft.get("status") != "approved":
            raise ValueError("draft_not_approved")
        item = {
            "id": f"q-{uuid.uuid4().hex[:10]}",
            "draft_id": draft.get("id"),
            "title": draft.get("title"),
            "status": "queued",
            "queue_state": "waiting",
            "publish_enabled": False,
            "publish_blocked": "stage1_no_publish",
            "publish_note_ru": "Stage 1: материал в очереди. Публикация отключена.",
            "publish_window": draft.get("publish_window"),
            "queued_at": _now(),
            "channel": "tiktok",
        }
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
        return item

    def attempt_publish(self, _queue_id: str) -> dict[str, Any]:
        return {
            "ok": False,
            "error": "publish_disabled_stage1",
            "note_ru": "Автопубликация и ручной publish API отключены до Stage 2+.",
        }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out
