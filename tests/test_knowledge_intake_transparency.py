"""Knowledge Intake — Transparency slice tests."""

from io import BytesIO

from fastapi import UploadFile

from app.integration.feature_registry import FeatureRegistry
from app.integration.knowledge_intake_transparency import (
    build_brain_attachment_note,
    build_user_attachment_ack,
    transparency_enabled,
    upload_policy_snapshot,
)
from app.integration.public_chat_attachments import PublicChatAttachmentService


def test_transparency_feature_enabled_by_default():
    assert FeatureRegistry().is_enabled("attachment_transparency") is True
    assert transparency_enabled() is True


def test_brain_note_does_not_claim_content_read():
    files = [{"filename": "contract.pdf", "content_type": "application/pdf"}]
    note = build_brain_attachment_note(files, locale="ru")
    assert "contract.pdf" in note
    assert "НЕ доступно" in note or "не прочитано" in note.lower() or "содержимое" in note.lower()


def test_user_ack_stored_only_honest():
    files = [{"filename": "brief.pdf", "content_type": "application/pdf"}]
    ack = build_user_attachment_ack(files, locale="ru")
    assert "brief.pdf" in ack
    assert "не анализируется" in ack.lower() or "не анализируется" in ack


def test_upload_policy_snapshot_free_tier(tmp_path):
    snap = upload_policy_snapshot(tmp_path, visitor_id="v1")
    assert snap["transparency_enabled"] is True
    assert snap["tier"] == "free"
    assert "pdf" in snap["analyze"]["available_kinds"]
    assert snap["analyze"]["stored_only"] is False


def test_upload_enforces_free_size_limit(tmp_path):
    svc = PublicChatAttachmentService(tmp_path)
    big = b"x" * (5 * 1024 * 1024)
    upload = UploadFile(filename="big.pdf", file=BytesIO(big), headers={"content-type": "application/pdf"})
    try:
        svc.save(upload, visitor_id="u1")
        assert False, "expected size rejection"
    except ValueError as exc:
        assert "large" in str(exc).lower() or "MB" in str(exc)


def test_upload_records_daily_quota(tmp_path):
    svc = PublicChatAttachmentService(tmp_path)
    small = b"%PDF-1.4 test"
    upload = UploadFile(filename="a.pdf", file=BytesIO(small), headers={"content-type": "application/pdf"})
    svc.save(upload, visitor_id="u2")
    assert svc.uploads_today("u2") == 1
