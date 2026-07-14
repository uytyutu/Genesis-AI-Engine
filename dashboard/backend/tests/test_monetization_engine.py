from pathlib import Path
from unittest.mock import patch

import pytest

from app.integration.asset_scanner_service import AssetScannerService
from app.integration.finance_service import FinanceService
from app.integration.monetization_engine_service import (
    MonetizationEngineService,
    compute_profitability_score,
    MIN_PROFIT_SCORE,
)
from app.integration.opportunity_service import OpportunityService
from app.integration.payment_checkout_service import PaymentCheckoutService


@pytest.fixture()
def engine(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    fin = FinanceService(tmp_path)
    checkout = PaymentCheckoutService(tmp_path)
    scanner = AssetScannerService(opp)
    return MonetizationEngineService(opp, fin, checkout, scanner, tmp_path)


def test_profitability_score_gate():
    high = compute_profitability_score(
        potential_eur=55,
        traffic_band="medium",
        abandoned=True,
        analysis_score=60,
        issue_count=1,
    )
    low = compute_profitability_score(
        potential_eur=10,
        traffic_band="trace",
        abandoned=False,
        analysis_score=10,
        issue_count=8,
    )
    assert high >= MIN_PROFIT_SCORE
    assert low < MIN_PROFIT_SCORE


def test_scan_and_gate_routes_low_yield_to_junk_archive(engine: MonetizationEngineService):
    fake_weak = {
        "url": "https://weak.example",
        "final_url": "https://weak.example",
        "title": "Weak",
        "issues": ["x"] * 10,
        "strengths": [],
        "issue_count": 10,
        "improvement_score": 5,
    }
    with patch(
        "app.integration.asset_scanner_service.SiteAnalysisService.analyze",
        return_value=fake_weak,
    ):
        result = engine.scan_and_gate("https://weak.example", manual=True)
    assert result["shown_to_owner"] is False
    assert result["archived"] is True
    assert result["lane"] == "junk_archive"
    meta = result["target"].get("meta") or {}
    assert meta.get("processing_lane") == "junk_archive"
    assert float(meta.get("junk_micro_revenue_eur") or 0) >= 0.5


def test_junk_archive_batch(engine: MonetizationEngineService):
    row = engine._opportunity.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "Junk Site",
            "website_url": "https://junk.example",
            "status": "reviewed",
            "meta": {"processing_lane": "junk_archive", "profit_score": 20},
        }
    )
    batch = engine.process_junk_archive_cycle()
    assert batch["processed"] >= 1
    updated = engine._opportunity.get(row["id"])
    assert float(updated.get("revenue_eur") or 0) >= 0.5


def test_network_portfolio_projection(engine: MonetizationEngineService):
    engine._opportunity.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "Net Asset 1",
            "website_url": "https://net1.example",
            "status": "proposed",
            "meta": {"network_managed": True, "projected_monthly_eur": 20, "processing_lane": "high"},
        }
    )
    dash = engine.engine_dashboard()
    assert dash["network"]["managed_assets"] >= 1
    assert dash["network"]["projected_mrr_eur"] >= 20


def test_network_scan_requires_places(engine: MonetizationEngineService):
    result = engine.run_network_scan(niche="local_service", batch_limit=10)
    assert result["ok"] is False
    assert "GOOGLE_PLACES" in result["errors"][0]


def test_withdraw_queues_payout(engine: MonetizationEngineService):
    snap_path = engine._memory / "finance_snapshot.json"  # noqa: SLF001
    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(
        '{"available_for_withdrawal_eur": 100.0, "pending_payouts_eur": 0.0}',
        encoding="utf-8",
    )
    result = engine.request_withdrawal(40.0, "bank")
    assert result["ok"] is True
    assert result["amount_eur"] == 40.0
