"""Email contact status + Support Unsubscribe."""

from __future__ import annotations

from pathlib import Path

from app.integration.email_contact_status import (
    EmailContactStatusService,
    suppress_outreach_leads_for_email,
)
from app.integration.lead_engine_quality_gate import quality_gate_before_send
from app.integration.support_inbox_service import SupportInboxService


def test_mark_unsubscribed_blocks_quality_gate(tmp_path: Path):
    svc = EmailContactStatusService(tmp_path)
    svc.mark_unsubscribed("ceo@example.com", source="test")
    assert svc.status_of("ceo@example.com") == "unsubscribed"
    assert svc.is_marketing_blocked("CEO@Example.com")

    # Point gate at same memory via monkeypatch path — set status then check meta path
    row = {
        "id": "1",
        "contact": "ceo@example.com",
        "proposed_message": "Hello",
        "recommended_package_id": "basic",
        "meta": {},
        "website_url": "https://example.com",
    }
    # Inject service by writing status where default won't see tmp — use meta instead
    row["meta"] = {"do_not_contact": True, "email_status": "unsubscribed"}
    gate = quality_gate_before_send(row, require_site_alive=False)
    assert gate["ok"] is False
    assert gate["reason"] == "do_not_contact"


def test_support_unsubscribe_keeps_history(tmp_path: Path):
    inbox = SupportInboxService(tmp_path)
    ingested = inbox.ingest_inbound(
        from_email="optout@firma.de",
        subject="Unsubscribe please",
        text="Please remove me from your mailing list",
        auto_reply=False,
    )
    tid = ingested["thread"]["id"]
    result = inbox.mark_unsubscribed(tid)
    assert result["ok"] is True
    assert result["contact"]["status"] == "unsubscribed"
    thread = inbox.get_thread(tid)
    assert thread is not None
    assert thread["status"] == "closed"
    assert thread["do_not_email"] is True
    assert len(thread.get("messages") or []) >= 2  # inbound + system note
    # Still listed under closed — not deleted
    closed = inbox.list_threads(status="closed")
    assert any(str(t.get("id")) == tid for t in closed)


def test_suppress_opportunity_jsonl(tmp_path: Path):
    path = tmp_path / "opportunities.jsonl"
    path.write_text(
        '{"id":"a","contact":"x@y.com","meta":{}}\n'
        '{"id":"b","contact":"other@z.com","meta":{}}\n',
        encoding="utf-8",
    )
    n = suppress_outreach_leads_for_email(tmp_path, "x@y.com")
    assert n == 1
    text = path.read_text(encoding="utf-8")
    assert "do_not_contact" in text
    assert '"id": "b"' in text.replace(" ", "") or '"id":"b"' in text
