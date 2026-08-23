"""Horizon Media Engine shell."""

from app.integration.horizon_studio import build_horizon_manifest


def test_horizon_manifest_internal_only():
    m = build_horizon_manifest()
    assert m["ok"] is True
    assert m["stage"] == "internal_only"
    assert m["client_sales"] is False
    assert m["video_generation_enabled"] is False
    assert m["studio_steps"][-1]["id"] == "prompt_director"
    assert "quality_gate" in m["creative_bible"]
    assert len(m["platforms"]) >= 6
