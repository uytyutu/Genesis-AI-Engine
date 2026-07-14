"""Commercial experiment journal — канал / итог / дата (Decision Memory v0)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

JOURNAL_FILENAME = "commercial_experiments.jsonl"


def _journal_path(memory_dir: Path) -> Path:
    return memory_dir / JOURNAL_FILENAME


def append_experiment(
    memory_dir: Path,
    *,
    channel: str,
    outcome_ru: str,
    outcome_code: str,
    detail_ru: str = "",
    vre_level: int = 0,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "date_ru": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "channel": channel,
        "outcome_ru": outcome_ru,
        "outcome_code": outcome_code,
        "detail_ru": detail_ru,
        "vre_level": vre_level,
    }
    if extra:
        entry["extra"] = extra
    path = _journal_path(memory_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def list_experiments(memory_dir: Path, *, limit: int = 30) -> list[dict[str, Any]]:
    path = _journal_path(memory_dir)
    if not path.is_file():
        return []
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    out: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                out.append(row)
        except json.JSONDecodeError:
            continue
    return list(reversed(out))


def ensure_baseline_experiments(memory_dir: Path) -> None:
    """Seed journal once if empty — CEO-visible history template."""
    path = _journal_path(memory_dir)
    if path.is_file() and path.stat().st_size > 0:
        return
    defaults = [
        ("toloka_requester", "Доход не подтверждён", "UNVERIFIED", "Pipeline v2 requester — ждём wallet CEO"),
        ("scale_ai", "Проверяется", "PENDING", "Адаптер есть · нужен ключ и аккаунт"),
        ("direct_b2b", "Первый клиент", "HORIZON", "Virtus site / Vector — Mission 1+"),
    ]
    for channel, outcome, code, detail in defaults:
        append_experiment(
            memory_dir,
            channel=channel,
            outcome_ru=outcome,
            outcome_code=code,
            detail_ru=detail,
            vre_level=0,
        )
