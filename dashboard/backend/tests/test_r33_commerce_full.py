"""R3.3.2–R3.3.6 Commerce + Mission Control Integrations Analytics."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.platform_global_analytics import (
    PlatformGlobalAnalyticsService,
    build_integrations_analytics,
)
from app.integration.store_admin.commerce_settings import StoreCommerceSettingsService
from app.integration.vector.capabilities import action_for, is_live


def test_shipping_capability_live():
    assert is_live("shipping_carriers") is True
    assert action_for("shipping_carriers")["kind"] == "navigate_section"
    assert is_live("taxes_vat") is True
    assert is_live("email_transactional") is True
    assert is_live("invoices_pdf") is True
    assert is_live("notifications_channels") is True


def test_connect_dhl_and_shipping_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_SHIPPING_MOCK", "1")
    from app.integration.store_admin.shipping_api_service import StoreShippingApiService

    svc = StoreCommerceSettingsService(tmp_path)
    with pytest.raises(ValueError, match="shipping_api_required"):
        svc.connect("ord-1", "dhl", account="dhl@shop.de")
    out = StoreShippingApiService(tmp_path).connect_carrier(
        "ord-1", "dhl", {"account_name": "dhl@shop.de"}
    )
    assert out["provider"]["status"] == "connected"
    assert out["provider"]["account"] == "dhl@shop.de"

    cfg = svc.update_shipping_config(
        "ord-1",
        {
            "country": "DE",
            "regions": ["DE", "AT"],
            "free_shipping_from_eur": 100,
            "min_order_eur": 20,
            "processing_days": 2,
            "rate_mode": "fixed",
            "methods": [
                {
                    "id": "dhl_standard",
                    "carrier": "dhl",
                    "label": "DHL Standard",
                    "days_min": 3,
                    "days_max": 5,
                    "price_eur": 7.9,
                    "enabled": True,
                },
                {
                    "id": "pickup_free",
                    "carrier": "pickup",
                    "label": "Самовывоз",
                    "days_min": 0,
                    "days_max": 0,
                    "price_eur": 0,
                    "enabled": True,
                },
            ],
        },
    )
    assert cfg["shipping_config"]["free_shipping_from_eur"] == 100
    assert len(cfg["shipping_config"]["methods"]) >= 2

    got = svc.get("ord-1")
    assert got["shipping_ready"] is True
    tips = got["shipping_tips"]
    assert any("DHL" in t["message"] or "подключ" in t["message"].lower() for t in tips)


def test_tax_profiles(tmp_path: Path):
    svc = StoreCommerceSettingsService(tmp_path)
    out = svc.update_tax_config("ord-1", {"profile": "de_standard", "company_vat_id": "DE99"})
    assert out["tax_config"]["standard_rate_pct"] == 19.0
    assert out["taxes"]["status"] == "connected"

    reduced = svc.update_tax_config("ord-1", {"profile": "de_reduced"})
    assert reduced["tax_config"]["standard_rate_pct"] == 7.0

    exempt = svc.update_tax_config("ord-1", {"profile": "vat_exempt"})
    assert exempt["tax_config"]["vat_exempt"] is True


def test_email_gmail_and_notifications(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_SMTP_MOCK", "1")
    svc = StoreCommerceSettingsService(tmp_path)
    with pytest.raises(ValueError, match="smtp_form_required"):
        svc.connect("ord-1", "gmail")
    g = svc.connect_email_smtp(
        "ord-1",
        "gmail",
        {
            "username": "shop@gmail.com",
            "password": "app-pass",
            "from_email": "shop@gmail.com",
        },
    )
    assert g["provider"]["status"] == "connected"

    tg = svc.connect("ord-1", "telegram", account="@shop_bot")
    assert tg["provider"]["status"] == "connected"

    hub = svc.integrations_hub("ord-1")
    email = next(s for s in hub["sections"] if s["id"] == "email")
    assert {i["id"] for i in email["items"]} >= {"gmail", "outlook", "microsoft365", "smtp"}


def test_invoice_allocate(tmp_path: Path):
    svc = StoreCommerceSettingsService(tmp_path)
    svc.update_invoice_config(
        "ord-1", {"prefix": "INV", "next_number": 1001, "auto_pdf": True}
    )
    a = svc.allocate_invoice_number("ord-1")
    assert a["invoice_number"] == "INV-1001"
    b = svc.allocate_invoice_number("ord-1")
    assert b["invoice_number"] == "INV-1002"
    cn = svc.allocate_credit_note("ord-1")
    assert cn["credit_note_number"].startswith("CN-")


def test_integrations_analytics_aggregation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_SHIPPING_MOCK", "1")
    monkeypatch.setenv("GENESIS_SMTP_MOCK", "1")
    from app.integration.store_admin.shipping_api_service import StoreShippingApiService

    a = StoreCommerceSettingsService(tmp_path)
    b = StoreCommerceSettingsService(tmp_path)
    StoreShippingApiService(tmp_path).connect_carrier(
        "store-a", "dhl", {"account_name": "dhl-a"}
    )
    a.apply_stripe_oauth(
        "store-a", stripe_user_id="acct_mock_a", account_label="a@x.de", mock=True
    )
    b.apply_stripe_oauth(
        "store-b", stripe_user_id="acct_mock_b", account_label="b@x.de", mock=True
    )
    b.connect_email_smtp(
        "store-b",
        "gmail",
        {
            "username": "b@gmail.com",
            "password": "app-pass",
            "from_email": "b@gmail.com",
        },
    )

    stats = build_integrations_analytics(tmp_path)
    assert stats["stores_scanned"] == 2
    stripe = next(p for p in stats["providers"] if p["id"] == "stripe")
    assert stripe["connected_stores"] == 2
    dhl = next(p for p in stats["providers"] if p["id"] == "dhl")
    assert dhl["connected_stores"] == 1
    assert stats["commerce_incomplete_stores"] >= 1

    snap = PlatformGlobalAnalyticsService(tmp_path).global_snapshot(
        finance={"revenue_today_eur": 10},
        company={"total_clients": 3},
    )
    assert snap["title"] == "Global Analytics"
    assert any(s["id"] == "commerce" for s in snap["sections"])
    assert snap["integrations"]["stores_scanned"] == 2
