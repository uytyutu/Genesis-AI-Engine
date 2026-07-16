"""CEO feature flags — kill switches. Path A never imports TikTok workers from here."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[4]
_FEATURES = _REPO_ROOT / "config" / "features.json"


def _ensure_repo_on_path() -> None:
    root = str(_REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def features_file() -> Path:
    return _FEATURES


def load_features() -> dict[str, Any]:
    if not _FEATURES.is_file():
        return {
            "tiktok_enabled": False,
            "media_engine_enabled": False,
            "path_a_independent": True,
        }
    try:
        data = json.loads(_FEATURES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"tiktok_enabled": False, "media_engine_enabled": False}
    return data if isinstance(data, dict) else {"tiktok_enabled": False}


def snapshot() -> dict[str, Any]:
    data = load_features()
    enabled = data.get("tiktok_enabled") is True
    return {
        "tiktok_enabled": enabled,
        "media_engine_enabled": data.get("media_engine_enabled") is True,
        "path_a_independent": True,
        "status_ru": "активно" if enabled else "выключено (безопасно)",
        "principle_ru": (
            "Ролик только из повторяющейся закономерности → человек → /order. "
            "Не ради просмотров. Content Engine → TikTok/YouTube/LinkedIn/Blog — Horizon."
        ),
        "module": "modules/tiktok_factory",
        "config_path": str(_FEATURES.as_posix()),
    }


def activate_tiktok(*, ceo_confirmed: bool) -> dict[str, Any]:
    if not ceo_confirmed:
        raise ValueError("ceo_confirm_required")
    data = load_features()
    data["tiktok_enabled"] = True
    data.setdefault("media_engine_enabled", False)
    _FEATURES.parent.mkdir(parents=True, exist_ok=True)
    _FEATURES.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return snapshot()


def deactivate_tiktok() -> dict[str, Any]:
    data = load_features()
    data["tiktok_enabled"] = False
    _FEATURES.parent.mkdir(parents=True, exist_ok=True)
    _FEATURES.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return snapshot()


def try_build_scenario(**kwargs: Any) -> dict[str, Any]:
    """No-op when disabled — never starts workers."""
    if load_features().get("tiktok_enabled") is not True:
        return {"ok": False, "reason": "tiktok_disabled", "draft": None}
    _ensure_repo_on_path()
    from modules.tiktok_factory.scenario_pipeline import build_educational_scenario

    draft = build_educational_scenario(**kwargs)
    return {"ok": True, "draft": draft.to_dict()}
