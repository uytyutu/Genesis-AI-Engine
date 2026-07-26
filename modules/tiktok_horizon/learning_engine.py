"""Learning Engine — Stage 1 architecture: record outcomes, suggest adjustments later."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LearningEngine:
    """Persists feedback loops. Stage 1 does not auto-rewrite generators."""

    def __init__(self, root: Path) -> None:
        self._path = root / "learning.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("", encoding="utf-8")

    def record_event(self, event: dict[str, Any]) -> dict[str, Any]:
        row = {
            "recorded_at": _now(),
            "event_type": str(event.get("event_type") or "feedback")[:60],
            "draft_id": event.get("draft_id"),
            "payload": event.get("payload") or {},
            "note_ru": "Stage 1: событие сохранено. Автоулучшение генераторов — после накопления статистики.",
        }
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def summary(self) -> dict[str, Any]:
        rows = _read_jsonl(self._path)
        return {
            "events": len(rows),
            "improves": [
                "idea_selection",
                "script_structure",
                "publish_timing",
                "prompt_quality",
            ],
            "active": False,
            "note_ru": "Архитектура готова. Самообучение включится, когда появятся реальные метрики публикаций.",
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
