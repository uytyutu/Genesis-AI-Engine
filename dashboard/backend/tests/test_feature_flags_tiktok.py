"""Feature flags + TikTok kill switch (dormant by default)."""

from __future__ import annotations

import json
from pathlib import Path

from app.integration.feature_flags_service import (
    activate_tiktok,
    deactivate_tiktok,
    load_features,
    snapshot,
    try_build_scenario,
)


def test_tiktok_kill_switch_default_off(tmp_path: Path, monkeypatch):
    features = tmp_path / "features.json"
    features.write_text(
        json.dumps({"tiktok_enabled": False, "media_engine_enabled": False}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "app.integration.feature_flags_service._FEATURES",
        features,
    )
    snap = snapshot()
    assert snap["tiktok_enabled"] is False
    assert snap["path_a_independent"] is True
    blocked = try_build_scenario(
        niche="Kfz",
        city="Köln",
        pattern_issues=["Kein HTTPS"],
    )
    assert blocked["ok"] is False
    assert blocked["reason"] == "tiktok_disabled"


def test_tiktok_activate_requires_ceo_flag(tmp_path: Path, monkeypatch):
    features = tmp_path / "features.json"
    features.write_text(json.dumps({"tiktok_enabled": False}), encoding="utf-8")
    monkeypatch.setattr("app.integration.feature_flags_service._FEATURES", features)

    try:
        activate_tiktok(ceo_confirmed=False)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "ceo_confirm" in str(exc)

    out = activate_tiktok(ceo_confirmed=True)
    assert out["tiktok_enabled"] is True
    data = json.loads(features.read_text(encoding="utf-8"))
    assert data["tiktok_enabled"] is True
    deactivate_tiktok()
    assert load_features()["tiktok_enabled"] is False
