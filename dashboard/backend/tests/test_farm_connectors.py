"""Farm Connector Manager — multi-platform pool (no live network)."""

from __future__ import annotations

from swarm.farm_connectors.base import ConnectorStatus, Tier
from swarm.farm_connectors.manager import ConnectorManager, parse_opportunity_id
from swarm.farm_connectors.normalize import dedupe_opportunities, opportunity_key
from swarm.farm_connectors.opire_connector import OpireConnector
from swarm.farm_connectors.registry import CONNECTOR_CATALOG
from swarm.farm_connectors.stubs import StubConnector


def test_catalog_has_tiers_and_opire_live():
    ids = {c["id"] for c in CONNECTOR_CATALOG}
    assert "opire" in ids
    assert "polar" in ids
    assert "hackerone" in ids
    assert "gitcoin" in ids
    opire = next(c for c in CONNECTOR_CATALOG if c["id"] == "opire")
    assert opire["tier"] == "A"
    assert opire["status"] == "live"
    h1 = next(c for c in CONNECTOR_CATALOG if c["id"] == "hackerone")
    assert h1["tier"] == "B"
    assert h1["status"] == "disabled"


def test_dedupe_keeps_best_confidence():
    a = {
        "id": "opire:1",
        "platform": "opire",
        "title": "Fix X",
        "url": "https://github.com/acme/demo/issues/1",
        "repository": "acme/demo",
        "issue_id": "1",
        "reward_usd": 50,
        "overall_confidence_pct": 70,
    }
    b = {
        "id": "polar:9",
        "platform": "polar",
        "title": "Fix X",
        "url": "https://github.com/acme/demo/issues/1",
        "repository": "acme/demo",
        "issue_id": "1",
        "reward_usd": 80,
        "overall_confidence_pct": 88,
    }
    out = dedupe_opportunities([a, b])
    assert len(out) == 1
    assert out[0]["platform"] == "polar"
    assert "opire" in (out[0].get("also_on") or [])
    assert opportunity_key(a) == opportunity_key(b)


def test_manager_default_skips_tier_b_and_planned():
    mgr = ConnectorManager()
    cat = {c["id"]: c for c in mgr.catalog()}
    assert cat["opire"]["runtime_status"] == "live"
    assert cat["polar"]["runtime_status"] == "planned"
    assert cat["hackerone"]["runtime_status"] == "disabled"

    # Planned/stub connectors contribute 0 without calling external APIs
    scan = mgr.scan(threshold=0, live_only=True)
    polar_row = next(c for c in scan["connectors"] if c["id"] == "polar")
    assert polar_row.get("skipped") == "not_live"
    assert "B" not in scan["tiers_scanned"]


def test_manager_opire_only_with_stub_fetch():
    raw = {
        "id": "raw-1",
        "title": "Fix pagination race in API",
        "url": "https://github.com/acme/demo/issues/42",
        "claimerUsers": [],
        "tryingUsers": [],
        "programmingLanguages": ["Python"],
        "pendingPrice": {"value": 8000, "unit": "USD_CENT"},
        "project": {
            "isPublic": True,
            "isBotInstalled": True,
        },
    }
    mgr = ConnectorManager(connectors=[OpireConnector(fetch_fn=lambda: [raw])])
    out = mgr.scan(threshold=70)
    assert out["ok"] is True
    assert out["scanned"] >= 1
    assert any(c["id"] == "opire:raw-1" for c in out["candidates"])
    assert out["candidates"][0]["platform"] == "opire"


def test_parse_opportunity_id():
    assert parse_opportunity_id("opire:abc") == ("opire", "abc")
    assert parse_opportunity_id("abc") == (None, "abc")


def test_stub_never_fetches():
    stub = StubConnector(
        id="polar",
        display_name="Polar",
        tier=Tier.A,
        status=ConnectorStatus.PLANNED,
        official_docs_url="https://polar.sh",
    )
    assert stub.fetch_raw() == []
    assert stub.normalize({"x": 1}) is None
