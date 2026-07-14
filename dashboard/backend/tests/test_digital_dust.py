from pathlib import Path

import pytest

from app.integration.digital_dust_service import DigitalDustService
from app.integration.public_intel_miner import PublicIntelMiner, PatternHit


@pytest.fixture()
def dust(tmp_path: Path):
    return DigitalDustService(tmp_path)


def test_rejects_private_key_context(dust: DigitalDustService):
    assert dust.is_safe_public_reference("leaked private key 0xabc") is False
    assert dust.extract_contract_addresses("mnemonic phrase twelve words") == []


def test_extract_public_contract_with_claim(dust: DigitalDustService):
    text = (
        "Pool paused. Public withdraw() available. "
        "Contract 0xAbCdEf0123456789AbCdEf0123456789AbCdEf01"
    )
    addrs = dust.extract_contract_addresses(text)
    claims = dust.detect_claim_signals(text)
    assert len(addrs) == 1
    assert claims


def test_build_recoverable_asset(dust: DigitalDustService):
    row = {
        "id": "opp-test1234",
        "website_url": "https://defi.example",
        "fit_reason": "orphan pool with withdraw()",
        "site_analysis": {
            "notes": "0x1111111111111111111111111111111111111111",
        },
    }
    hits = [
        PatternHit(
            pattern_id="defi_orphan_pool",
            pattern_label="Orphan pool",
            matched_value="orphan pool",
            source_url="https://defi.example",
            context_snippet="orphan pool",
            confidence=0.8,
            valuation_eur=40.0,
            lane="digital_dust",
        ),
        PatternHit(
            pattern_id="public_claim_function",
            pattern_label="claim",
            matched_value="withdraw()",
            source_url="https://defi.example",
            context_snippet="withdraw()",
            confidence=0.8,
            valuation_eur=35.0,
            lane="digital_dust",
        ),
    ]
    assets = dust.build_recoverable_from_hits(row, hits)
    assert len(assets) >= 1
    assert assets[0].legal_status == "potential_recoverable_public_only"
    assert "CEO" in assets[0].ceo_action


def test_append_harvest_ledger(dust: DigitalDustService, tmp_path: Path):
    from app.integration.opportunity_service import OpportunityService

    opp = OpportunityService(tmp_path)
    row = opp.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "Dust Co",
            "website_url": "https://dust.example",
            "fit_reason": "claim() on 0x2222222222222222222222222222222222222222",
        }
    )
    hits = [
        PatternHit(
            pattern_id="public_claim_function",
            pattern_label="claim",
            matched_value="claim()",
            source_url="https://dust.example",
            context_snippet="claim()",
            confidence=0.8,
            valuation_eur=35.0,
            lane="digital_dust",
        )
    ]
    updated = dust.process_opportunity(row, hits, opportunity_update=opp.update)
    meta = updated.get("meta") or {}
    assert meta.get("recoverable_assets_count", 0) >= 1
    ledger = tmp_path / "harvest_ledger.jsonl"
    assert ledger.is_file()
    assert "potential_recoverable_asset" in ledger.read_text(encoding="utf-8")


def test_miner_digital_dust_lane(tmp_path: Path):
    miner = PublicIntelMiner(tmp_path)
    opp = {
        "website_url": "https://pool.example",
        "fit_reason": "orphan pool — call withdraw() on 0x3333333333333333333333333333333333333333",
        "site_analysis": {},
    }
    hits = miner.mine_patterns_from_scan(opp)
    lanes = {h.lane for h in hits}
    assert "digital_dust" in lanes


def test_miner_blocks_private_key_near_contract(tmp_path: Path):
    miner = PublicIntelMiner(tmp_path)
    opp = {
        "website_url": "https://bad.example",
        "fit_reason": "private key 0xAbCdEf0123456789AbCdEf0123456789AbCdEf01",
        "site_analysis": {},
    }
    hits = miner.mine_patterns_from_scan(opp)
    assert hits == []
