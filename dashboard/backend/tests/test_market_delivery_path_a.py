"""Market-aware Path A: status copy + Factory legal packs."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

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


def test_delivery_maturity_matrix_levels():
    from app.factory.market_delivery import list_path_a_delivery_matrix, market_delivery_support

    de = market_delivery_support("DE")
    us = market_delivery_support("US")
    fr = market_delivery_support("FR")
    pl = market_delivery_support("PL")
    ua = market_delivery_support("UA")
    ru = market_delivery_support("RU")
    gb = market_delivery_support("GB")
    at = market_delivery_support("AT")

    assert de["level"] == 1 and de["status"] == "production" and de["legal_ready"] is True
    assert us["level"] == 1 and us["status"] == "production"
    assert gb["level"] == 1 and at["level"] == 1
    assert fr["level"] == 2 and fr["status"] == "beta" and fr["ui_lang"] == "en"
    assert pl["level"] == 2 and pl["legal_label"] == "Placeholder"
    assert ua["level"] == 3 and ua["ui_lang"] == "uk"
    assert ru["level"] == 3 and ru["ui_lang"] == "ru"

    matrix = list_path_a_delivery_matrix()
    codes = {row["market_code"] for row in matrix}
    assert {"DE", "US", "FR", "PL", "UA", "RU", "GB", "AT"} <= codes
    # No Production row without a real legal pack
    for row in matrix:
        if row["status"] == "production":
            assert row["legal_ready"] is True
        if row["legal_ready"] is False:
            assert row["status"] == "beta"


@pytest.mark.parametrize(
    "market,ui,currency,zip_has,zip_missing,readme_forbidden",
    [
        ("DE", "de", "EUR", ("impressum.html", "datenschutz.html"), ("privacy.html", "LEGAL_NOTICE.txt"), ()),
        ("AT", "de", "EUR", ("impressum.html", "datenschutz.html"), ("LEGAL_NOTICE.txt",), ()),
        ("US", "en", "USD", ("privacy.html", "terms.html"), ("impressum.html",), ("Hetzner",)),
        ("GB", "en", "GBP", ("privacy.html", "terms.html"), ("impressum.html",), ("Hetzner",)),
        ("FR", "en", "EUR", ("LEGAL_NOTICE.txt",), ("impressum.html", "datenschutz.html"), ("Hetzner",)),
        ("PL", "en", "PLN", ("LEGAL_NOTICE.txt",), ("impressum.html",), ("Hetzner",)),
        ("UA", "uk", "UAH", ("LEGAL_NOTICE.txt",), ("impressum.html",), ("Hetzner",)),
        ("RU", "ru", "EUR", ("LEGAL_NOTICE.txt",), ("impressum.html",), ("Hetzner",)),
    ],
)
def test_path_a_markets_status_and_zip(
    tmp_path: Path,
    monkeypatch,
    market,
    ui,
    currency,
    zip_has,
    zip_missing,
    readme_forbidden,
):
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
            "business_name": f"Biz {market}",
            "description": f"Landing for market {market}",
            "email": f"a@{market.lower()}.example",
            "package_id": "basic",
            "city": "City",
            "market_code": market,
            "client_legal": {
                "owner_name": "Owner",
                "street": "1 Main",
                "zip": "10000",
                "city": "City",
                "email": f"a@{market.lower()}.example",
                "country": market,
            },
        }
    )
    order_id = created["order_id"]
    status = sales.public_status(order_id)
    assert status["market_code"] == market
    assert status["ui_lang"] == ui
    assert status["currency"] == currency
    assert status["status_label"] == client_status_label("awaiting_payment", market)

    revenue.begin_checkout(
        order_id,
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
    )
    revenue.complete_sandbox_payment(order_id)
    data, _ = sales.build_client_download(order_id)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
        readme = zf.read("README_PUBLISH.txt").decode("utf-8")
    for name in zip_has:
        assert name in names, f"{market}: missing {name}"
    for name in zip_missing:
        assert name not in names, f"{market}: unexpected {name}"
    for bad in readme_forbidden:
        assert bad not in readme, f"{market}: README must not mention {bad}"



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
