from app.integration.swarm_bridge import ensure_swarm_importable

ensure_swarm_importable()
from swarm.finance_ledger import FinanceLedger
from swarm.revenue_source import (
    CONFIDENCE_CONFIRMED,
    CONFIDENCE_ESTIMATED,
    catalog,
    is_withdrawable_confidence,
)
from swarm.revenue_source_capabilities import audit_report
from swarm.unit_economics import build_unit_economics


def test_audit_toloka_is_requester_not_earnable():
    report = audit_report()
    by_id = {r["id"]: r for r in report["sources"]}
    toloka = by_id["toloka"]
    assert toloka["role"] == "requester"
    assert toloka["balance_api"] == "no"
    assert toloka["auto_withdraw"] == "no"
    assert toloka["can_earn_via_virtus"] is False
    assert by_id["stripe"]["can_earn_via_virtus"] is True
    assert by_id["appen"]["registry_only"] is True
    assert "earnable_ids" in report["summary"]
    assert report["summary"]["earnable_ids"] == ["stripe"]


def test_revenue_source_catalog_has_confidence_ladder():
    cat = catalog()
    ids = [c["id"] for c in cat["confidence_states"]]
    assert ids == [
        "SIMULATED",
        "ESTIMATED",
        "PENDING",
        "CONFIRMED",
        "WITHDRAWN",
        "BOOKED",
    ]
    assert is_withdrawable_confidence(CONFIDENCE_CONFIRMED) is True
    assert is_withdrawable_confidence(CONFIDENCE_ESTIMATED) is False


def test_unit_economics_marks_internal_as_estimate():
    report = build_unit_economics(
        farm_state={"total_tasks_done": 100, "llm_cost_eur": 0.4, "today_earned_eur": 1.0}
    )
    by_id = {r["source_id"]: r for r in report["rows"]}
    assert by_id["ai_labeling"]["confidence"] == "ESTIMATED"
    assert by_id["ai_labeling"]["is_real_income"] is False
    assert by_id["toloka"]["avg_gross_eur"] == 0.0
    assert report["summary"]["best_real_source"] in {None, "stripe"}


def test_finance_ledger_csv_real_only(tmp_path):
    ledger = FinanceLedger(tmp_path)
    ledger.append(
        source_id="internal",
        amount=0.05,
        confidence=CONFIDENCE_ESTIMATED,
        description="estimate",
    )
    ledger.append(
        source_id="stripe",
        amount=49.0,
        confidence=CONFIDENCE_CONFIRMED,
        payout_id="pi_test",
        description="order paid",
    )
    csv_body = ledger.export_csv(real_only=True)
    assert "pi_test" in csv_body
    assert "estimate" not in csv_body
    snap = ledger.summary()
    assert snap["real_withdrawable_eur"] == 49.0
