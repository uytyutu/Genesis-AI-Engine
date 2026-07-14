from pathlib import Path

import pytest

from app.integration.public_intel_miner import PublicIntelMiner


@pytest.fixture()
def miner(tmp_path: Path):
    return PublicIntelMiner(tmp_path)


def test_mine_eth_contract(miner: PublicIntelMiner):
    opp = {
        "website_url": "https://shop.example",
        "site_analysis": {
            "issues": [],
            "notes": "Partner wallet 0xAbCdEf0123456789AbCdEf0123456789AbCdEf01 listed",
        },
    }
    hits = miner.mine_patterns_from_scan(opp)
    assert any(h.pattern_id == "eth_contract_public" for h in hits)
    assert hits[0].lane == "data_product"


def test_mine_nft_collection_sets_arbitrage_lane(miner: PublicIntelMiner):
    opp = {
        "website_url": "https://agency.example",
        "fit_reason": "See https://opensea.io/collection/cool-degens for merch",
        "site_analysis": {},
    }
    hits = miner.mine_patterns_from_scan(opp)
    nft = [h for h in hits if h.pattern_id == "nft_collection_opensea"]
    assert len(nft) == 1
    assert nft[0].lane == "arbitrage_alert"
    assert nft[0].valuation_eur == 5.0


def test_rejects_private_key_context(miner: PublicIntelMiner):
    opp = {
        "website_url": "https://bad.example",
        "site_analysis": {
            "issues": ["leaked private key 0xAbCdEf0123456789AbCdEf0123456789AbCdEf01"],
        },
    }
    hits = miner.mine_patterns_from_scan(opp)
    assert hits == []


def test_process_pattern_hits_pending_ceo(monetization_engine_fixture):
    engine, opp = monetization_engine_fixture
    row = opp.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "NFT Shop",
            "website_url": "https://nft.example",
            "fit_reason": "https://opensea.io/collection/test-nft",
            "potential_value_eur": 30,
            "meta": {"niche": "niche_blog"},
        }
    )
    updated = engine.process_pattern_hits(row["id"])
    meta = updated.get("meta") or {}
    assert meta.get("pattern_hits_count", 0) >= 1
    assert meta.get("execution_status") == "pending_ceo_approval"
    assert meta.get("pending_transactions")
    assert meta["pending_transactions"][0]["status"] == "pending_ceo_approval"
    assert meta["pending_transactions"][0]["auto_execute"] is False


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
