"""Load legal entity config from memory — separate from product code."""

from __future__ import annotations

import json
from pathlib import Path

from app.legal.entity_schema import LegalEntityConfig

_ENTITY_FILENAME = "legal_entity.json"
_EXAMPLE_FILENAME = "legal_entity.example.json"
_PACKAGE_EXAMPLE = Path(__file__).resolve().parent / "legal_entity.example.json"


class LegalEntityStore:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._memory.mkdir(parents=True, exist_ok=True)

    def _entity_path(self) -> Path:
        return self._memory / _ENTITY_FILENAME

    def _example_path(self) -> Path:
        mem = self._memory / _EXAMPLE_FILENAME
        return mem if mem.is_file() else _PACKAGE_EXAMPLE

    def load(self) -> LegalEntityConfig:
        path = self._entity_path()
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return LegalEntityConfig.from_dict(data)
            except (json.JSONDecodeError, OSError):
                pass
        example = self._example_path()
        if example.is_file():
            try:
                data = json.loads(example.read_text(encoding="utf-8"))
                return LegalEntityConfig.from_dict(data)
            except (json.JSONDecodeError, OSError):
                pass
        return LegalEntityConfig()

    def save(self, config: LegalEntityConfig) -> None:
        self._entity_path().write_text(
            json.dumps(config.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def status(self) -> dict:
        cfg = self.load()
        return {
            "interview_completed": cfg.interview_completed,
            "impressum_publishable": cfg.is_impressum_publishable(),
            "datenschutz_publishable": cfg.is_datenschutz_publishable(),
            "missing_impressum": cfg.missing_impressum_fields(),
            "missing_datenschutz": cfg.missing_datenschutz_fields(),
            "documents_last_review": cfg.documents_last_review,
            "entity_path": str(self._entity_path()),
        }
