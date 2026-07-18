"""Video Factory v0 — CEO Horizon niche; Path A stays independent."""

from __future__ import annotations

import json
from pathlib import Path

from app.integration.feature_flags_service import activate_tiktok, deactivate_tiktok
from app.integration.sales_order_service import SalesOrderService
from app.integration.video_factory_service import (
    VideoFactoryService,
    audit_video_factory_background,
    clear_video_workers_for_tests,
    register_video_worker_for_tests,
)


class _Factory:
    def submit(self, intent):  # noqa: ANN001
        return {"product_id": "prod-test-1"}

    class _Inner:
        def get_product(self, product_id: str):  # noqa: ANN001
            return {"id": product_id}

    _factory = _Inner()


def _patch_features(tmp_path: Path, monkeypatch, *, enabled: bool = False):
    features = tmp_path / "features.json"
    features.write_text(
        json.dumps(
            {
                "tiktok_enabled": enabled,
                "media_engine_enabled": False,
                "video_factory": {
                    "channels": {
                        "tiktok": {"stage": "dormant"},
                        "youtube_shorts": {"stage": "dormant"},
                        "instagram_reels": {"stage": "dormant"},
                    },
                    "capcut_connected": False,
                    "payout_mode": "owner_platform_only",
                },
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


def test_create_draft_blocked_when_off(tmp_path: Path, monkeypatch):
    _patch_features(tmp_path, monkeypatch, enabled=False)
    svc = VideoFactoryService(tmp_path / "mem")
    try:
        svc.create_draft_from_pattern(
            niche="Kfz",
            city="Köln",
            pattern_issues=["Kein HTTPS"],
        )
        assert False, "expected tiktok_disabled"
    except ValueError as exc:
        assert str(exc) == "tiktok_disabled"


def test_create_approve_queue_when_on(tmp_path: Path, monkeypatch):
    _patch_features(tmp_path, monkeypatch, enabled=False)
    activate_tiktok(ceo_confirmed=True)
    svc = VideoFactoryService(tmp_path / "mem")
    draft = svc.create_draft_from_pattern(
        niche="Kfz",
        city="Köln",
        pattern_issues=["Kein WhatsApp", "Langsame Seite"],
        source="manual",
    )
    assert draft["id"].startswith("draft-")
    assert draft["status"] == "draft"
    assert draft["source"] == "manual"
    assert draft["scenario"]["hook_de"]

    approved = svc.approve_draft(draft["id"])
    assert approved["status"] == "approved"
    assert len(svc.list_library()) >= 1

    queued = svc.queue_for_channel(draft["id"], "tiktok")
    assert queued["status"] == "blocked"
    assert queued["display_status"] == "Blocked"
    assert queued["queue_state"] == "queued"
    assert queued["block_reason_code"] == "tiktok_connector_missing"
    assert "TikTok connector" in (queued["block_reason_ru"] or "")
    assert queued["publish_blocked"] == "awaiting_connector"
    assert queued["channel"] == "tiktok"
    assert queued["source"] == "manual"
    assert len(svc.list_queue()) == 1

    earn = svc.earnings_snapshot()
    assert earn["balance_in_virtus"] == 0
    assert earn["withdraw_via"] == "tiktok_owner_account"

    dash = svc.dashboard()
    assert dash["path_a_independent"] is True
    assert dash["reality"]["video_generation"] is False
    assert dash["reality"]["tiktok_connector"] is False
    assert dash["reality"]["earn_money_inside_virtus"] is False
    assert any(c["id"] == "scenarios" for c in dash["capabilities"]["available"])
    assert any(c["id"] == "capcut" for c in dash["capabilities"]["unavailable"])
    assert dash["worker_audit"]["ok"] is True
    deactivate_tiktok()


def test_path_a_order_does_not_touch_video_factory(tmp_path: Path, monkeypatch):
    _patch_features(tmp_path, monkeypatch, enabled=True)
    mem = tmp_path / "mem"
    vf = VideoFactoryService(mem)
    assert vf.list_drafts() == []
    assert vf.list_queue() == []

    sales = SalesOrderService(mem, _Factory())
    created = sales.create_order(
        {
            "business_name": "Path A Shop",
            "description": "Landing only",
            "email": "a@example.de",
            "package_id": "basic",
        }
    )
    assert created["order_id"]
    assert vf.list_drafts() == []
    assert vf.list_queue() == []
    assert vf.list_library() == []
    drafts_file = mem / "video_factory" / "drafts.jsonl"
    assert not drafts_file.is_file() or drafts_file.read_text(encoding="utf-8").strip() == ""


def test_feature_flag_audit_off_blocks_workers(tmp_path: Path, monkeypatch):
    _patch_features(tmp_path, monkeypatch, enabled=False)
    clear_video_workers_for_tests()
    clean = audit_video_factory_background()
    assert clean["ok"] is True
    assert clean["tiktok_enabled"] is False
    assert clean["background_workers_started"] == []
    assert clean["publish_loops_started"] is False

    register_video_worker_for_tests("fake_tiktok_publisher")
    leaked = audit_video_factory_background()
    assert leaked["ok"] is False
    assert "fake_tiktok_publisher" in leaked["background_workers_started"]
    clear_video_workers_for_tests()
    assert audit_video_factory_background()["ok"] is True


def test_invalid_draft_source_rejected(tmp_path: Path, monkeypatch):
    _patch_features(tmp_path, monkeypatch, enabled=True)
    svc = VideoFactoryService(tmp_path / "mem")
    try:
        svc.create_draft_from_pattern(
            niche="Kfz",
            city="Köln",
            pattern_issues=["Kein HTTPS"],
            source="spider",
        )
        assert False, "expected invalid_source"
    except ValueError as exc:
        assert str(exc) == "invalid_source"
