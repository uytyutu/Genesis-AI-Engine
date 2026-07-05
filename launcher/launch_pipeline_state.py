"""Launch Pipeline verification tiers — programmatic, GUI, CEO manual."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from launcher import paths

STATE_NAME = "launch_pipeline.json"


def _state_path(root: Path | None = None) -> Path:
    return paths.memory_dir(root) / STATE_NAME


def load_pipeline_state(root: Path | None = None) -> dict:
    path = _state_path(root)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_pipeline_state(data: dict, root: Path | None = None) -> None:
    path = _state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def record_programmatic_cycles(count: int, root: Path | None = None) -> None:
    data = load_pipeline_state(root)
    data["programmatic_cycles_count"] = count
    data["programmatic_cycles_passed_at"] = datetime.now(timezone.utc).isoformat()
    save_pipeline_state(data, root)


def record_gui_cycles(count: int, root: Path | None = None) -> None:
    data = load_pipeline_state(root)
    data["gui_cycles_count"] = count
    data["gui_cycles_passed_at"] = datetime.now(timezone.utc).isoformat()
    data.pop("gui_cycles_invalidated_at", None)
    save_pipeline_state(data, root)


def invalidate_gui_cycles(root: Path | None = None, *, reason: str = "") -> None:
    data = load_pipeline_state(root)
    data.pop("gui_cycles_count", None)
    data.pop("gui_cycles_passed_at", None)
    data["gui_cycles_invalidated_at"] = datetime.now(timezone.utc).isoformat()
    if reason:
        data["gui_cycles_invalidated_reason"] = reason
    save_pipeline_state(data, root)


def record_ceo_manual_verify(root: Path | None = None, *, by: str = "CEO") -> None:
    data = load_pipeline_state(root)
    data["ceo_manual_verified_at"] = datetime.now(timezone.utc).isoformat()
    data["ceo_manual_verified_by"] = by
    save_pipeline_state(data, root)


def programmatic_passed(root: Path | None = None, *, min_cycles: int = 10) -> bool:
    data = load_pipeline_state(root)
    return int(data.get("programmatic_cycles_count") or 0) >= min_cycles and bool(
        data.get("programmatic_cycles_passed_at")
    )


def gui_passed(root: Path | None = None, *, min_cycles: int = 10) -> bool:
    data = load_pipeline_state(root)
    if data.get("gui_cycles_invalidated_at"):
        return False
    return int(data.get("gui_cycles_count") or 0) >= min_cycles and bool(
        data.get("gui_cycles_passed_at")
    )


def ceo_manual_verified(root: Path | None = None) -> bool:
    return bool(load_pipeline_state(root).get("ceo_manual_verified_at"))
