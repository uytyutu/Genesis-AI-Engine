from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol, runtime_checkable

from brain.models import QueuedTaskRecord


@runtime_checkable
class QueueStorage(Protocol):
    """Abstract queue persistence — swap JSON for PostgreSQL without changing Brain."""

    def load_all(self) -> list[QueuedTaskRecord]: ...

    def save_all(self, records: list[QueuedTaskRecord]) -> None: ...


class JsonQueueStorage:
    """v0.1 implementation: human-readable JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def load_all(self) -> list[QueuedTaskRecord]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        items = raw.get("records", [])
        return [QueuedTaskRecord.from_dict(item) for item in items]

    def save_all(self, records: list[QueuedTaskRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "records": [record.to_dict() for record in records],
        }
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp_path.write_text(text, encoding="utf-8")
        os.replace(tmp_path, self._path)
