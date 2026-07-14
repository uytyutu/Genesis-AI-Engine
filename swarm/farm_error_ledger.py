"""Error Ledger v0 — log exchange rejects with taxonomy (QC, not auto-fix)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LEDGER_FILENAME = "farm_error_ledger.jsonl"

TAXONOMY_RU = {
    "format": "Ошибка формата / схемы данных",
    "content": "Качество разметки / валидация контента",
    "data": "Неполные или некорректные поля",
    "api": "API / авторизация / HTTP",
    "pipeline": "Pipeline run failed",
    "unknown": "Причина не классифицирована",
}


def classify_error(*, message: str, http_status: int | None = None, context: str = "") -> str:
    """Deterministic taxonomy — no LLM."""
    text = f"{message} {context}".lower()
    if http_status in {401, 403, 404, 429, 500, 502, 503}:
        return "api"
    if context == "pipeline_run":
        return "pipeline"
    if any(k in text for k in ("schema", "json", "field", "format", "invalid type", "required")):
        return "format"
    if any(k in text for k in ("quality", "label", "confidence", "validation", "reject")):
        return "content"
    if any(k in text for k in ("missing", "empty", "null", "task_id", "dataset")):
        return "data"
    if re.search(r"\b4\d{2}\b|\b5\d{2}\b", text):
        return "api"
    return "unknown"


class FarmErrorLedger:
    def __init__(self, memory_dir: Path) -> None:
        self._path = memory_dir / LEDGER_FILENAME

    def append(
        self,
        *,
        exchange: str,
        stage: str,
        message: str,
        http_status: int | None = None,
        batch_size: int = 0,
        sample_task_ids: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        taxonomy = classify_error(message=message, http_status=http_status, context=stage)
        entry: dict[str, Any] = {
            "at": datetime.now(timezone.utc).isoformat(),
            "exchange": exchange,
            "stage": stage,
            "taxonomy": taxonomy,
            "taxonomy_ru": TAXONOMY_RU.get(taxonomy, TAXONOMY_RU["unknown"]),
            "message": (message or "")[:500],
            "http_status": http_status,
            "batch_size": batch_size,
            "sample_task_ids": (sample_task_ids or [])[:5],
        }
        if extra:
            entry["extra"] = extra
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def read_recent(self, *, limit: int = 20) -> list[dict[str, Any]]:
        if not self._path.is_file():
            return []
        lines = [ln for ln in self._path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        out: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    out.append(row)
            except json.JSONDecodeError:
                continue
        return out

    def summary(self) -> dict[str, Any]:
        recent = self.read_recent(limit=200)
        by_taxonomy: dict[str, int] = {}
        by_exchange: dict[str, int] = {}
        for row in recent:
            tax = str(row.get("taxonomy") or "unknown")
            by_taxonomy[tax] = by_taxonomy.get(tax, 0) + 1
            ex = str(row.get("exchange") or "unknown")
            by_exchange[ex] = by_exchange.get(ex, 0) + 1
        last = recent[-1] if recent else None
        hint_ru = None
        if by_taxonomy.get("format", 0) >= 2:
            hint_ru = "Повтор format — проверь DATASET_FIELDS и export.jsonl"
        elif by_taxonomy.get("content", 0) >= 2:
            hint_ru = "Повтор content — качество разметки Workers, не API"
        elif by_taxonomy.get("api", 0) >= 2:
            hint_ru = "Повтор api — ключ Toloka, circuit breaker, Safe Mode"
        return {
            "total_logged": len(recent),
            "last_entry": last,
            "by_taxonomy": by_taxonomy,
            "by_exchange": by_exchange,
            "taxonomy_labels_ru": TAXONOMY_RU,
            "hint_ru": hint_ru,
            "note_ru": "Error Ledger v0 — только фиксация reject, без auto-fix",
        }
