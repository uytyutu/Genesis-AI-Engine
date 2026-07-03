"""Owner notifications for paid orders and pipeline events."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"


class OwnerNotificationService:
    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._memory.mkdir(parents=True, exist_ok=True)

    def notify(self, *, title: str, message: str, order_id: str | None = None) -> dict:
        row = {
            "at": datetime.now(timezone.utc).isoformat(),
            "title": title,
            "message": message,
            "order_id": order_id,
            "read": False,
        }
        path = self._memory / "owner_notifications.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def list_recent(self, limit: int = 20) -> list[dict]:
        path = self._memory / "owner_notifications.jsonl"
        if not path.is_file():
            return []
        rows: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        rows.sort(key=lambda r: str(r.get("at", "")), reverse=True)
        return rows[:limit]
