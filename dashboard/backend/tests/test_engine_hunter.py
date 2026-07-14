from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.integration.engine_hunter_service import EngineHunterService
from app.integration.opportunity_service import OpportunityService
from app.integration.public_intel_miner import PatternHit, PublicIntelMiner


@pytest.fixture()
def hunter(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    miner = PublicIntelMiner(tmp_path)
    acquisition = MagicMock()
    acquisition.prepare_opportunity.side_effect = lambda oid: {
        **opp.get(oid),
        "outreach_status": "pending_approval",
        "proposed_message": "Hallo — wir können Ihren Auftritt verbessern.",
    }
    return EngineHunterService(opp, acquisition, None, miner, tmp_path), opp


def test_mine_analysis_signals_maps_issues(hunter):
    svc, opp = hunter
    row = opp.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "Test GmbH",
            "website_url": "https://test.example",
            "site_analysis": {"issues": ["Kein HTTPS — unsicher", "wenig Inhalt"]},
        }
    )
    hits = svc.mine_analysis_signals(opp.get(row["id"]))
    lanes = {h.lane for h in hits}
    assert "outreach_lead" in lanes
    assert "seo_revival" in lanes


def test_run_hunter_scenarios_builds_drafts(hunter):
    svc, opp = hunter
    row = opp.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "Stale Shop",
            "website_url": "https://stale.example",
            "potential_value_eur": 90,
            "site_analysis": {
                "issues": ["CMS veraltet", "wenig Inhalt"],
                "title": "Stale Shop",
            },
            "meta": {"niche": "local_service"},
        }
    )
    regex_hits = [
        PatternHit(
            pattern_id="copyright_stale",
            pattern_label="Veraltetes Copyright",
            matched_value="Copyright 2019",
            source_url="https://stale.example",
            context_snippet="Copyright 2019",
            confidence=0.8,
            valuation_eur=50.0,
            lane="seo_revival",
        )
    ]
    updated = svc.run_hunter_scenarios(row["id"], regex_hits)
    meta = updated.get("meta") or {}
    assert meta.get("hunter_mode") == "service_first"
    assert meta.get("zero_cost") is True
    assert meta.get("seo_content_draft")
    assert meta.get("bounty_report_draft")
    assert meta.get("outreach_prepared") is True
    assert meta["hunter_scenarios"]["seo_revival"] >= 1


def test_dataset_export_csv(hunter, tmp_path: Path):
    svc, opp = hunter
    ds = tmp_path / "hunter_dataset.jsonl"
    ds.write_text(
        '{"at":"2026-07-14T10:00:00+00:00","company":"A","url":"https://a.de","niche":"local",'
        '"issues":["x"],"pattern_hits":["no_https_issue"],"potential_eur":100}\n',
        encoding="utf-8",
    )
    svc._memory = tmp_path  # noqa: SLF001
    csv_text = svc.dataset_export_csv()
    assert "Firma" in csv_text
    assert "A" in csv_text
    assert "https://a.de" in csv_text


def test_hunter_dashboard_counts(hunter):
    svc, opp = hunter
    opp.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "Dash Co",
            "website_url": "https://dash.example",
            "meta": {
                "hunter_scenarios": {"bounty": 1, "seo_revival": 2, "outreach": 1, "dataset": 0},
                "hunter_value_eur": 200,
                "outreach_prepared": True,
            },
        }
    )
    dash = svc.hunter_dashboard()
    assert dash["mode"] == "service_first"
    assert dash["priority"] == "outreach"
    assert dash["scenario_stats"]["seo_revival"] >= 2
    assert dash["hunter_value_eur"] >= 200
