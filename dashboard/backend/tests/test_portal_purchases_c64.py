"""Commercial Platform 6.4 — Purchases (commerce → License → Activation)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.billing_facade import BillingFacade
from app.portal.billing_store import InMemoryBillingStore
from app.portal.license_facade import LicenseFacade
from app.portal.license_store import InMemoryLicenseStore
from app.portal.portal_billing_registration import register_portal_billing
from app.portal.portal_billing_router import clear_billing_facade
from app.portal.portal_my_products_registration import register_portal_my_products
from app.portal.portal_my_products_router import clear_product_ownership_facade
from app.portal.portal_product_activation_registration import (
    register_portal_product_activation,
)
from app.portal.portal_product_activation_router import clear_product_activation_facade
from app.portal.portal_purchase_registration import register_portal_purchases
from app.portal.portal_purchase_router import (
    ENGINE_ID,
    clear_purchase_facade,
    portal_purchase_router,
)
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_activation_store import InMemoryProductActivationStore
from app.portal.product_catalog_store import InMemoryProductCatalogStore
from app.portal.product_ownership_store import InMemoryProductOwnershipStore
from app.portal.purchase_facade import PurchaseFacade
from app.portal.purchase_store import InMemoryPurchaseStore


def _stack():
    catalog = InMemoryProductCatalogStore()
    ownerships = InMemoryProductOwnershipStore()
    activations = InMemoryProductActivationStore()
    activation = ProductActivationFacade.from_parts(
        catalog=catalog, ownerships=ownerships, activations=activations
    )
    licenses = LicenseFacade.from_parts(
        catalog=catalog,
        licenses=InMemoryLicenseStore(),
        activation=activation,
    )
    billing = BillingFacade.from_store(InMemoryBillingStore())
    return catalog, ownerships, activations, activation, licenses, billing


def test_engine_id():
    assert ENGINE_ID == "portal_purchase_router_v1"


def test_purchase_grants_license_then_activates():
    catalog, ownerships, _, activation, licenses, billing = _stack()
    facade = PurchaseFacade.from_parts(
        catalog=catalog,
        purchases=InMemoryPurchaseStore(),
        licenses=licenses,
        billing=billing,
    )
    view = facade.purchase(account_id="acc-1", catalog_product_id="prod_chatbot")
    assert view.status == "paid"
    assert view.activated_product is not None
    assert view.activated_product.source == "native"
    assert ownerships.list_for_account("acc-1")[0].source == "native"
    listed = licenses.list_licenses(account_id="acc-1")
    assert len(listed) == 1
    assert listed[0].source == "purchase"
    assert listed[0].status == "used"


def test_http_purchase_then_my_products():
    clear_purchase_facade()
    clear_billing_facade()
    clear_product_activation_facade()
    clear_product_ownership_facade()

    account = new_account(email="a@b.c", display_name="A", status="ready")
    catalog, ownerships, activations, activation, licenses, _ = _stack()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_my_products(
        app, ownership_store=ownerships, catalog=catalog
    )
    register_portal_product_activation(
        app,
        ownership_store=ownerships,
        catalog=catalog,
        activation_store=activations,
        facade=activation,
    )
    billing = register_portal_billing(app)
    register_portal_purchases(
        app, licenses=licenses, billing=billing, catalog=catalog
    )

    http = TestClient(app)
    try:
        bought = http.post("/portal/products/prod_analytics/purchase")
        assert bought.status_code == 200
        assert bought.json()["activated_product"]["source"] == "native"

        mine = http.get("/portal/my-products")
        assert any(
            row["product_type"] == "analytics" and row["source"] == "native"
            for row in mine.json()
        )
    finally:
        clear_purchase_facade()
        clear_billing_facade()
        clear_product_activation_facade()
        clear_product_ownership_facade()


def test_anonymous_401():
    clear_purchase_facade()
    clear_billing_facade()
    catalog, _, _, activation, licenses, billing = _stack()
    app = FastAPI()
    register_portal_purchases(
        app, licenses=licenses, billing=billing, catalog=catalog
    )
    try:
        assert (
            TestClient(app)
            .post("/portal/products/prod_chatbot/purchase")
            .status_code
            == 401
        )
    finally:
        clear_purchase_facade()
        clear_billing_facade()


def test_coming_soon_not_purchasable():
    clear_purchase_facade()
    clear_billing_facade()
    account = new_account(email="a@b.c", display_name="A", status="ready")
    catalog, _, _, _, licenses, billing = _stack()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_purchases(
        app, licenses=licenses, billing=billing, catalog=catalog
    )
    try:
        r = TestClient(app).post("/portal/products/prod_crm/purchase")
        assert r.status_code == 400
        assert r.json()["detail"] == "product_not_purchasable"
    finally:
        clear_purchase_facade()
        clear_billing_facade()


def test_commercial_boundary_no_direct_ownership_writes():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "purchase_service.py",
        "purchase_facade.py",
        "portal_purchase_router.py",
    ):
        text = (portal / name).read_text(encoding="utf-8")
        assert "from app.portal.product_ownership_store" not in text
        assert "ownerships.save" not in text
        assert "stripe" not in text.lower()
    service = (portal / "purchase_service.py").read_text(encoding="utf-8")
    assert "licenses.grant" in service or "_licenses.grant" in service
    assert "redeem" in service


def test_router_post_only():
    methods: set[str] = set()
    matched = False
    for route in portal_purchase_router.routes:
        path = getattr(route, "path", "")
        if "/products/{product_id}/purchase" in path:
            matched = True
            methods |= set(getattr(route, "methods", set()) or set())
    assert matched
    assert methods == {"POST"}


def test_main_wires_purchases_through_licenses():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_purchases(" in text
    assert "licenses=_portal_license_facade" in text
    assert "billing=_portal_billing_facade" in text
    assert "register_portal_licenses(" in text
    assert "register_portal_billing(" in text
