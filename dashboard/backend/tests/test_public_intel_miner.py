from pathlib import Path

import pytest

from app.integration.public_intel_miner import PublicIntelMiner


@pytest.fixture()
def miner(tmp_path: Path):
    return PublicIntelMiner(tmp_path)


def test_mine_stale_copyright(miner: PublicIntelMiner):
    opp = {
        "website_url": "https://shop.example",
        "site_analysis": {
            "issues": [],
            "notes": "Footer: Copyright © 2018 — all rights reserved",
        },
    }
    hits = miner.mine_patterns_from_scan(opp)
    assert any(h.pattern_id == "copyright_stale" for h in hits)
    assert hits[0].lane == "seo_revival"


def test_mine_no_https_outreach_lane(miner: PublicIntelMiner):
    opp = {
        "website_url": "http://insecure.example",
        "site_analysis": {
            "issues": ["Kein HTTPS — unsicher für Besucher"],
        },
    }
    hits = miner.mine_patterns_from_scan(opp)
    https = [h for h in hits if h.pattern_id == "no_https_issue"]
    assert len(https) == 1
    assert https[0].lane == "outreach_lead"
    assert https[0].valuation_eur == 150.0


def test_rejects_private_key_context(miner: PublicIntelMiner):
    opp = {
        "website_url": "https://bad.example",
        "site_analysis": {
            "issues": ["leaked private key 0xAbCdEf0123456789AbCdEf0123456789AbCdEf01"],
        },
    }
    hits = miner.mine_patterns_from_scan(opp)
    assert hits == []


def test_process_pattern_hits_service_first_outreach(monetization_engine_fixture):
    engine, opp = monetization_engine_fixture
    row = opp.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "Weak Dental",
            "website_url": "http://dental.example",
            "fit_reason": "Lokaler Zahnarzt",
            "potential_value_eur": 120,
            "site_analysis": {
                "issues": ["Kein HTTPS — unsicher", "wenig Inhalt auf Startseite"],
                "title": "Zahnarzt",
            },
            "meta": {"niche": "local_service"},
        }
    )
    updated = engine.process_pattern_hits(row["id"])
    meta = updated.get("meta") or {}
    assert meta.get("pattern_hits_count", 0) >= 1
    assert meta.get("execution_status") in (
        "outreach_pending_approval",
        "auto_executed",
        "pending_ceo_approval",
    )
    assert meta.get("monetization_priority") == "outreach"
    assert meta.get("hunter_scenarios")
    assert meta.get("smart_gate")
    assert "pending_transactions" not in meta or not meta["pending_transactions"]


@pytest.fixture()
def monetization_engine_fixture(tmp_path: Path):
    from app.integration.asset_scanner_service import AssetScannerService
    from app.integration.finance_service import FinanceService
    from app.integration.monetization_engine_service import MonetizationEngineService
    from app.integration.opportunity_service import OpportunityService
    from app.integration.payment_checkout_service import PaymentCheckoutService

    opp = OpportunityService(tmp_path)
    fin = FinanceService(tmp_path)
    checkout = PaymentCheckoutService(tmp_path)
    scanner = AssetScannerService(opp)
    engine = MonetizationEngineService(opp, fin, checkout, scanner, tmp_path)
    return engine, opp
