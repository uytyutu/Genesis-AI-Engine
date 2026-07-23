"""Sniper daily outreach caps (single-domain and shared counters)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.global_exclusion import GlobalExclusionService, is_excluded, normalize_email
from app.integration.outreach_send_quota import OutreachSendQuota, outreach_daily_cap
from app.integration.opportunity_service import OpportunityService


def test_normalize_email():
    assert normalize_email("CEO <Owner@Example.DE>") == "owner@example.de"


def test_exclusion_blocks_same_email(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    a = opp.create(
        {
            "company_name": "A GmbH",
            "contact": "same@firma.de",
            "website_url": "https://a.example.de",
        }
    )
    opp.update(
        a["id"],
        {"status": "contacted", "outreach_status": "sent"},
    )
    svc = GlobalExclusionService(opp)
    blocked, reason = svc.check(email="same@firma.de", website_url="https://other.de")
    assert blocked is True
    assert reason == "email_already_contacted"

    blocked2, reason2 = svc.check(
        email="new@firma.de",
        website_url="https://a.example.de",
    )
    assert blocked2 is True
    assert reason2 == "host_already_contacted"

    ok, _ = is_excluded(
        email="same@firma.de",
        website_url="https://a.example.de",
        rows=opp._load_rows(),
        exclude_id=a["id"],
    )
    assert ok is False


def test_single_mailbox_skips_regional_daily_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """RC1 Decision #1: one From address → regional daily_cap does not apply.

    Global + pacing + per-market quotas still apply; stacking GENESIS_OUTREACH_DAILY_CAP
    on a Mission-1 single mailbox is intentionally disabled.
    """
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "2")
    monkeypatch.setenv("GENESIS_OUTREACH_MIN_INTERVAL_SEC", "0")
    monkeypatch.setenv("GENESIS_OUTREACH_GLOBAL_DAILY_CAP", "500")
    monkeypatch.setenv("GENESIS_EMAIL_FROM", "Virtus <hello@ram98.de>")
    monkeypatch.delenv("GENESIS_OUTREACH_FROM_DOMAINS", raising=False)
    assert outreach_daily_cap() == 2
    q = OutreachSendQuota(tmp_path)
    addr, meta = q.pick_from_address()
    assert addr and meta["ok"]
    assert q.can_send(addr)[0] is True
    q.record_send(addr)
    q.record_send(addr)
    can, why = q.can_send(addr)
    assert can is True
    assert why == ""
    # Multi-domain still enforces regional daily_cap (see test_outreach_multi_domain).


def test_multi_domain_regional_daily_cap_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """With ≥2 From addresses, regional GENESIS_OUTREACH_DAILY_CAP blocks overage."""
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "2")
    monkeypatch.setenv("GENESIS_OUTREACH_MIN_INTERVAL_SEC", "0")
    monkeypatch.setenv("GENESIS_OUTREACH_GLOBAL_DAILY_CAP", "500")
    monkeypatch.setenv(
        "GENESIS_OUTREACH_FROM_DOMAINS",
        "A <a@one.de>, B <b@two.de>",
    )
    q = OutreachSendQuota(tmp_path)
    for _ in range(2):
        addr, meta = q.pick_from_address()
        assert addr and meta["ok"]
        q.record_send(addr)
    can, why = q.can_send("A <a@one.de>")
    assert can is False
    assert "daily_cap" in why
