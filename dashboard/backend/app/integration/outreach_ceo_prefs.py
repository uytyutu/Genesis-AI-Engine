"""CEO Country Desk prefs — auto-refresh / auto-send toggles (memory file)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


_DEFAULTS: dict[str, Any] = {
    "auto_refresh": False,
    "auto_send": False,
}


def _path(memory_dir: Path | None) -> Path | None:
    if not memory_dir:
        return None
    return Path(memory_dir) / "outreach_ceo_prefs.json"


def load_prefs(memory_dir: Path | None) -> dict[str, Any]:
    path = _path(memory_dir)
    data = dict(_DEFAULTS)
    if path and path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data["auto_refresh"] = bool(raw.get("auto_refresh", False))
                data["auto_send"] = bool(raw.get("auto_send", False))
        except (json.JSONDecodeError, OSError):
            pass
    return data


def save_prefs(memory_dir: Path | None, **updates: Any) -> dict[str, Any]:
    data = load_prefs(memory_dir)
    for key in ("auto_refresh", "auto_send"):
        if key in updates and updates[key] is not None:
            data[key] = bool(updates[key])
    path = _path(memory_dir)
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def outreach_send_allowed(memory_dir: Path | None = None) -> bool:
    """Env gate OR CEO toggle — both still need Resend + legal footer in send path."""
    if os.getenv("GENESIS_OUTREACH_ENABLED", "").strip().lower() == "true":
        return True
    return bool(load_prefs(memory_dir).get("auto_send"))
