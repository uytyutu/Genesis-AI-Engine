from pathlib import Path

import pytest

from app.integration.engine_accounting_service import EngineAccountingService
from app.integration.finance_service import FinanceService
from app.integration.financial_export_bridge import FinancialExportBridge
from app.integration.opportunity_service import OpportunityService


@pytest.fixture()
def bridge(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    fin = FinanceService(tmp_path)
    accounting = EngineAccountingService(opp, tmp_path)
    return FinancialExportBridge(accounting, fin, tmp_path)


def test_collects_finance_transactions(bridge: FinancialExportBridge):
    tx_path = bridge._memory / "finance_transactions.jsonl"
    tx_path.write_text(
        '{"at":"2026-07-14T10:00:00+00:00","amount_eur":100,"label":"Stripe Erlös","provider":"stripe","payment_id":"pay1","category":"sale"}\n',
        encoding="utf-8",
    )
    entries = bridge.collect_ledger_entries()
    assert len(entries) >= 2
    assert any(e["event_type"] == "sale" for e in entries)
    assert any(e["event_type"] == "fee" for e in entries)


def test_export_datev_csv_format(bridge: FinancialExportBridge):
    tx_path = bridge._memory / "finance_transactions.jsonl"
    tx_path.write_text(
        '{"at":"2026-07-14T10:00:00+00:00","amount_eur":50,"label":"Test","provider":"stripe","payment_id":"x1","category":"sale"}\n',
        encoding="utf-8",
    )
    csv_text = bridge.export_datev_csv()
    assert "Buchungsdatum" in csv_text
    assert "DATEV" not in csv_text
    assert ";" in csv_text
    assert "8400" in csv_text


def test_export_summary_totals(bridge: FinancialExportBridge):
    tx_path = bridge._memory / "finance_transactions.jsonl"
    tx_path.write_text(
        '{"at":"2026-07-14T10:00:00+00:00","amount_eur":25,"label":"Fiat","provider":"stripe","payment_id":"a1","category":"sale"}\n',
        encoding="utf-8",
    )
    harvest_path = bridge._memory / "engine_harvest_events.jsonl"
    harvest_path.write_text(
        '{"type":"pattern_intel","at":"2026-07-14T11:00:00+00:00","data_product_value_eur":5,"opportunity_id":"opp-1","company":"X"}\n',
        encoding="utf-8",
    )
    summary = bridge.export_summary()
    assert summary["entries_count"] >= 2
    assert summary["fiat_gross_eur"] >= 25
    assert summary["format"] == "DATEV_Buchungsstapel_lite"
