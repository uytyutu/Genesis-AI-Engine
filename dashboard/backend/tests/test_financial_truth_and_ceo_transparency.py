"""Financial Truth + revenue source transparency + Opire execution success."""

from __future__ import annotations

from pathlib import Path

from swarm.finance_ledger import FinanceLedger
from swarm.finance_reality_law import (
    TAX_ALLOWED_CONFIDENCE,
    financial_truth_manifest,
    tax_export_allowed,
)
from swarm.revenue_source import CONFIDENCE_CONFIRMED, CONFIDENCE_ESTIMATED, CONFIDENCE_SIMULATED
from swarm.revenue_sources_center import build_revenue_sources_center
from swarm.opire_farm import OpireFarmEngine


def test_tax_export_allowed_only_confirmed():
    assert tax_export_allowed("CONFIRMED")
    assert tax_export_allowed("BOOKED")
    assert tax_export_allowed("WITHDRAWN")
    assert not tax_export_allowed("ESTIMATED")
    assert not tax_export_allowed("SIMULATED")
    assert not tax_export_allowed("PENDING")
    assert "CONFIRMED" in TAX_ALLOWED_CONFIDENCE


def test_ledger_tax_report_ignores_simulation(tmp_path: Path):
    led = FinanceLedger(tmp_path)
    led.append(
        source_id="demo",
        amount=3644.0,
        confidence=CONFIDENCE_SIMULATED,
        description="demo replay",
    )
    led.append(
        source_id="stripe",
        amount=49.0,
        confidence=CONFIDENCE_CONFIRMED,
        description="real payment",
        payout_id="po_test",
    )
    snap = led.summary()
    assert snap["tax_report_confirmed_eur"] == 49.0
    assert snap["simulation_estimate_eur"] == 3644.0
    csv = led.export_csv(real_only=True)
    assert "3644" not in csv
    assert "49" in csv
    assert financial_truth_manifest()["id"] == "FINANCIAL_TRUTH_RULE"


def test_revenue_source_why_not_earned_fields():
    center = build_revenue_sources_center(
        stripe_connected=True,
        stripe_webhook=True,
        stripe_income_eur=0,
        opire={
            "ceo_approved": 3,
            "executed": 0,
            "draft_pr": 0,
            "failed": 0,
            "skipped": 0,
            "paid": 0,
            "github_token": False,
        },
    )
    by_id = {s["id"]: s for s in center["sources"]}
    stripe = by_id["stripe"]
    assert stripe["stage"]
    assert stripe["why_not_earned_ru"]
    assert stripe["next_step_ru"]
    assert stripe["why_button_label_ru"]
    opire = by_id["opire"]
    assert opire["stage"] == "EXECUTION_PAUSED"
    assert "Approve" in opire["why_not_earned_ru"] or "Execution" in opire["why_not_earned_ru"]


def test_execution_success_in_opire_panel(tmp_path: Path):
    eng = OpireFarmEngine(tmp_path)
    panel = eng.panel(force_scan=False)
    assert "execution_success" in panel
    es = panel["execution_success"]
    assert "approved" in es and "started" in es and "completed" in es
    assert "failed" in es and "skipped" in es
    assert "avg_execution_s" in es
