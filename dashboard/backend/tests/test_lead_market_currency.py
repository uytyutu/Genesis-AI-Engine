"""Lead prepare stores market-local currency (not forced EUR)."""

from __future__ import annotations

from pathlib import Path

from app.factory.factory_service import FactoryService
from app.integration.acquisition_studio_service import AcquisitionStudioService
from app.integration.commerce_engine import resolve_final_offer
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.opportunity_service import OpportunityService
from app.integration.sales_order_service import SalesOrderService


def test_pl_offer_not_euro_label() -> None:
    offer = resolve_final_offer("business", "PL")
    assert offer.currency == "PLN"
    assert "€" not in offer.price_label
    assert "zł" in offer.price_label


def test_prepare_stores_local_currency(tmp_path: Path, monkeypatch) -> None:
    factory = FactoryService(tmp_path)
    intent = FactoryIntentService(tmp_path, factory)
    sales = SalesOrderService(tmp_path, intent)
    opp = OpportunityService(tmp_path)
    studio = AcquisitionStudioService(opp, sales)

    row = opp.create(
        {
            "source_id": "google_maps",
            "opportunity_type": "lead",
            "company_name": "Salon Kraków",
            "website_url": "https://example.pl",
            "fit_reason": "Google Places: слабый сайт",
            "contact": "owner@example.pl",
            "status": "reviewed",
            "score": 70,
            "site_analysis": {
                "issue_count": 4,
                "issues": ["mobile"],
                "title": "Salon",
            },
            "meta": {"market": "PL", "hunt_city": "Kraków"},
            "market": "PL",
        }
    )
    oid = row["id"]

    from app.integration import lead_qualification_gate as gate

    monkeypatch.setattr(
        gate,
        "qualify_lead",
        lambda *a, **k: {
            "passed": True,
            "blockers_ru": [],
            "channels": {"primary_email": "owner@example.pl"},
        },
    )

    prepared = studio.prepare_opportunity(oid, auto_lane=False)
    assert prepared.get("recommended_currency") == "PLN"
    assert "zł" in str(prepared.get("recommended_price_label") or "")
    assert "€" not in str(prepared.get("recommended_price_label") or "")
    item = studio._queue_item(prepared)
    assert item["recommended_currency"] == "PLN"
    assert "zł" in item["recommended_price_label"]


def test_queue_item_rewrites_stale_eur_for_foreign_market(tmp_path: Path) -> None:
    """Old rows stored EUR labels — owner list must show local currency."""
    factory = FactoryService(tmp_path)
    intent = FactoryIntentService(tmp_path, factory)
    sales = SalesOrderService(tmp_path, intent)
    opp = OpportunityService(tmp_path)
    studio = AcquisitionStudioService(opp, sales)

    row = opp.create(
        {
            "source_id": "google_maps",
            "opportunity_type": "lead",
            "company_name": "London Cafe",
            "website_url": "https://example.co.uk",
            "fit_reason": "weak site",
            "contact": "owner@example.co.uk",
            "status": "reviewed",
            "score": 65,
            "recommended_price_eur": 650,
            "recommended_currency": "EUR",
            "recommended_price_label": "650 €",
            "meta": {"market": "GB", "hunt_city": "London"},
            "market": "GB",
        }
    )

    item = studio._queue_item(row)
    assert item["recommended_currency"] == "GBP"
    assert "£" in item["recommended_price_label"]
    assert "€" not in item["recommended_price_label"]
