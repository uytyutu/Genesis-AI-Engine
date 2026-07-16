"""CEO Outbox — auto-prepare discovery leads + batch approve."""

from pathlib import Path

import pytest

from app.integration.acquisition_studio_service import AcquisitionStudioService
from app.integration.opportunity_service import OpportunityService
from app.integration.sales_order_service import SalesOrderService
from app.integration.factory_intent_service import FactoryIntentService
from app.factory.factory_service import FactoryService


@pytest.fixture
def studio(tmp_path: Path):
    factory = FactoryService(tmp_path)
    intent = FactoryIntentService(tmp_path, factory)
    sales = SalesOrderService(tmp_path, intent)
    opp = OpportunityService(tmp_path)
    return AcquisitionStudioService(opp, sales), opp


def _row(company: str, url: str, **kwargs) -> dict:
    return {
        "source_id": "asset_scan",
        "opportunity_type": "asset",
        "company_name": company,
        "website_url": url,
        "status": "reviewed",
        "score": 78,
        "site_analysis": {
            "issue_count": 4,
            "issues": ["Kein Seitentitel", "Langsame Antwort", "Kein HTTPS"],
        },
        **kwargs,
    }


def test_auto_prepare_skips_blocklist(studio):
    svc, opp = studio
    opp.create(_row("Wiki", "https://www.wikipedia.org"))
    opp.create(_row("Real Shop", "https://beispiel-laden.de"))
    result = svc.auto_prepare_discovery_leads(limit=3, min_score=50, min_win_pct=40)
    assert result["ok"] is True
    assert "wikipedia" not in " ".join(result.get("prepared_names") or []).lower()
    assert result["prepared"] >= 0


def test_ceo_prepare_lands_in_approval_queue(studio):
    """CEO-initiated prepare always → pending_approval (even if price > 50€)."""
    svc, opp = studio
    row = opp.create(_row("Test GmbH", "https://test-gmbh.de"))
    prepared = svc.prepare_opportunity(row["id"], skip_qualification=True, auto_lane=False)
    assert prepared["outreach_status"] == "pending_approval"
    outbox = svc.ceo_outbox_summary()
    assert outbox["pending_count"] >= 1


def test_auto_lane_high_price_manual_review(studio, monkeypatch):
    svc, opp = studio
    row = opp.create(_row("Premium Co", "https://premium-co.de"))

    def _price(self, row, analysis):
        return "business", 350.0, "tier test"

    monkeypatch.setattr(AcquisitionStudioService, "_recommend_pricing", _price)
    # Force low win so price-tier manual_review applies (high win would auto-queue).
    import app.integration.opportunity_discovery_engine as ode

    real_eval = ode.evaluate_opportunity

    def _eval(row, **kwargs):
        ev = real_eval(row, **kwargs)
        ev["win_probability_pct"] = 40
        return ev

    monkeypatch.setattr(ode, "evaluate_opportunity", _eval)
    prepared = svc.prepare_opportunity(row["id"], skip_qualification=True, auto_lane=True)
    assert prepared["outreach_status"] == "manual_review"
    assert svc.approval_queue() == []
    assert len(svc.manual_review_queue()) >= 1
    promoted = svc.promote_manual_review(row["id"])
    assert promoted["outreach_status"] == "pending_approval"


def test_approve_batch(studio):
    svc, opp = studio
    row = opp.create(_row("Batch Co", "https://batch-co.de"))
    svc.prepare_opportunity(row["id"], skip_qualification=True, auto_lane=False)
    result = svc.approve_batch(limit=5)
    assert result["approved_count"] >= 1
    updated = opp.get(row["id"])
    assert updated["outreach_status"] in ("approved", "sent")
