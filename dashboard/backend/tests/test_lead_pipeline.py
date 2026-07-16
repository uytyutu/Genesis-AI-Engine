"""Lead pipeline — ingest_lead + gate funnel metrics."""

from __future__ import annotations

from pathlib import Path

from app.integration.lead_pipeline_service import (
    detect_niche_key,
    gate_funnel_metrics,
    ingest_lead,
)
from app.integration.opportunity_service import OpportunityService
from app.integration.outreach_language_service import OutreachLanguageService


def test_detect_niche_kfz_zahnarzt():
    assert detect_niche_key(company="Müller Kfz-Werkstatt", query="") == "kfz"
    assert detect_niche_key(company="Praxis Dr. Zahn", query="Zahnarzt Köln") == "zahnarzt"
    assert detect_niche_key(company="Dachdecker Nord", query="Dachdecker Köln") == "dach"
    assert detect_niche_key(company="Café Sonne", query="") == "general"


def test_ingest_lead_dedupe(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    first = ingest_lead(
        opp,
        {
            "source_id": "google_maps",
            "company_name": "KFZ Süd",
            "website_url": "https://kfz-sued.de",
            "meta": {"place_id": "place-1"},
            "query": "Kfz-Werkstatt",
        },
    )
    assert first["created"] is True
    assert first["row"]["meta"]["niche"] == "kfz"

    second = ingest_lead(
        opp,
        {
            "source_id": "google_maps",
            "company_name": "KFZ Süd GmbH",
            "website_url": "https://kfz-sued.de",
            "meta": {"place_id": "place-1"},
        },
    )
    assert second["duplicate"] is True
    assert second["created"] is False
    assert len(opp.list_opportunities(limit=50)) == 1


def test_ingest_blocks_demo_host(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    r = ingest_lead(
        opp,
        {
            "source_id": "manual",
            "company_name": "Wiki",
            "website_url": "https://www.wikipedia.org/wiki/Test",
        },
    )
    assert r["blocked"] is True
    assert opp.list_opportunities(limit=10) == []


def test_gate_funnel_metrics(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    a = opp.create(
        {
            "source_id": "google_maps",
            "company_name": "A",
            "website_url": "https://a.de",
        }
    )
    opp.update(a["id"], {"outreach_status": "pending_approval", "proposed_message": "x"})
    b = opp.create(
        {
            "source_id": "google_maps",
            "company_name": "B",
            "website_url": "https://b.de",
            "meta": {"quality_archive": True},
        }
    )
    opp.update(b["id"], {"meta": {**(b.get("meta") or {}), "quality_archive": True}})
    metrics = gate_funnel_metrics(opp, memory_dir=tmp_path)
    assert metrics["summary"]["found"] >= 2
    assert metrics["summary"]["approve"] >= 1
    assert any(s["id"] == "quality_archive" for s in metrics["stages"])


def test_kfz_template_in_outreach(monkeypatch):
    import app.integration.outreach_language_service as ols

    monkeypatch.setattr(ols._AI, "generate_personalized_offer", lambda **kwargs: None)
    svc = OutreachLanguageService()
    subject, body, lang = svc.draft_outreach(
        company="Auto Müller",
        analysis={"issues": ["Kein HTTPS"]},
        package={"name": "Landing"},
        price=350,
        fit_reason="Kfz",
        language="de",
        row={"meta": {"niche": "kfz"}, "company_name": "Auto Müller"},
    )
    assert lang == "de"
    assert "Werkstatt" in subject or "Termine" in subject
    assert "Kfz" in body or "Werkstatt" in body or "Diagnose" in body
    assert "/order" in body


def test_market_lesson_required_on_reply(tmp_path: Path):
    from app.factory.factory_service import FactoryService
    from app.integration.acquisition_studio_service import AcquisitionStudioService
    from app.integration.factory_intent_service import FactoryIntentService
    from app.integration.sales_order_service import SalesOrderService

    factory = FactoryService(tmp_path)
    intent = FactoryIntentService(tmp_path, factory)
    sales = SalesOrderService(tmp_path, intent)
    opp = OpportunityService(tmp_path)
    created = ingest_lead(
        opp,
        {
            "source_id": "google_maps",
            "company_name": "Auto Lernen",
            "website_url": "https://auto-lernen.de",
            "meta": {"place_id": "place-learn"},
            "query": "Kfz",
        },
    )
    row = created["row"]
    row["outreach_status"] = "sent"
    row["status"] = "contacted"
    opp._save_rows([row])

    studio = AcquisitionStudioService(opp, sales)
    try:
        studio.record_interaction(row["id"], "replied", "")
        assert False, "expected market_reason_required"
    except ValueError as exc:
        assert str(exc) == "market_reason_required"

    updated = studio.record_interaction(
        row["id"],
        "replied",
        "",
        market_reason="interested",
        market_lesson="Просят детали по Landing",
    )
    assert updated["status"] == "replied"
    assert updated["meta"]["last_market_reason"] == "interested"
    assert "Заинтересовались" in updated["meta"]["last_market_lesson"]
    report = studio.evidence_report()
    assert report["recent_lessons"]
    assert report["learning"]["lessons_logged"] >= 1
    assert report["learning"]["completeness_pct"] >= 0
    assert any(r["reason"] == "interested" for r in report["reason_counts"])
    assert "сигнал рынка" in report["milestone_ru"] or "sniper" in report["milestone_ru"].casefold()
