"""Trend Database — persistent trend pattern store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modules.tiktok_horizon.models import TrendRecord


class TrendDatabase:
    def __init__(self, root: Path) -> None:
        self._path = root / "trends.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("", encoding="utf-8")

    def upsert(self, record: TrendRecord) -> TrendRecord:
        rows = self.list_all()
        by_id = {r["trend_id"]: r for r in rows if r.get("trend_id")}
        by_id[record.trend_id] = record.to_dict()
        self._rewrite(list(by_id.values()))
        return record

    def list_all(self) -> list[dict[str, Any]]:
        return _read_jsonl(self._path)

    def top_by_growth(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.list_all()
        rows.sort(key=lambda r: float(r.get("growth_score") or 0), reverse=True)
        return rows[:limit]

    def get(self, trend_id: str) -> dict[str, Any] | None:
        for row in self.list_all():
            if row.get("trend_id") == trend_id:
                return row
        return None

    def _rewrite(self, rows: list[dict[str, Any]]) -> None:
        with self._path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")


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
