"""S1.3 — Upload security + XSS checks."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.integration.order_materials_service import OrderMaterialsService
from app.integration.public_chat_attachments import PublicChatAttachmentService
from app.integration.receipt_email_service import _html_email
from app.portal.s1_3_xss_upload import (
    assert_safe_upload_filename,
    contains_reflected_xss_payload,
    html_escape_user_text,
)


def test_reject_html_and_traversal_filenames():
    with pytest.raises(ValueError):
        assert_safe_upload_filename("../etc/passwd")
    with pytest.raises(ValueError):
        assert_safe_upload_filename("payload.html")
    with pytest.raises(ValueError):
        assert_safe_upload_filename("x.js")
    assert_safe_upload_filename("logo.png")


def test_public_chat_upload_rejects_html(tmp_path: Path):
    svc = PublicChatAttachmentService(tmp_path)
    upload = UploadFile(
        filename="xss.html",
        file=BytesIO(b"<script>alert(1)</script>"),
        headers={"content-type": "text/html"},
    )
    with pytest.raises(ValueError):
        svc.save(upload, visitor_id="v1")


def test_order_materials_reject_html_and_path_traversal(tmp_path: Path):
    svc = OrderMaterialsService(tmp_path)
    bad = UploadFile(
        filename="../../payload.html",
        file=BytesIO(b"<script>x</script>"),
        headers={"content-type": "text/html"},
    )
    with pytest.raises(ValueError):
        svc.save(bad, session_id="s1")


def test_html_email_escapes_xss_payload():
    payload = '<script>alert("x")</script>'
    body = _html_email(
        title=payload,
        intro=payload,
        rows=[("Name", payload)],
    )
    assert "<script>" not in body
    assert "&lt;script&gt;" in body
    assert not contains_reflected_xss_payload(body)
    assert html_escape_user_text(payload) == "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;"
