from pathlib import Path

import pytest

from app.integration.business_mode_service import BusinessModeService
from app.integration.finance_service import FinanceService
from app.integration.monetization_engine_service import MonetizationEngineService
from app.integration.opportunity_service import OpportunityService


def test_financial_view_sandbox_zero_withdraw(tmp_path: Path):
    mode = BusinessModeService(tmp_path)
    opp = OpportunityService(tmp_path)
    opp.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "Lead Co",
            "website_url": "https://lead.example",
            "potential_value_eur": 200,
            "meta": {"hunter_value_eur": 50},
        }
    )
    fin = FinanceService(tmp_path)
    view = fin.financial_view(
        business_mode=mode,
        opportunities=opp.list_opportunities(),
    )
    assert view["system_mode"] == "sandbox"
    assert view["funds_held_by_genesis_eur"] == 0.0
    assert view["safe_to_withdraw_eur"] == 0.0
    assert view["withdraw_enabled"] is False
    assert view["potential_revenue_eur"] == 250.0
    assert view["money_never_stored"] is True


def test_financial_view_live_safe_to_withdraw(tmp_path: Path):
    mode = BusinessModeService(tmp_path)
    mode.activate_business(confirmed=True, phrase="ACTIVATE BUSINESS")
    snap_path = tmp_path / "finance_snapshot.json"
    snap_path.write_text(
        '{"gross_revenue_eur": 1000.0, "available_for_withdrawal_eur": 900.0, '
        '"pending_payouts_eur": 100.0, "platform_balance_eur": 1000.0}',
        encoding="utf-8",
    )
    tax_path = tmp_path / "engine_tax_config.json"
    tax_path.write_text(
        '{"vat_rate_percent": 19.0, "stripe_fee_percent": 1.4, "stripe_fee_fixed_eur": 0.25}',
        encoding="utf-8",
    )
    fin = FinanceService(tmp_path)
    view = fin.financial_view(business_mode=mode)
    assert view["system_mode"] == "live"
    assert view["gross_synced_eur"] == 1000.0
    assert view["tax_reserve_eur"] > 0
    assert view["safe_to_withdraw_eur"] > 0
    assert view["safe_to_withdraw_status"] == "green"
    assert view["funds_held_by_genesis_eur"] == 0.0


def test_reconcile_updates_sync_timestamp(tmp_path: Path):
    fin = FinanceService(tmp_path)
    result = fin.reconcile(business_mode=BusinessModeService(tmp_path))
    assert result["ok"] is True
    assert result["synced_at"]
    config = fin._load_config()
    assert config.get("last_sync_at") == result["synced_at"]


def test_finance_center_includes_settlements(tmp_path: Path):
    mode = BusinessModeService(tmp_path)
    fin = FinanceService(tmp_path)
    fin.credit_order_payment(
        150.0,
        "Test webhook",
        provider="stripe",
        order_id="ord_settle_1",
        external_id="cs_settle_1",
    )
    center = fin.finance_center("CEO", "Привет", business_mode=mode, opportunities=[])
    assert len(center["settlements"]) == 1
    row = center["settlements"][0]
    assert row["amount_eur"] == 150.0
    assert row["settlement_status"] == "pending_settlement"
    assert row["paid_at"]
    assert row["available_at"]
    assert center["paid_by_client_eur"] == 150.0
    assert center["pending_settlement_eur"] == 150.0


def test_finance_center_includes_financial_view(tmp_path: Path):
    mode = BusinessModeService(tmp_path)
    fin = FinanceService(tmp_path)
    center = fin.finance_center("CEO", "Привет", business_mode=mode, opportunities=[])
    assert "financial_view" in center
    assert center["system_mode"] == "sandbox"
    assert center["withdrawal_enabled"] is False


def test_withdrawal_blocked_in_sandbox(tmp_path: Path):
    from app.integration.asset_scanner_service import AssetScannerService
    from app.integration.payment_checkout_service import PaymentCheckoutService

    mode = BusinessModeService(tmp_path)
    fin = FinanceService(tmp_path)
    snap_path = tmp_path / "finance_snapshot.json"
    snap_path.write_text('{"available_for_withdrawal_eur": 500.0, "pending_payouts_eur": 0.0}', encoding="utf-8")
    opp = OpportunityService(tmp_path)
    engine = MonetizationEngineService(
        opp,
        fin,
        PaymentCheckoutService(tmp_path),
        AssetScannerService(opp),
        tmp_path,
        business_mode=mode,
    )
    with pytest.raises(ValueError, match="sandbox_mode_withdrawal_disabled"):
        engine.request_withdrawal(50.0, "bank")
