"""Language Consistency Gate L1–L5 — order language must not be guessed."""

from __future__ import annotations

from pathlib import Path

from app.factory.market_delivery import (
    deploy_readme,
    factory_locale_context,
    order_ui_lang,
    render_client_receipt_text,
)
from app.integration.locale_service import normalize_order_ui_lang
from app.integration.product_line import (
    SERVICE_WEBSITE,
    project_awaiting_payment_message,
    project_order_created_message,
)
from app.integration.receipt_email_service import ReceiptEmailService, _pack
from app.integration.sales_order_service import SalesOrderService


class _Factory:
    def submit(self, intent):  # noqa: ANN001
        return {"product_id": "prod-test-1"}

    class _Inner:
        def get_product(self, product_id: str):  # noqa: ANN001
            return {"id": product_id}

    _factory = _Inner()


def test_normalize_order_ui_lang_ceo_packs():
    assert normalize_order_ui_lang("de-DE") == "de"
    assert normalize_order_ui_lang("en") == "en"
    assert normalize_order_ui_lang("ru") == "ru"
    assert normalize_order_ui_lang("uk") == "uk"
    assert normalize_order_ui_lang(None, market_code="DE") == "de"
    assert normalize_order_ui_lang(None, market_code="US") == "en"


def test_factory_locale_context_from_order():
    ctx = factory_locale_context(
        {"ui_lang": "en", "market_code": "DE", "currency": "EUR", "locale": "en_DE"}
    )
    assert ctx["language"] == "en"
    assert ctx["market"] == "DE"
    assert ctx["currency"] == "EUR"
    assert ctx["locale"] == "en_DE"


def test_order_persists_ui_lang_and_status_exposes_it(tmp_path: Path):
    svc = SalesOrderService(tmp_path, _Factory())
    created = svc.create_order(
        {
            "business_name": "Bake EN",
            "description": "Fresh bread and coffee for local customers",
            "email": "buyer@example.com",
            "package_id": "basic",
            "market_code": "DE",
            "ui_lang": "en",
            "city": "Berlin",
        }
    )
    assert created["ui_lang"] == "en"
    order = svc.get_order(created["order_id"])
    assert order is not None
    assert order["ui_lang"] == "en"
    assert order["factory_context"]["language"] == "en"
    assert order["factory_context"]["market"] == "DE"
    status = svc.public_status(created["order_id"])
    assert status["ui_lang"] == "en"
    assert status["factory_context"]["language"] == "en"
    assert "Thank you" in created["message"] or "thank" in created["message"].lower()


def test_receipt_email_pack_matches_order_language():
    for lang in ("de", "en", "ru", "uk"):
        pack = _pack(lang)
        assert pack["received_title"]
        assert pack["receipt_title"]
    order = {
        "order_id": "ord-testlang01",
        "business_name": "Lang Cafe",
        "package_name": "Basic",
        "price_label": "350 €",
        "market_code": "DE",
        "ui_lang": "en",
        "email": "a@b.com",
        "launch_mode": False,
    }
    assert order_ui_lang(order) == "en"
    svc = ReceiptEmailService()
    result = svc.send_order_received(order=order)
    assert result.get("skipped") is True


def test_readme_follows_ui_lang_not_only_market():
    en_on_de = deploy_readme("DE", package_id="basic", ui_lang="en")
    assert "Publish" in en_on_de or "publish" in en_on_de.lower()
    assert "veröffentlichen" not in en_on_de.lower()


def test_product_line_messages_localized():
    de = project_awaiting_payment_message(ui_lang="de")
    en = project_awaiting_payment_message(ui_lang="en")
    assert "Bitte" in de
    assert "Please" in en
    msg = project_order_created_message(SERVICE_WEBSITE, ui_lang="ru", project_name="Test")
    assert "Спасибо" in msg or "заявк" in msg.lower()


def test_receipt_text_uses_order_ui_lang():
    text = render_client_receipt_text(
        order={
            "order_id": "ord-x",
            "business_name": "X",
            "package_name": "Basic",
            "price_label": "350 €",
            "market_code": "DE",
            "ui_lang": "en",
        },
        status_path="/order/status/ord-x",
        paid=350,
    )
    assert "Receipt" in text or "Order:" in text
    assert "Quittung" not in text
