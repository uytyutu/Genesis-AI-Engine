"""Config-driven outreach markets (outreach_markets.json)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.outreach_market_config import (
    get_market,
    list_markets,
    market_daily_cap,
    market_legal_profile,
    market_send_pool,
    market_template_lang,
)
from app.integration.outreach_send_quota import OutreachSendQuota


@pytest.fixture(autouse=True)
def _pacing_off(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_MIN_INTERVAL_SEC", "0")
    monkeypatch.setenv("GENESIS_OUTREACH_GLOBAL_DAILY_CAP", "500")
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "100")


def test_phase1_markets_enabled():
    enabled = list_markets(enabled_only=True)
    codes = {m["code"] for m in enabled}
    assert codes == {"DE", "US", "UA", "RU"}
    assert market_daily_cap("DE") == 20
    assert market_daily_cap("US") == 40
    assert market_template_lang("UA") == "uk"
    assert market_send_pool("RU") == "cis"
    assert market_legal_profile("US") == "us_can_spam"
    assert get_market("UK") and get_market("UK")["code"] == "GB"
    assert get_market("UK")["enabled"] is False


def test_market_cap_independent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(
        "GENESIS_OUTREACH_FROM_DOMAINS",
        "de:A <a@one.de>, us:B <b@two.com>, cis:C <c@cis.example>",
    )
    q = OutreachSendQuota(tmp_path)
    # Exhaust DE (20) should not block US
    for _ in range(20):
        addr, meta = q.pick_from_address(market="DE")
        assert addr and meta["ok"]
        q.record_send(addr, market="DE")
    blocked, why = q.can_send("A <a@one.de>", market="DE")
    assert blocked is False
    assert "DE" in why
    addr_us, meta_us = q.pick_from_address(market="US")
    assert addr_us and meta_us["ok"]
    h = q.health()
    by = {r["code"]: r for r in h["markets"]}
    assert by["DE"]["used_today"] == 20 and by["DE"]["at_cap"]
    assert by["US"]["used_today"] == 0 and by["US"]["enabled"]
    assert by["GB"]["enabled"] is False
