"""Public truth catalog — Mission 1 pricing display."""

from app.integration.pricing_display_service import PricingDisplayService
from app.integration.public_truth_catalog import build_truth_pricing_display


def test_truth_catalog_matches_sales_packages():
    truth = build_truth_pricing_display()
    items = truth["service_categories"][0]["items"]
    assert items[0]["available"] is True
    assert "350" in items[0]["price_label"]
    assert truth["subscriptions"][0]["id"] == "free"
    assert all(s.get("available") is not True or s["id"] == "free" for s in truth["subscriptions"])


def test_pricing_display_defaults_to_truth_without_json(tmp_path):
    svc = PricingDisplayService(memory_dir=tmp_path)
    data = svc.get_display()
    assert data["version"].startswith("mission1-truth")
    assert data["service_categories"][0]["items"][0]["cta_href"] == "/order"
