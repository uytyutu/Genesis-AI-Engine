"""Multi-domain outreach From rotation (GENESIS_OUTREACH_FROM_DOMAINS)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.outreach_send_quota import OutreachSendQuota


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
