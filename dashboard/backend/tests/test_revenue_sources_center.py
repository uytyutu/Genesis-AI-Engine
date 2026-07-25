from app.integration.swarm_bridge import ensure_swarm_importable

ensure_swarm_importable()
from swarm.finance_reality_law import (
    is_reportable_revenue,
    law_manifest,
    profitability_gate,
    trial_passed,
)
from swarm.revenue_sources_center import build_revenue_sources_center


def test_finance_reality_law_ladder():
    law = law_manifest()
    assert law["id"] == "FINANCE_REALITY_OVER_SIMULATION"
    assert "Estimate ≠ Revenue" in law["inequalities_ru"]
    assert is_reportable_revenue("ESTIMATED") is False
    assert is_reportable_revenue("BOOKED") is True
    assert trial_passed(confirmed_ops=100) is True
    assert trial_passed(confirmed_ops=10, active_days=30) is True
    assert trial_passed(confirmed_ops=10, active_days=5) is False
    assert profitability_gate(net_eur=-0.01) == "disconnect_candidate"


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
