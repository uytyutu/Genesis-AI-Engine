"""Revenue Replay v0 — сохранить и повторить последовательность полевого эксперimenta."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPLAY_STATE_FILE = "revenue_replay_last.json"


def save_replay_snapshot(memory_dir: Path, snapshot: dict[str, Any]) -> Path:
    path = memory_dir / REPLAY_STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {**snapshot, "saved_at": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_replay_snapshot(memory_dir: Path) -> dict[str, Any] | None:
    path = memory_dir / REPLAY_STATE_FILE
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def build_snapshot_from_run(
    *,
    workers: int,
    feed_ok: bool,
    tick_tasks: int,
    submit_result: dict[str, Any] | None,
    toloka_status: dict[str, Any],
) -> dict[str, Any]:
    return {
        "label_ru": "Последний полевой прогон",
        "workers": workers,
        "feed_ok": feed_ok,
        "tick_tasks": tick_tasks,
        "submit_ok": bool((submit_result or {}).get("ok")),
        "submit_message": (submit_result or {}).get("message"),
        "submitted_count": int(toloka_status.get("submitted_count") or 0),
        "pipeline_success_count": int(toloka_status.get("pipeline_success_count") or 0),
        "last_run_status": toloka_status.get("last_run_status"),
        "steps_ru": [
            "POST /api/farm/feed",
            f"POST /api/farm/start?workers={workers}",
            "POST /api/farm/tick",
            "POST /api/farm/toloka/submit",
        ],
    }
