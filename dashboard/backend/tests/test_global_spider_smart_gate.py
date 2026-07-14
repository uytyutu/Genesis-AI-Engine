from pathlib import Path

import pytest

from app.integration.global_spider_service import GlobalSpiderService
from app.integration.smart_gate_approval import SmartGateApprovalService
from app.integration.outreach_language_service import OutreachLanguageService
from app.integration.opportunity_service import OpportunityService


def test_infer_country_from_tld():
    assert GlobalSpiderService.infer_country_code("https://shop.example.de") == "DE"
    assert GlobalSpiderService.infer_country_code("https://shop.co.uk") == "GB"
    assert GlobalSpiderService.infer_country_code("https://shop.com") == "GLOBAL"


def test_global_spider_discovers_seed_targets(tmp_path: Path):
    cfg = tmp_path / "global_spider_config.json"
    cfg.write_text(
        '{"seed_targets":["https://seed1.example","https://seed2.example"],"regions_enabled":false}',
        encoding="utf-8",
    )
    spider = GlobalSpiderService(tmp_path)
    urls, stats = spider.discover_candidate_urls(batch_limit=10)
    assert len(urls) == 2
    assert stats["seeds"] == 2


def test_smart_gate_rejects_blacklist(tmp_path: Path):
    gate = SmartGateApprovalService(tmp_path)
    row = {
        "id": "x1",
        "company_name": "Casino Royale",
        "website_url": "https://casino.example",
        "potential_value_eur": 100,
        "meta": {"profit_score": 80},
        "site_analysis": {"has_https": True, "issues": []},
    }
    decision = gate.evaluate(row, context="outreach")
    assert decision.qualified is False
    assert decision.action == "pending_ceo_approval"
    assert decision.risk_score == 1.0


def test_smart_gate_auto_executes_junk_micro(tmp_path: Path):
    gate = SmartGateApprovalService(tmp_path)
    opp = OpportunityService(tmp_path)

    def update(oid, data):
        return opp.update(oid, data)

    row = opp.create(
        {
            "source_id": "asset_scan",
            "opportunity_type": "asset",
            "company_name": "Micro Site",
            "website_url": "http://micro.example",
            "meta": {"processing_lane": "junk_archive", "profit_score": 25},
            "site_analysis": {"has_https": False, "issues": ["wenig Inhalt"]},
        }
    )
    updated = gate.auto_execute_if_qualified(row, context="junk_micro", opportunity_update=update)
    meta = updated.get("meta") or {}
    assert meta.get("junk_smart_gate_pass") is True
    assert meta.get("execution_status") == "auto_executed"


def test_outreach_language_detects_english():
    svc = OutreachLanguageService()
    row = {
        "site_analysis": {
            "detected_lang": "en",
            "issues": ["No contact form on your website"],
            "title": "Local Plumber",
        },
        "fit_reason": "weak website",
    }
    subject, body, lang = svc.draft_outreach(
        company="Acme Plumbing",
        analysis=row["site_analysis"],
        package={"name": "Landing Basic"},
        price=350,
        fit_reason="weak website",
        row=row,
    )
    assert lang == "en"
    assert "Hello" in body
    assert "Acme Plumbing" in subject


def test_global_revenue_report_groups_by_country(tmp_path: Path):
    from app.integration.finance_service import FinanceService

    fin = FinanceService(tmp_path)
    opps = [
        {
            "revenue_eur": 50,
            "potential_value_eur": 100,
            "status": "won",
            "meta": {"country_code": "DE"},
        },
        {
            "revenue_eur": 30,
            "potential_value_eur": 80,
            "status": "won",
            "meta": {"country_code": "US"},
        },
        {
            "revenue_eur": 0,
            "potential_value_eur": 120,
            "status": "new",
            "meta": {"country_code": "IN"},
        },
    ]
    report = fin.global_revenue_report(opps)
    assert report["total_revenue_eur"] == 80
    assert report["countries_active"] == 2
    assert len(report["by_country"]) >= 3
