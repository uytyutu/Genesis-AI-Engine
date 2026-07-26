"""TikTok Horizon Stage 1 — foundation without video/publish."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.integration.feature_flags_service import activate_tiktok
from modules.tiktok_horizon import HorizonService, STAGE1_CAPABILITIES


def _patch_features(tmp_path: Path, monkeypatch, *, enabled: bool = False):
    features = tmp_path / "features.json"
    features.write_text(
        json.dumps(
            {
                "tiktok_enabled": enabled,
                "media_engine_enabled": False,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "app.integration.feature_flags_service._FEATURES",
        features,
    )
    monkeypatch.setattr(
        "modules.tiktok_factory.gate._FEATURES_PATH",
        features,
    )
    return features


def _sample_observations():
    return [
        {
            "signal_id": "s1",
            "observed_at": "2026-07-20T10:00:00+00:00",
            "topic_tokens": ["handwerk", "anruf", "landing"],
            "duration_sec": 22,
            "hook_style": "question",
            "editing_style": "fast_cut",
            "caption_style": "short_cta",
            "hashtag_pattern": ["handwerk", "tipps"],
            "engagement_proxy": 2.4,
        },
        {
            "signal_id": "s2",
            "observed_at": "2026-07-21T11:00:00+00:00",
            "topic_tokens": ["handwerk", "whatsapp", "anruf"],
            "duration_sec": 28,
            "hook_style": "question",
            "editing_style": "fast_cut",
            "caption_style": "short_cta",
            "hashtag_pattern": ["handwerk"],
            "engagement_proxy": 3.1,
        },
        {
            "signal_id": "s3",
            "observed_at": "2026-07-21T12:00:00+00:00",
            "topic_tokens": ["seo", "local", "google"],
            "duration_sec": 35,
            "hook_style": "myth",
            "editing_style": "talking_head",
            "caption_style": "story",
            "hashtag_pattern": ["seo"],
            "engagement_proxy": 1.2,
        },
    ]


def test_stage1_capabilities_video_off():
    assert STAGE1_CAPABILITIES["video_generation"] is False
    assert STAGE1_CAPABILITIES["auto_publish"] is False
    assert STAGE1_CAPABILITIES["human_review"] is True


def test_blocked_when_kill_switch_off(tmp_path: Path, monkeypatch):
    _patch_features(tmp_path, monkeypatch, enabled=False)
    svc = HorizonService(tmp_path / "mem")
    with pytest.raises(ValueError, match="tiktok_disabled"):
        svc.ingest_observations(_sample_observations())


def test_pipeline_trend_to_queue(tmp_path: Path, monkeypatch):
    _patch_features(tmp_path, monkeypatch, enabled=False)
    activate_tiktok(ceo_confirmed=True)
    svc = HorizonService(tmp_path / "mem")

    ing = svc.ingest_observations(_sample_observations())
    assert ing["ingested"] == 3
    assert len(ing["trends"]) >= 1

    dash = svc.dashboard()
    assert dash["stage"] >= 1
    assert dash["capabilities"]["video_generation"] is False
    assert dash["visibility"]["owner_internal_only"] is True

    drafts = svc.generate_drafts(limit=2, language="ru")
    assert len(drafts) == 2
    draft = drafts[0]
    assert draft["status"] == "review"
    assert draft["prompt"]["video_api_enabled"] is False
    assert "quality" in draft
    assert "publish_window" in draft
    assert draft["publish_window"]["confidence"] <= 1.0

    checklist = svc.review_checklist(draft["id"])
    assert any(i["id"] == "hook_seconds" for i in checklist["items"])

    edited = svc.apply_review_edits(
        draft["id"],
        {"hook_seconds": "Новый хук за 3 секунды", "caption": "Новое описание"},
    )
    assert edited["human_edited"] is True
    assert edited["script"]["hook_seconds"].startswith("Новый хук")

    approved = svc.approve_draft(draft["id"])
    assert approved["status"] == "approved"

    queued = svc.enqueue_draft(draft["id"])
    assert queued["status"] == "queued"
    assert queued["publish_enabled"] is False
    assert queued["publish_blocked"] == "stage1_no_publish"

    # Publish must stay disabled
    pub = svc.scheduler.attempt_publish(queued["id"])
    assert pub["ok"] is False
    assert pub["error"] == "publish_disabled_stage1"

    video = svc.video.generate({"prompt": "x"})
    assert video.stage1_disabled is True


def test_ideas_use_diverse_styles(tmp_path: Path, monkeypatch):
    _patch_features(tmp_path, monkeypatch, enabled=False)
    activate_tiktok(ceo_confirmed=True)
    svc = HorizonService(tmp_path / "mem")
    svc.ingest_observations(_sample_observations())
    drafts = svc.generate_drafts(limit=3)
    styles = {d["style_variant"] for d in drafts}
    assert len(styles) >= 2
