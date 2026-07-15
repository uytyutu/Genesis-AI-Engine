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


def test_ceo_outbox_summary(studio):
    svc, opp = studio
    row = opp.create(_row("Test GmbH", "https://test-gmbh.de"))
    svc.prepare_opportunity(row["id"])
    outbox = svc.ceo_outbox_summary()
    assert outbox["pending_count"] >= 1
    assert "Stripe" in outbox["money_path_ru"] or "клиент" in outbox["money_path_ru"]


def test_approve_batch(studio):
    svc, opp = studio
    row = opp.create(_row("Batch Co", "https://batch-co.de"))
    svc.prepare_opportunity(row["id"])
    result = svc.approve_batch(limit=5)
    assert result["approved_count"] >= 1
    updated = opp.get(row["id"])
    assert updated["outreach_status"] in ("approved", "sent")
