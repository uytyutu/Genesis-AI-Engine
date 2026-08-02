from app.integration.swarm_bridge import ensure_swarm_importable

ensure_swarm_importable()
from swarm.finance_reality_law import (
    income_phase,
    is_modeling_only,
    is_real_money_event,
    is_reportable_revenue,
    law_manifest,
    module_may_mutate_real,
    profitability_gate,
    real_money_missing_fields,
    trial_passed,
)
from swarm.revenue_sources_center import build_revenue_sources_center


def test_finance_reality_law_ladder():
    law = law_manifest()
    assert law["id"] == "FINANCE_REALITY_OVER_SIMULATION"
    assert law["version"] == "1.4"
    assert "Estimate ≠ Revenue" in law["inequalities_ru"]
    assert "Modeling ≠ REAL income" in law["inequalities_ru"]
    assert len(law["real_required_fields"]) == 5
    assert law["real_truth_pipeline"][-1] == "roi"
    assert law["connector_ingest_pipeline"] == [
        "connector",
        "normalize_payout",
        "is_real_money_event",
        "finance_ledger",
    ]
    assert "Источник истины один" in law["law_2_ru"]
    assert "Live Earn Connector" in law["law_3_ru"]
    assert is_reportable_revenue("ESTIMATED") is False
    assert is_reportable_revenue("BOOKED") is True
    assert trial_passed(confirmed_ops=100) is True
    assert trial_passed(confirmed_ops=10, active_days=30) is True
    assert trial_passed(confirmed_ops=10, active_days=5) is False
    assert profitability_gate(net_eur=-0.01) == "disconnect_candidate"
    assert module_may_mutate_real("farm_engine") is False
    assert module_may_mutate_real("ai_router") is False
    assert module_may_mutate_real("finance_ledger") is True
    assert is_modeling_only() is True
    ready = income_phase(
        live_earn_connector=True,
        legal_review_pass=True,
        confirmed_external_payouts=True,
    )
    assert ready["phase"] == "real_eligible"
    assert ready["is_modeling"] is False


def test_hard_real_requires_five_fields():
    assert is_real_money_event({"amount": 0.15, "currency": "EUR"}) is False
    assert "external_payout_id" in real_money_missing_fields({"amount": 0.15})
    full = {
        "external_payout_id": "po_72831",
        "amount": 0.15,
        "currency": "EUR",
        "paid_at": "2026-08-04T14:31:00+00:00",
        "source_id": "connector_x",
    }
    assert is_real_money_event(full) is True
    assert real_money_missing_fields(full) == []
    # Aliases used by ledger
    assert is_real_money_event(
        {
            "payout_id": "po_1",
            "amount_eur": 2.1,
            "currency": "EUR",
            "booked_at": "2026-08-04T14:31:00+00:00",
            "platform": "stripe",
        }
    )


def test_revenue_sources_center_stripe_active_toloka_unsupported():
    center = build_revenue_sources_center(
        stripe_income_eur=350.0,
        stripe_connected=True,
        farm_estimate_eur=12.5,
    )
    by_id = {s["id"]: s for s in center["sources"]}
    assert by_id["stripe"]["status"] == "active"
    assert by_id["stripe"]["confidence"] == "BOOKED"
    assert by_id["stripe"]["automation_score"] == 100
    assert "350" in by_id["stripe"]["income_label"]
    assert by_id["toloka"]["status"] == "unsupported"
    assert by_id["toloka"]["automation_score"] == 10
    assert by_id["awin"]["status"] == "candidate"
    assert by_id["awin"]["confidence"] == "NOT_CONNECTED"
    assert by_id["groq"]["status"] == "cost"
    assert center["law"]["title_en"] == "Reality over Simulation"
    assert "Discovery" in center["discovery_ru"] or "автопоиск" in center["discovery_ru"].lower()
    why = by_id["toloka"]["why_ru"].lower()
    assert "заказчик" in why or "requester" in why or "performer" in why


def test_revenue_sources_keys_present_not_active():
    center = build_revenue_sources_center(
        stripe_income_eur=0.0,
        stripe_connected=True,
        stripe_webhook=True,
        digistore_connected=True,
        awin_connected=False,
    )
    by_id = {s["id"]: s for s in center["sources"]}
    assert by_id["stripe"]["status"] == "candidate"
    assert by_id["stripe"]["status_label"] == "Ключ есть"
    assert by_id["stripe"]["confidence"] == "KEYS_PRESENT"
    assert by_id["digistore24"]["keys_present"] is True
    assert by_id["digistore24"]["confidence"] == "KEYS_PRESENT"
    assert by_id["awin"]["keys_present"] is False
    assert center["keys_probe"]["digistore24"] is True
    assert center["summary"]["keys_present"] == 2
