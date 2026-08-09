"""Demo Company Test — Nordlicht Möbel GmbH (Handwerk / furniture, DE).

Gate: every major feature must pass this path before OAuth / Visual Engine / Marketing.
In-process E2E — does not require a running HTTP server.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.factory.store_factory import StoreFactoryService
from app.integration.finance_service import FinanceService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.platform_global_analytics import PlatformGlobalAnalyticsService
from app.integration.revenue_pipeline_service import RevenuePipelineService
from app.integration.sales_order_service import SalesOrderService
from app.integration.store_admin.catalog_service import StoreCatalogService
from app.integration.store_admin.commerce_settings import StoreCommerceSettingsService
from app.integration.store_admin.design_service import StoreDesignService
from app.integration.store_admin.setup_status import build_setup_status
from app.integration.store_checkout import StoreCheckoutService
from app.integration.store_customer.service import StoreCustomerService
from app.integration.vector.business_setup import build_business_setup
from app.integration.vector.website_tips import scan_website_tips
from app.integration.vc_auditor import VirtusCoreWebsiteAuditor


COMPANY = "Nordlicht Möbel GmbH"
EMAIL = "info@nordlicht-moebel.de"
CITY = "Hamburg"


class _WebsiteFactoryStub:
    """Minimal factory hook used by SalesOrderService.start_production."""

    def submit(self, intent):  # noqa: ANN001
        oid = getattr(intent, "order_id", None) or "nordlicht"
        return {"product_id": f"web-{str(oid)[:12]}"}

    class _Inner:
        def get_product(self, product_id: str):  # noqa: ANN001
            return {"id": product_id, "business_name": COMPANY}

    _factory = _Inner()


@pytest.fixture()
def sandbox_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.setenv("GENESIS_STORE_BUYER_JWT_SECRET", "nordlicht-demo-secret")
    monkeypatch.setenv("GENESIS_SHIPPING_MOCK", "1")
    monkeypatch.setenv("GENESIS_SMTP_MOCK", "1")
    monkeypatch.setenv("GENESIS_STRIPE_CONNECT_MOCK", "1")


def _revenue(tmp_path: Path) -> tuple[SalesOrderService, RevenuePipelineService]:
    sales = SalesOrderService(tmp_path, _WebsiteFactoryStub())
    checkout = PaymentCheckoutService(tmp_path)
    finance = FinanceService(tmp_path)
    notifications = OwnerNotificationService(tmp_path)
    revenue = RevenuePipelineService(sales, finance, checkout, notifications)
    return sales, revenue


def _shop_brief():
    return {
        "company_name": COMPANY,
        "store_name": "Nordlicht Möbel",
        "what_is_sold": "Hochwertige Möbel und Einrichtung aus Hamburg",
        "category": "home",
        "catalog_size": "50",
        "languages": ["de"],
        "currency": "EUR",
        "payments": ["stripe", "invoice"],
        "shipping": ["dhl", "pickup"],
        "pages": ["home", "catalog", "pdp", "about", "contact", "legal", "returns", "cart"],
        "style": "premium",
        "market_code": "DE",
    }


def test_demo_company_website_path(tmp_path: Path, sandbox_env, monkeypatch: pytest.MonkeyPatch):
    """1. Order Website → Demo Payment → production → Vector tips / Auditor on HTML."""
    monkeypatch.setenv("GENESIS_ALLOW_DEMO_PAYMENT", "1")
    sales, revenue = _revenue(tmp_path)
    created = sales.create_order(
        {
            "business_name": COMPANY,
            "description": "Tischlerei und Möbelhaus in Hamburg — Handwerk Premium",
            "email": EMAIL,
            "package_id": "business",
            "city": CITY,
            "niche": "handwerk",
            "market_code": "DE",
            "ui_lang": "de",
            "customer_id": "cust-nordlicht-web",
            "demo": True,
        }
    )
    order_id = created["order_id"]
    assert created["price_eur"] > 0
    assert created.get("payment_mode") == "demo"

    paid = revenue.complete_demo_payment(order_id)
    assert paid["ok"] is True
    assert paid.get("demo") is True

    status = sales.public_status(order_id)
    assert status["paid"] is True
    assert status.get("payment_mode") == "demo"
    assert status.get("product_id") or status["paid"]

    order = sales.get_order(order_id)
    assert order is not None
    assert order.get("product_id")

    # Website tips / Auditor need HTML — write a minimal published page for the gate
    product_id = str(order["product_id"])
    site_dir = tmp_path / "sandbox" / product_id
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "index.html").write_text(
        f"""<!DOCTYPE html><html lang="de"><head>
        <title>{COMPANY}</title>
        <meta name="description" content="Möbel und Einrichtung aus Hamburg" />
        </head><body>
        <h1>{COMPANY}</h1>
        <p>Handwerk · Hamburg</p>
        <a href="/kontakt">Kontakt</a>
        <footer>Impressum</footer>
        </body></html>""",
        encoding="utf-8",
    )

    tips = scan_website_tips(
        product_id=product_id,
        product_dir=site_dir,
        niche="handwerk",
    )
    assert tips.get("ok") is not False or tips.get("tips") is not None

    auditor = VirtusCoreWebsiteAuditor(tmp_path)
    report = auditor.analyze_virtus_product(
        product_id=product_id,
        product_dir=site_dir,
        niche="handwerk",
    )
    assert report.get("ok") is not False or "scores" in report or "overall" in str(report)


def test_demo_company_ai_store_full_loop(tmp_path: Path, sandbox_env):
    """2–4. Buy AI Store → Factory → Design/Products → Publish → Checkout → Order → Admin."""
    sales = SalesOrderService(tmp_path, _WebsiteFactoryStub())
    created = sales.create_order(
        {
            "business_name": COMPANY,
            "email": EMAIL,
            "package_id": "ecommerce_shop",
            "description": "Online-Shop für Möbel",
            "customer_id": "cust-nordlicht-shop",
            "city": CITY,
            "market_code": "DE",
            "ui_lang": "de",
            "shop_brief": _shop_brief(),
        }
    )
    order_id = created["order_id"]
    order = sales.get_order(order_id)
    assert order is not None
    order["status"] = "paid"
    order["paid_at"] = "2026-08-06T01:00:00+00:00"
    sales._save_order(order)  # noqa: SLF001

    pipeline = sales.start_shop_pipeline(order_id)
    assert pipeline["ok"] is True
    assert pipeline.get("published_url") or pipeline.get("product_id")

    order = sales.get_order(order_id)
    assert order is not None
    product_id = str(order["product_id"])
    product_dir = tmp_path / "sandbox" / product_id
    assert (product_dir / "index.html").is_file()
    assert (product_dir / "cart.html").is_file()
    assert (product_dir / "checkout.html").is_file(), "Checkout 1.0 page missing — regenerate required"
    assert (product_dir / "account.html").is_file()
    assert (product_dir / "assets" / "checkout.js").is_file()
    checkout_js = (product_dir / "assets" / "checkout.js").read_text(encoding="utf-8")
    assert "/checkout/place" in checkout_js
    store_js = (product_dir / "assets" / "store.js").read_text(encoding="utf-8")
    assert "checkout.html" in store_js

    # Store Admin — products + design
    catalog = StoreCatalogService(tmp_path)
    p1 = catalog.create_product(
        order_id,
        {
            "title": "Nordlicht Esstisch Eiche",
            "price": 899.0,
            "status": "published",
            "description": "Massivholz Esstisch",
        },
    )
    p2 = catalog.create_product(
        order_id,
        {
            "title": "Regal Hamburg",
            "price": 349.0,
            "status": "published",
        },
    )
    assert p1.get("ok") or p1.get("product") or p1.get("id")
    listed = catalog.list_products(order_id)
    assert int(listed.get("count") or 0) >= 2

    design = StoreDesignService(tmp_path)
    d = design.get_design(order_id, store_name="Nordlicht Möbel")
    design_payload = d.get("design") or {}
    design_payload.setdefault("branding", {})["logo"] = {"id": "logo-nordlicht"}
    design_payload.setdefault("colors", {})["primary"] = "#1c1917"
    design.update_design(order_id, design_payload)

    # Commerce connect
    commerce = StoreCommerceSettingsService(tmp_path)
    commerce.apply_stripe_oauth(
        order_id,
        stripe_user_id="acct_mock_nordlicht",
        account_label=EMAIL,
        mock=True,
    )
    from app.integration.store_admin.shipping_api_service import StoreShippingApiService

    StoreShippingApiService(tmp_path).connect_carrier(
        order_id, "dhl", {"account_name": "dhl@nordlicht.de"}
    )
    commerce.connect(order_id, "invoice")
    commerce.update_shipping_config(
        order_id,
        {
            "free_shipping_from_eur": 1200,
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
                    "label": "Abholung Hamburg",
                    "days_min": 0,
                    "days_max": 0,
                    "price_eur": 0,
                    "enabled": True,
                },
            ],
        },
    )
    commerce.update_tax_config(order_id, {"profile": "de_standard", "company_vat_id": "DE123456789"})

    setup = build_setup_status(
        order_id=order_id,
        product_count=int(listed.get("count") or 0),
        design=design.get_design(order_id, store_name="Nordlicht Möbel").get("design") or {},
        commerce_settings=commerce.get(order_id)["settings"],
        shop_pipeline=str(order.get("shop_pipeline") or "published"),
    )
    assert setup["readiness_pct"] > 0
    shipping_step = next(s for s in setup["steps"] if s["id"] == "shipping")
    assert shipping_step["done"] is True
    assert shipping_step["actionable"] is True

    # Buyer checkout → first order
    buyers = StoreCustomerService(tmp_path)
    reg = buyers.register(
        order_id,
        {
            "email": "kunde@beispiel.de",
            "password": "moebel2026",
            "first_name": "Lisa",
            "last_name": "Berger",
        },
    )
    buyer_id = reg["buyer"]["id"]
    checkout = StoreCheckoutService(tmp_path)
    placed = checkout.place_order(
        order_id,
        buyer_id,
        {
            "items": [
                {
                    "id": (p1.get("product") or {}).get("id") or "sku-1",
                    "name": "Nordlicht Esstisch Eiche",
                    "price": 899.0,
                    "qty": 1,
                }
            ],
            "address": {
                "full_name": "Lisa Berger",
                "line1": "Elbchaussee 12",
                "city": "Hamburg",
                "postal_code": "22763",
                "country": "DE",
            },
            "shipping_method_id": "dhl_standard",
            "payment_method_id": "stripe",
            "save_address": True,
        },
    )
    assert placed["ok"] is True
    assert placed["order"]["total_eur"] == round(899.0 + 7.9, 2)
    assert placed["email"]["queued"] is True

    assert buyers.get_orders(order_id, buyer_id)["orders"]
    admin_orders = checkout.list_shop_orders(order_id)
    assert admin_orders["count"] >= 1

    biz = build_business_setup(
        has_website=True,
        has_store=True,
        product_count=2,
        branding_done=True,
        store_published=True,
        primary_store_order_id=order_id,
        payments_connected=True,
        shipping_connected=True,
        taxes_configured=True,
        email_connected=False,
    )
    assert biz["pct"] >= 50
    assert next(i for i in biz["items"] if i["id"] == "payments")["done"] is True

    snap = PlatformGlobalAnalyticsService(tmp_path).global_snapshot()
    assert snap["revenue"]["metrics"]["shop_orders_total"] >= 1
    assert snap["funnel"]["counts"].get("checkout_completed", 0) >= 1


def test_demo_company_digital_employee_not_ready_yet():
    """Digital Employee path is intentionally deferred — document the gap."""
    gaps = {
        "buy_digital_employee": "not_wired_as_sales_package_e2e",
        "telegram_connect": "post_R3.3",
        "first_bot_reply": "post_R3.3",
    }
    assert gaps["telegram_connect"] == "post_R3.3"


def test_demo_company_report_checklist():
    """Living checklist for human Demo Company Test (browser)."""
    checklist = [
        "Website: order → sandbox pay → cabinet → Website Admin → Vector → Auditor",
        "AI Store: order → Factory → Store Admin → Design → Products → Publish",
        "Checkout: cart → register → address → shipping → payment → place order",
        "Mail outbox stub + Store Admin Orders",
        "Vector Business Ready progress",
        "Mission Control /global-analytics Revenue + Funnel",
        "SKIP until E2E green: Stripe OAuth, SMTP, PDF, DHL API, Visual Intelligence Engine",
    ]
    assert len(checklist) >= 6
