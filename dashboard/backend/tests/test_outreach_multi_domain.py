"""Multi-domain outreach From rotation (GENESIS_OUTREACH_FROM_DOMAINS)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.outreach_send_quota import OutreachSendQuota, outreach_daily_cap


def test_multi_domain_least_used(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "10")
    monkeypatch.setenv(
        "GENESIS_OUTREACH_FROM_DOMAINS",
        "A <a@one.de>, B <b@two.de>",
    )
    q = OutreachSendQuota(tmp_path)
    first, _ = q.pick_from_address()
    assert first is not None
    q.record_send(first)
    second, meta = q.pick_from_address()
    assert second is not None
    assert second != first
    assert meta["domain"] in ("one.de", "two.de")
    health = q.health()
    assert health["daily_cap"] == 10
    assert len(health["domains"]) == 2
    assert sum(1 for d in health["domains"] if d["used_today"] >= 1) >= 1
    assert health["pool_cap_total"] == 20
    assert health["sent_today_total"] >= 1
    assert "remaining_today_total" in health


def test_daily_cap_allows_planning_100(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "100")
    assert outreach_daily_cap() == 100
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "999")
    assert outreach_daily_cap() == 100


def test_quota_health_ceo_totals(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "100")
    monkeypatch.setenv(
        "GENESIS_OUTREACH_FROM_DOMAINS",
        "A <a@one.de>, B <b@two.de>, C <c@three.de>",
    )
    q = OutreachSendQuota(tmp_path)
    for _ in range(3):
        addr, _ = q.pick_from_address()
        assert addr
        q.record_send(addr)
    h = q.health()
    assert h["daily_cap"] == 100
    assert h["domain_count"] == 3
    assert h["pool_cap_total"] == 300
    assert h["sent_today_total"] == 3
    assert h["remaining_today_total"] == 297
    assert h["primary_used_today"] + h["primary_remaining"] == 100
