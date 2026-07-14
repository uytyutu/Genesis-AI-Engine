"""Opportunity Discovery — Win Probability, Lost Reasons, Success Patterns."""

from pathlib import Path

from app.integration.opportunity_discovery_engine import (
    build_opportunity_discovery,
    estimate_confidence,
    evaluate_opportunity,
    load_lost_reasons,
    prepare_commercial_proposal,
    record_lost_reason,
)


def _sample_row(**overrides) -> dict:
    base = {
        "id": "opp-test-1",
        "source_id": "asset_scan",
        "opportunity_type": "asset",
        "company_name": "ABC GmbH",
        "website_url": "https://example-shop.de",
        "status": "reviewed",
        "score": 60,
        "site_analysis": {
            "issue_count": 5,
            "issues": [
                "Kein Seitentitel — schlecht für SEO",
                "Sehr wenig Inhalt — möglicherweise veraltet",
                "Langsame Antwort (~3200 ms)",
            ],
            "improvement_score": 48,
        },
        "meta": {"abandoned": True},
    }
    base.update(overrides)
    return base


def test_win_probability_with_reasons():
    row = _sample_row()
    ev = evaluate_opportunity(row)
    assert 5 <= ev["win_probability_pct"] <= 92
    assert len(ev["win_probability_reasons_ru"]) >= 2
    assert ev["legal_gate"]["legal"] is True


def test_build_opportunity_discovery_bundle():
    rows = [_sample_row(id=f"opp-{i}") for i in range(2)]
    bundle = build_opportunity_discovery(rows, farm_state={"labels_export_count": 5})
    assert bundle["engine_id"] == "opportunity_discovery"
    assert bundle["title_ru"] == "Обнаружение возможностей"
    assert "lost_reason_database" in bundle
    assert "success_patterns" in bundle
    assert bundle["ceo_hints_ru"]


def test_lost_reason_database(tmp_path: Path):
    record_lost_reason(
        opportunity_id="opp-x",
        reason_code="expensive",
        company_name="Test Co",
        memory_dir=tmp_path,
    )
    rows = load_lost_reasons(tmp_path)
    assert len(rows) == 1
    assert rows[0]["reason_ru"] == "Дорого"


def test_prepare_proposal_ru():
    prep = prepare_commercial_proposal(_sample_row())
    assert prep["ok"] is True
    assert "Коммерческое предложение" in prep["proposal_ru"]
    assert prep.get("win_probability_pct") is not None


def test_confidence_low_without_data():
    c = estimate_confidence({"conversations": 2, "won": 0, "lost": 0, "lost_reasons": 0})
    assert c["confidence_pct"] < 35
    assert len(c["confidence_reasons_ru"]) >= 2


def test_build_includes_learning_timeline():
    bundle = build_opportunity_discovery([_sample_row()])
    assert "learning_timeline" in bundle
    assert "confidence" in bundle
    assert bundle["learning_timeline"]["stages"]


def test_market_memory_penalty():
    lost = _sample_row(id="lost-1", status="lost", notes="дорого")
    row = _sample_row()
    ev = evaluate_opportunity(row, all_rows=[lost, row])
    assert ev["market_memory"]["prior_lost"] >= 1
