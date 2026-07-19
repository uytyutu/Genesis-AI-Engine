"""Market-aware Path A: status copy + Factory legal packs."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from app.factory.client_legal_pages import ClientLegalInfo, write_client_legal_pages
from app.factory.factory_service import FactoryService
from app.factory.market_delivery import (
    client_status_label,
    deploy_readme,
    market_legal_pack,
    market_ui_lang,
)
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.finance_service import FinanceService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.revenue_pipeline_service import RevenuePipelineService
from app.integration.sales_order_service import SalesOrderService


def test_market_ui_lang_and_legal_packs():
    assert market_ui_lang("US") == "en"
    assert market_ui_lang("DE") == "de"
    assert market_ui_lang("UA") == "uk"
    assert market_legal_pack("US") == "us_privacy"
    assert market_legal_pack("DE") == "de_impressum"
    assert market_legal_pack("FR") == "placeholder"
    assert "Hetzner" in deploy_readme("DE")
    assert "Hetzner" not in deploy_readme("US")
    assert "Cloudflare" in deploy_readme("US")
    assert client_status_label("paid", "US") == "Paid"
    assert client_status_label("paid", "DE") == "Bezahlt"


def test_us_legal_pages_no_de_impressum(tmp_path: Path):
    info = ClientLegalInfo(business_name="Acme Dental", email="a@acme.com", city="Austin")
    meta = write_client_legal_pages(tmp_path, info, market_code="US")
    assert meta["pack"] == "us_privacy"
    assert (tmp_path / "privacy.html").is_file()
    assert (tmp_path / "terms.html").is_file()
    assert not (tmp_path / "impressum.html").exists()
    assert not (tmp_path / "datenschutz.html").exists()


def test_fr_gets_legal_notice_not_de(tmp_path: Path):
    info = ClientLegalInfo(business_name="Boutique Paris", email="a@b.fr")
    meta = write_client_legal_pages(tmp_path, info, market_code="FR")
    assert meta["pack"] == "placeholder"
    assert (tmp_path / "LEGAL_NOTICE.txt").is_file()
    assert not (tmp_path / "impressum.html").exists()
    text = (tmp_path / "LEGAL_NOTICE.txt").read_text(encoding="utf-8")
    assert "FR" in text or "not yet" in text.lower() or "not included" in text.lower()


def test_factory_us_build_writes_en_legal(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Dental clinic in Austin TX. Cleanings and implants.",
        market_code="US",
        client_legal={
            "owner_name": "Dr. Jane Smith",
            "street": "100 Main St",
            "zip": "78701",
            "city": "Austin",
            "email": "hello@austin-dental.com",
            "phone": "+1 512 555 0100",
            "country": "US",
        },
        contacts={"market_code": "US", "business_name": "Austin Dental"},
    )
    product_dir = tmp_path / "sandbox" / product["product_id"]
    assert (product_dir / "privacy.html").is_file()
    assert (product_dir / "terms.html").is_file()
    assert not (product_dir / "impressum.html").exists()
    import json

    meta = json.loads((product_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta.get("market_code") == "US"


def test_public_status_us_currency_and_english(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")

    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    intent = FactoryIntentService(memory_dir=tmp_path, factory=factory)
    sales = SalesOrderService(tmp_path, intent)
    revenue = RevenuePipelineService(
        sales,
        FinanceService(tmp_path),
        PaymentCheckoutService(tmp_path),
        OwnerNotificationService(tmp_path),
    )

    created = sales.create_order(
        {
            "business_name": "Austin Dental",
            "description": "Dental clinic Austin TX",
            "email": "a@acme.com",
            "package_id": "basic",
            "city": "Austin",
            "market_code": "US",
            "currency": "USD",
            "symbol": "$",
            "price_label": "$450",
            "client_legal": {
                "owner_name": "Dr. Test",
                "street": "100 Main",
                "zip": "78701",
                "city": "Austin",
                "email": "a@acme.com",
                "country": "US",
            },
        }
    )
    order_id = created["order_id"]
    status = sales.public_status(order_id)
    assert status["market_code"] == "US"
    assert status["ui_lang"] == "en"
    assert status["currency"] == "USD"
    assert "$" in status["price_label"] or status["price_label"].startswith("$")
    assert status["status_label"] == "Awaiting payment"
    assert "Waiting" in status["current_step"] or "payment" in status["current_step"].lower()

    revenue.begin_checkout(
        order_id,
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
    )
    revenue.complete_sandbox_payment(order_id)

    paid = sales.public_status(order_id)
    assert paid["paid"] is True
    assert paid["status_label"] in ("In production", "Paid", "Ready")
    assert paid["ui_lang"] == "en"

    data, _filename = sales.build_client_download(order_id)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
    assert "privacy.html" in names
    assert "terms.html" in names
    assert "impressum.html" not in names
    assert "datenschutz.html" not in names
    assert "README_PUBLISH.txt" in names
    readme = zipfile.ZipFile(io.BytesIO(data)).read("README_PUBLISH.txt").decode("utf-8")
    assert "Hetzner" not in readme
    assert "Cloudflare" in readme or "Publish" in readme
