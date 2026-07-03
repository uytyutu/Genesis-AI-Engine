from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class AuditStorage(Protocol):
    """Abstract audit log — swap JSONL for SQLite/PostgreSQL without changing Brain."""

    def append_event(self, event: dict) -> None: ...

    def append_events(self, events: list[dict]) -> None: ...

    def read_all(self) -> list[dict]:
        """Read all events in order. Used by tests and future Dashboard."""
        ...


class JsonlAuditStorage:
    """v0.1 implementation: append-only JSON Lines file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def append_event(self, event: dict) -> None:
        self.append_events([event])

    def append_events(self, events: list[dict]) -> None:
        if not events:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def read_all(self) -> list[dict]:
        if not self._path.exists():
            return []
        events: list[dict] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                events.append(json.loads(stripped))
        return events
