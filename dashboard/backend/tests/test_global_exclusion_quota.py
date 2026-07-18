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


def test_daily_cap_blocks_overage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "2")
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
    assert can is False
    assert "daily_cap" in why
    none_addr, none_meta = q.pick_from_address()
    assert none_addr is None
    assert none_meta["reason"] == "all_domains_at_cap"
