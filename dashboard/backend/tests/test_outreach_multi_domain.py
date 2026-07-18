"""Multi-domain / multi-region outreach From rotation."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.outreach_send_quota import (
    OutreachSendQuota,
    outreach_daily_cap,
    parse_from_entry,
)


@pytest.fixture(autouse=True)
def _phase1_pacing_off(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_MIN_INTERVAL_SEC", "0")
    monkeypatch.setenv("GENESIS_OUTREACH_GLOBAL_DAILY_CAP", "500")


def test_parse_region_tags():
    assert parse_from_entry("de:A <a@one.de>") == ("de", "A <a@one.de>")
    assert parse_from_entry("cis:B <b@two.com>") == ("cis", "B <b@two.com>")
    assert parse_from_entry("us:C <c@three.com>") == ("us", "C <c@three.com>")
    assert parse_from_entry("A <a@one.de>") == ("de", "A <a@one.de>")


def test_untagged_domains_share_de_region_cap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Two DE From addresses share one regional pool — not 2× cap."""
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "2")
    monkeypatch.setenv(
        "GENESIS_OUTREACH_FROM_DOMAINS",
        "A <a@one.de>, B <b@two.de>",
    )
    q = OutreachSendQuota(tmp_path)
    for _ in range(2):
        addr, meta = q.pick_from_address()
        assert addr and meta["ok"]
        assert meta["region"] == "de"
        q.record_send(addr)
    none_addr, none_meta = q.pick_from_address()
    assert none_addr is None
    assert none_meta["reason"] in ("all_regions_at_cap", "region_at_cap:de")
    h = q.health()
    assert h["region_count"] == 1
    assert h["pool_cap_total"] == 120  # sum enabled markets (DE+US+UA+RU), min(global)
    assert h["sent_today_total"] == 2


def test_multi_region_independent_caps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "2")
    monkeypatch.setenv(
        "GENESIS_OUTREACH_FROM_DOMAINS",
        "de:A <a@one.de>, cis:B <b@cis.example>, us:C <c@us.example>",
    )
    q = OutreachSendQuota(tmp_path)
    # Exhaust DE
    for _ in range(2):
        addr, meta = q.pick_from_address(region="de")
        assert addr and meta["region"] == "de"
        q.record_send(addr, region="de")
    blocked, why = q.can_send("A <a@one.de>", region="de")
    assert blocked is False
    assert "de" in why
    # CIS still open
    addr_cis, meta_cis = q.pick_from_address(region="cis")
    assert addr_cis and meta_cis["region"] == "cis"
    q.record_send(addr_cis, region="cis")
    h = q.health()
    assert h["region_count"] == 3
    assert h["pool_cap_total"] == 120  # config markets sum, not regions * env cap
    assert h["sent_today_total"] == 3
    by = {r["region"]: r for r in h["regions"]}
    assert by["de"]["used_today"] == 2 and by["de"]["at_cap"]
    assert by["cis"]["used_today"] == 1 and not by["cis"]["at_cap"]
    assert by["us"]["used_today"] == 0


def test_pick_balances_across_regions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "10")
    monkeypatch.setenv(
        "GENESIS_OUTREACH_FROM_DOMAINS",
        "de:A <a@one.de>, cis:B <b@cis.example>, us:C <c@us.example>",
    )
    q = OutreachSendQuota(tmp_path)
    seen = []
    for _ in range(3):
        addr, meta = q.pick_from_address()
        assert addr
        q.record_send(addr, region=meta["region"])
        seen.append(meta["region"])
    assert set(seen) == {"de", "cis", "us"}


def test_daily_cap_allows_planning_100(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "100")
    assert outreach_daily_cap() == 100
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "999")
    assert outreach_daily_cap() == 100


def test_quota_health_ceo_three_markets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_DAILY_CAP", "100")
    monkeypatch.setenv(
        "GENESIS_OUTREACH_FROM_DOMAINS",
        "de:A <a@one.de>, cis:B <b@cis.example>, us:C <c@us.example>",
    )
    q = OutreachSendQuota(tmp_path)
    for _ in range(3):
        addr, meta = q.pick_from_address()
        assert addr
        q.record_send(addr, region=meta["region"])
    h = q.health()
    assert h["daily_cap"] == 100
    assert h["region_count"] == 3
    assert h["global_daily_cap"] == 500
    assert h["pool_cap_total"] == 120  # min(enabled market caps sum, global)
    assert h["sent_today_total"] == 3
    assert h["remaining_today_total"] == 497
    labels = {r["label_ru"] for r in h["regions"]}
    assert labels == {"Германия", "СНГ", "Америка"}
