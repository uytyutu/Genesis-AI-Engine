"""Support Unsubscribe → email contact status + outreach block."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.integration.email_contact_status import EmailContactStatusService
from app.integration.lead_engine_quality_gate import quality_gate_before_send
from app.integration.support_inbox_service import SupportInboxService


def test_unsubscribe_by_email_without_local_thread(tmp_path: Path):
    """Railway thread missing locally — email fallback still blocks outreach."""
    svc = SupportInboxService(memory_dir=tmp_path)
    out = svc.unsubscribe_email("info@craigrace.com", thread_id="missing-id")
    assert out["ok"] is True
    assert out["email"] == "info@craigrace.com"
    assert EmailContactStatusService(tmp_path).is_marketing_blocked("info@craigrace.com")


def test_auto_unsubscribe_on_inbound_opt_out(tmp_path: Path):
    from app.integration.support_inbox_service import looks_like_unsubscribe_request

    assert looks_like_unsubscribe_request("Unsubscribe", "Please remove me from your list")
    assert looks_like_unsubscribe_request("Abmelden", "keine weiteren E-Mails")
    assert not looks_like_unsubscribe_request("Question", "We like your website")

    svc = SupportInboxService(memory_dir=tmp_path)
    ingested = svc.ingest_inbound(
        from_email="team@craigrace.com",
        subject="Re: your offer",
        text="Sincerely, the Craig Race Architecture Team. Please unsubscribe us.",
        auto_reply=False,
    )
    assert ingested.get("auto_unsubscribed")
    thread = ingested["thread"]
    assert thread["status"] == "closed"
    assert thread["do_not_email"] is True
    assert EmailContactStatusService(tmp_path).is_marketing_blocked("team@craigrace.com")


def test_mark_unsubscribed_keeps_thread_closes_and_blocks_send(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GENESIS_MEMORY_DIR", str(tmp_path))
    svc = SupportInboxService(memory_dir=tmp_path)
    ingested = svc.ingest_inbound(
        from_email="client@example.com",
        subject="Unsubscribe please",
        text="Please remove me from your mailing list",
        auto_reply=False,
    )
    tid = ingested["thread"]["id"]

    out = svc.mark_unsubscribed(tid)
    assert out["ok"] is True
    assert out["contact"]["status"] == "unsubscribed"
    assert out["thread"]["status"] == "closed"
    assert out["thread"]["do_not_email"] is True
    assert len(out["thread"]["messages"]) >= 2

    contacts = EmailContactStatusService(tmp_path)
    assert contacts.is_marketing_blocked("client@example.com")

    gate = quality_gate_before_send(
        {
            "contact": "client@example.com",
            "proposed_message": "Hello",
            "recommended_package_id": "basic",
            "meta": {},
            "market": "DE",
        },
        require_site_alive=False,
        now_utc=datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc),
    )
    assert gate["ok"] is False
    assert gate["reason"] == "unsubscribed"


def test_email_contact_status_service(tmp_path: Path):
    svc = EmailContactStatusService(tmp_path)
    assert svc.status_of("a@b.com") == "active"
    svc.mark_unsubscribed("a@b.com", source="support")
    assert svc.status_of("A@B.com") == "unsubscribed"
    assert svc.is_marketing_blocked("a@b.com")
    svc.set_status("a@b.com", "active", source="manual")
    assert not svc.is_marketing_blocked("a@b.com")
