from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class BrainConfig:
    memory_dir: Path = Path("memory")

    @property
    def queue_path(self) -> Path:
        return self.memory_dir / "queue.json"

    @property
    def audit_path(self) -> Path:
        return self.memory_dir / "audit.jsonl"
