from pathlib import Path

import pytest

from app.integration.engine_accounting_service import EngineAccountingService
from app.integration.opportunity_service import OpportunityService


@pytest.fixture()
def accounting(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    return EngineAccountingService(opp, tmp_path)


def test_net_income_after_fees_and_tax(accounting: EngineAccountingService):
    accounting.save_tax_settings({"vat_rate_percent": 19.0, "stripe_fee_percent": 1.4, "stripe_fee_fixed_eur": 0.25})
    opp = accounting._opportunity.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "Test Asset GmbH",
            "website_url": "https://example.de",
            "potential_value_eur": 100,
            "revenue_eur": 100,
            "fit_reason": "Public business only",
        }
    )
    accounting._opportunity.update(opp["id"], {"status": "won", "revenue_eur": 100.0})
    summary = accounting.accounting_summary()
    assert summary["harvest_count"] >= 1
    assert summary["totals"]["gross_eur"] >= 100
    assert summary["totals"]["net_clean_eur"] < summary["totals"]["gross_eur"]


def test_csv_export_de_format(accounting: EngineAccountingService):
    accounting.save_tax_settings({"vat_rate_percent": 19})
    csv_text = accounting.export_csv()
    assert "Datum" in csv_text
    assert "MwSt_Reserve" in csv_text
    assert ";" in csv_text


def test_invoice_html(accounting: EngineAccountingService):
    row = accounting._opportunity.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "Parked Site",
            "website_url": "https://parked.example",
            "revenue_eur": 50,
        }
    )
    accounting._opportunity.update(row["id"], {"status": "won", "revenue_eur": 50})
    html = accounting.generate_invoice_html(row["id"])
    assert "Rechnung" in html
    assert "Parked Site" in html
