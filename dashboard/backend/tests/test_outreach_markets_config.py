"""Config-driven outreach markets (outreach_markets.json)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.outreach_market_config import (
    enabled_markets_sum_caps,
    get_market,
    list_markets,
    market_daily_cap,
    market_legal_profile,
    market_send_pool,
    market_template_lang,
    market_website_profile,
    quality_first,
    reload_outreach_markets,
    shared_global_mode,
)
from app.integration.outreach_send_quota import OutreachSendQuota


@pytest.fixture(autouse=True)
def _pacing_off(monkeypatch: pytest.MonkeyPatch):
    reload_outreach_markets()
    monkeypatch.setenv("GENESIS_OUTREACH_MIN_INTERVAL_SEC", "0")
    monkeypatch.delenv("GENESIS_OUTREACH_GLOBAL_DAILY_CAP", raising=False)
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "100")


def test_start_quotas_per_country():
    enabled = list_markets(enabled_only=True)
    codes = {m["code"] for m in enabled}
    expected = {
        "US", "DE", "GB", "FR", "IT", "ES", "CA", "AU", "NL", "PL",
        "CH", "AT", "BE", "PT", "CZ", "RO", "SK", "UA", "RU",
    }
    assert codes == expected
    assert get_market("NZ")["enabled"] is False
    assert shared_global_mode() is False
    assert quality_first() is True
    assert market_daily_cap("US") == 100
    assert market_daily_cap("DE") == 50
    assert market_daily_cap("GB") == 50
    assert market_daily_cap("FR") == 40
    assert market_daily_cap("IT") == 35
    assert market_daily_cap("ES") == 30
    assert market_daily_cap("CA") == 25
    assert market_daily_cap("AU") == 20
    assert market_daily_cap("NL") == 20
    assert market_daily_cap("PL") == 20
    assert market_daily_cap("CH") == 15
    assert market_daily_cap("UA") == 10
    assert market_daily_cap("RU") == 10
    assert enabled_markets_sum_caps() == 485
    assert market_template_lang("UA") == "uk"
    assert market_send_pool("RU") == "cis"
    assert market_legal_profile("US") == "us_can_spam"
    site = market_website_profile("DE")
    assert site["currency"] == "EUR"
    assert "impressum" in site["legal_pages"]


def test_per_market_cap_blocks_and_single_mailbox_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("GENESIS_OUTREACH_FROM_DOMAINS", "de:A <a@one.de>")
    monkeypatch.setenv("GENESIS_OUTREACH_GLOBAL_DAILY_CAP", "485")
    q = OutreachSendQuota(tmp_path)
    # AT start quota = 10
    for _ in range(10):
        addr, meta = q.pick_from_address(market="AT")
        assert addr and meta["ok"], meta
        q.record_send(addr, market="AT")
    blocked, why = q.can_send("A <a@one.de>", market="AT")
    assert blocked is False
    assert "AT" in why
    # FR still open on the same single mailbox
    addr_fr, meta_fr = q.pick_from_address(market="FR")
    assert addr_fr and meta_fr["ok"]
    h = q.health()
    assert h["allocation_mode"] == "per_market"
    assert h["quality_first"] is True
    assert h["global_daily_cap"] == 485
    by = {r["code"]: r for r in h["markets"]}
    assert by["AT"]["used_today"] == 10 and by["AT"]["at_cap"]
    assert by["FR"]["enabled"] and by["FR"]["used_today"] == 0


def test_global_cap_still_hard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_GLOBAL_DAILY_CAP", "5")
    monkeypatch.setenv("GENESIS_OUTREACH_FROM_DOMAINS", "de:A <a@one.de>")
    q = OutreachSendQuota(tmp_path)
    for _ in range(5):
        addr, meta = q.pick_from_address(market="US")
        assert addr and meta["ok"]
        q.record_send(addr, market="US")
    blocked, why = q.can_send("A <a@one.de>", market="CA")
    assert blocked is False
    assert "global_cap" in why
