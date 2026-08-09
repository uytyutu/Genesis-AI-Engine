"""Gen1 SMTP + Business Profile + Test Email."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.platform_global_analytics import (
    build_email_analytics,
    build_gen1_readiness,
)
from app.integration.store_admin.business_profile import BusinessProfileService
from app.integration.store_admin.commerce_settings import StoreCommerceSettingsService
from app.integration.store_admin.email_templates import EmailTemplatesService


@pytest.fixture(autouse=True)
def _smtp_mock(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_SMTP_MOCK", "1")


def test_manual_email_connect_rejected(tmp_path: Path):
    svc = StoreCommerceSettingsService(tmp_path)
    with pytest.raises(ValueError, match="smtp_form_required"):
        svc.connect("ord-1", "gmail", account="info@x.de")


def test_smtp_connect_and_test_email(tmp_path: Path):
    svc = StoreCommerceSettingsService(tmp_path)
    out = svc.connect_email_smtp(
        "ord-1",
        "gmail",
        {
            "username": "info@company.de",
            "password": "app-pass-123",
            "from_email": "info@company.de",
            "from_name": "Nordlicht Möbel",
            "reply_to": "support@company.de",
            "support_email": "support@company.de",
        },
    )
    assert out["ok"] is True
    assert out["provider"]["status"] == "connected"
    assert out["provider"]["account"] == "info@company.de"
    assert out["vector_hint"]["suggest_test"] is True
    assert out["transport"]["password_set"] is True
    assert "password" not in out["transport"]

    # other providers disconnected
    hub = svc.integrations_hub("ord-1")
    email = next(s for s in hub["sections"] if s["id"] == "email")
    statuses = {i["id"]: i["status"] for i in email["items"]}
    assert statuses["gmail"] == "connected"
    assert statuses["smtp"] == "not_connected"

    test = svc.send_test_email("ord-1")
    assert test["ok"] is True
    assert test["test"]["status"] == "Delivered"
    assert test["message"].startswith("✓")

    ready = build_gen1_readiness(tmp_path)
    smtp = next(i for i in ready["items"] if i["id"] == "smtp")
    assert smtp["status"] == "done"

    analytics = build_email_analytics(tmp_path)
    assert analytics["connected"] >= 1
    assert analytics["test_success_rate"] is not None


def test_business_profile_ssot(tmp_path: Path):
    bp = BusinessProfileService(tmp_path)
    out = bp.update(
        "ord-1",
        {
            "company_name": "Nordlicht Möbel GmbH",
            "phone_country_code": "DE",
            "phone_primary": "030 1234567",
            "whatsapp": "030 1234567",
            "email_support": "info@nordlicht.de",
            "address": {
                "street": "Musterstr. 1",
                "postal_code": "10115",
                "city": "Berlin",
                "country": "DE",
            },
        },
    )
    assert out["profile"]["company_name"] == "Nordlicht Möbel GmbH"
    assert out["derived"]["tel_primary"].startswith("tel:")
    assert "wa.me" in (out["derived"]["whatsapp_url"] or "")
    contacts = bp.as_factory_contacts("ord-1")
    assert contacts["email"] == "info@nordlicht.de"
    assert contacts["phone"]


def test_email_templates_defaults(tmp_path: Path):
    tpl = EmailTemplatesService(tmp_path)
    pack = tpl.get("ord-1")
    ids = {t["id"] for t in pack["templates"]}
    assert {
        "order_confirmation",
        "payment_received",
        "invoice",
        "shipping_update",
        "password_reset",
        "welcome",
        "contact_form",
    } <= ids
    rendered = tpl.render(
        "ord-1",
        "order_confirmation",
        {
            "order_id": "SO-1",
            "company_name": "Nordlicht",
            "buyer_name": "Anna",
            "total": "99.00",
            "currency": "EUR",
            "support_email": "info@x.de",
        },
    )
    assert "SO-1" in rendered["subject"]
    assert "Anna" in rendered["body"]
