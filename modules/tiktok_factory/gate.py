"""Feature kill switch for TikTok / Media Horizon."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FEATURES_PATH = _REPO_ROOT / "config" / "features.json"


def features_path() -> Path:
    return _FEATURES_PATH


def load_features() -> dict[str, Any]:
    path = _FEATURES_PATH
    if not path.is_file():
        return {"tiktok_enabled": False, "media_engine_enabled": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"tiktok_enabled": False, "media_engine_enabled": False}
    if not isinstance(data, dict):
        return {"tiktok_enabled": False, "media_engine_enabled": False}
    return data


def is_tiktok_enabled() -> bool:
    return bool(load_features().get("tiktok_enabled") is True)


def require_tiktok_enabled() -> None:
    if not is_tiktok_enabled():
        raise RuntimeError("tiktok_disabled")


def set_tiktok_enabled(enabled: bool) -> dict[str, Any]:
    """CEO kill switch writer — only flips flag, starts no workers."""
    data = load_features()
    data["tiktok_enabled"] = bool(enabled)
    data.setdefault("media_engine_enabled", False)
    _FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
    _FEATURES_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return data
