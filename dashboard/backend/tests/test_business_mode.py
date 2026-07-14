from pathlib import Path

import pytest

from app.integration.business_mode_service import BusinessModeService
from app.integration.engine_accounting_service import EngineAccountingService
from app.integration.opportunity_service import OpportunityService


def test_default_sandbox_mode(tmp_path: Path):
    mode = BusinessModeService(tmp_path)
    assert mode.is_sandbox()
    assert not mode.financial_docs_enabled()


def test_activate_business_requires_phrase(tmp_path: Path):
    mode = BusinessModeService(tmp_path)
    with pytest.raises(ValueError, match="invalid_confirm_phrase"):
        mode.activate_business(confirmed=True, phrase="wrong")


def test_activate_business_live(tmp_path: Path):
    mode = BusinessModeService(tmp_path)
    status = mode.activate_business(confirmed=True, phrase="ACTIVATE BUSINESS")
    assert status["system_mode"] == "live"
    assert mode.financial_docs_enabled()


def test_potential_revenue_not_realized(tmp_path: Path):
    mode = BusinessModeService(tmp_path)
    opp = OpportunityService(tmp_path)
    opp.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "Lead Co",
            "website_url": "https://lead.example",
            "potential_value_eur": 150,
            "meta": {"hunter_value_eur": 50, "profit_score": 60},
        }
    )
    pot = mode.compute_potential_revenue(opp.list_opportunities())
    assert pot["potential_revenue_eur"] == 200
    assert pot["revenue_quality"] == "projected"


def test_accounting_sandbox_blocks_exports(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    accounting = EngineAccountingService(opp, tmp_path, business_mode=BusinessModeService(tmp_path))
    summary = accounting.accounting_summary()
    assert summary["system_mode"] == "sandbox"
    assert summary["financial_docs_enabled"] is False
    assert summary["potential_revenue"]["potential_revenue_eur"] >= 0
    with pytest.raises(ValueError, match="sandbox_mode"):
        accounting.export_csv()
