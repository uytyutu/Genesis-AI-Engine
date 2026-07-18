"""Pilot service catalog — quotes expand first-euro paths without new engines."""

from app.integration.pilot_service_catalog import (
    ceo_catalog_snapshot,
    public_pilot_categories,
    signals_from_site_issues,
    suggest_services_for_signals,
    suggest_services_for_site_issues,
)


def test_spider_signal_maps_to_boost():
    assert "site_boost" in suggest_services_for_signals(["no_whatsapp"])


def test_site_issues_https_to_security():
    sigs = signals_from_site_issues(["Kein HTTPS — unsicher für Besucher"])
    assert "no_https" in sigs
    services = suggest_services_for_site_issues(["Kein HTTPS — unsicher für Besucher"])
    assert "security_audit" in services or "website_audit" in services


def test_ceo_snapshot_checkout_packages():
    snap = ceo_catalog_snapshot()
    assert "basic" in snap["checkout_online"]
    assert "site_boost" in snap["pilot_quote"]
    assert snap["spider_signal_map"]["no_site"]


def test_go_to_market_has_three_levels():
    from app.integration.pilot_service_catalog import public_go_to_market

    gtm = public_go_to_market()
    assert len(gtm["levels"]) == 3
    assert gtm["niches"]
    assert gtm["signals"]
    assert gtm["modes"]["auto"]


def test_truth_display_has_checkout_cta():
    # Avoid public_truth_catalog (circular import with genesis_core_intelligence).
    cats = public_pilot_categories()
    assert any(c["id"] == "path_a_pilot" for c in cats)
    from app.integration.sales_order_service import _PACKAGES

    assert "basic" in _PACKAGES
    assert "business" in _PACKAGES
    assert "premium" in _PACKAGES
