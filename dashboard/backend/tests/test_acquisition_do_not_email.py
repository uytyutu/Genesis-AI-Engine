"""Acquisition do-not-email bypasses Support→Railway proxy."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_acquisition_do_not_email_blocks(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("GENESIS_MEMORY_DIR", str(tmp_path))
    # Ensure support remote is off
    monkeypatch.delenv("SUPPORT_INBOX_REMOTE_URL", raising=False)
    monkeypatch.delenv("SUPPORT_BRIDGE_SECRET", raising=False)

    from app.integration.email_contact_status import EmailContactStatusService
    from app.integration.support_inbox_service import SupportInboxService

    svc = SupportInboxService(memory_dir=tmp_path)
    out = svc.unsubscribe_email("info@craigrace.com")
    assert out["ok"] is True
    assert EmailContactStatusService(tmp_path).is_marketing_blocked("info@craigrace.com")
