"""Analytics store — Stage 1: schema + ingest interface only."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ANALYTICS_FIELDS = (
    "views",
    "likes",
    "comments",
    "shares",
    "saves",
    "audience_retention",
    "follows",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AnalyticsStore:
    def __init__(self, root: Path) -> None:
        self._path = root / "analytics.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("", encoding="utf-8")

    def schema(self) -> dict[str, Any]:
        return {
            "fields": list(ANALYTICS_FIELDS),
            "note_ru": "Stage 1: модели и запись метрик. Live TikTok analytics — после официального API.",
        }

    def list_rows(self) -> list[dict[str, Any]]:
        return _read_jsonl(self._path)

    def record(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {
            "id": f"an-{uuid.uuid4().hex[:10]}",
            "draft_id": payload.get("draft_id"),
            "queue_id": payload.get("queue_id"),
            "published_at": payload.get("published_at"),
            "recorded_at": _now(),
            "source": payload.get("source") or "manual",
        }
        for key in ANALYTICS_FIELDS:
            if key in payload:
                try:
                    row[key] = float(payload[key])
                except (TypeError, ValueError):
                    row[key] = payload[key]
        # Optional proxy for Publish Intelligence before real views exist
        if "watch_proxy" in payload:
            row["watch_proxy"] = float(payload["watch_proxy"])
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row


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
