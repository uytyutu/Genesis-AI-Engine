"""Attachment policy — tier limits and feature-flag gates."""

from app.integration.attachment_policy import (
    AttachmentPolicy,
    resolve_attachment_tier,
)
from app.integration.feature_registry import FeatureRegistry


def test_mission1_all_visitors_are_free_tier():
    assert resolve_attachment_tier(visitor_id="any-visitor") == "free"


def test_free_tier_allows_small_pdf_upload():
    policy = AttachmentPolicy()
    result = policy.check_upload(
        tier="free",
        content_type="application/pdf",
        size_bytes=1024,
        files_in_message=1,
        uploads_today=0,
    )
    assert result.allowed is True


def test_free_tier_blocks_oversized_file():
    policy = AttachmentPolicy()
    result = policy.check_upload(
        tier="free",
        content_type="application/pdf",
        size_bytes=5 * 1024 * 1024,
        files_in_message=1,
        uploads_today=0,
    )
    assert result.allowed is False


def test_free_tier_blocks_daily_upload_cap():
    policy = AttachmentPolicy()
    result = policy.check_upload(
        tier="free",
        content_type="application/pdf",
        size_bytes=1024,
        files_in_message=1,
        uploads_today=10,
    )
    assert result.allowed is False


def test_parse_allowed_on_studio_when_pdf_feature_on():
    policy = AttachmentPolicy()
    result = policy.check_parse(tier="studio", content_type="application/pdf")
    assert result.allowed is True


def test_parse_allowed_when_feature_on(tmp_path, monkeypatch):
    cfg = tmp_path / "platform_features.json"
    cfg.write_text('{"features": {"attachment_pdf": true}}', encoding="utf-8")
    policy = AttachmentPolicy(memory_dir=tmp_path)
    result = policy.check_parse(tier="studio", content_type="application/pdf")
    assert result.allowed is True
    assert result.parse_kind == "pdf"


def test_free_tier_parse_pdf_allowed_when_feature_on(tmp_path):
    cfg = tmp_path / "platform_features.json"
    cfg.write_text('{"features": {"attachment_pdf": true}}', encoding="utf-8")
    policy = AttachmentPolicy(memory_dir=tmp_path)
    result = policy.check_parse(tier="free", content_type="application/pdf")
    assert result.allowed is True
    limits = policy.limits_for("free")
    assert limits.max_parsed_documents_per_day == 1
    assert limits.max_parsed_pages_per_day == 5


def test_free_tier_parse_pdf_blocked_without_feature(tmp_path, monkeypatch):
    cfg = tmp_path / "platform_features.json"
    cfg.write_text('{"features": {"attachment_pdf": false}}', encoding="utf-8")
    policy = AttachmentPolicy(memory_dir=tmp_path)
    result = policy.check_parse(tier="free", content_type="application/pdf")
    assert result.allowed is False


def test_free_tier_parse_docx_blocked():
    policy = AttachmentPolicy()
    result_docx = policy.check_parse(
        tier="free",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert result_docx.allowed is False


def test_attachment_features_parse_default_disabled():
    reg = FeatureRegistry()
    assert reg.is_enabled("attachment_pdf") is True
    for fid in (
        "attachment_docx",
        "attachment_vision",
    ):
        assert reg.is_enabled(fid) is False
    assert reg.is_enabled("attachment_transparency") is True
