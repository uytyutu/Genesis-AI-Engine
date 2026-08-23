"""Gen2 Stage 0 Service Marketplace catalog."""

from app.integration.service_marketplace_stage0 import build_service_marketplace_catalog


def test_stage0_catalog_has_activate_and_coming_soon():
    out = build_service_marketplace_catalog()
    assert out["stage"] == "gen2_stage_0"
    ids = {s["id"] for s in out["services"]}
    assert "website" in ids
    assert "ai_store" in ids
    assert "digital_employee" in ids
    assert "seo" in ids
    soon = {s["id"] for s in out["coming_soon"]}
    assert "crm" in soon
    assert "ai_marketing" in soon
    assert all(s["badge"] == "coming_soon" for s in out["coming_soon"])
    assert all(s.get("activate_href") or s["id"] == "booking" for s in out["services"])
