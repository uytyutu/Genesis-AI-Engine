"""Commercial Platform 6.6 — Billing (financial ledger only)."""

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
from app.portal.portal_billing_router import (
    ENGINE_ID,
    clear_billing_facade,
    portal_billing_router,
)
from app.portal.portal_my_products_registration import register_portal_my_products
from app.portal.portal_my_products_router import clear_product_ownership_facade
from app.portal.portal_product_activation_registration import (
    register_portal_product_activation,
)
from app.portal.portal_product_activation_router import clear_product_activation_facade
from app.portal.portal_purchase_registration import register_portal_purchases
from app.portal.portal_purchase_router import clear_purchase_facade
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_activation_store import InMemoryProductActivationStore
from app.portal.product_catalog_store import InMemoryProductCatalogStore
from app.portal.product_ownership_store import InMemoryProductOwnershipStore
from app.portal.purchase_facade import PurchaseFacade
from app.portal.purchase_store import InMemoryPurchaseStore


def _commerce_stack():
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
    billing_store = InMemoryBillingStore()
    billing = BillingFacade.from_store(billing_store)
    return catalog, ownerships, activations, activation, licenses, billing, billing_store


def test_engine_id():
    assert ENGINE_ID == "portal_billing_router_v1"


def test_purchase_writes_paid_ledger_row():
    catalog, ownerships, _, _, licenses, billing, billing_store = _commerce_stack()
    facade = PurchaseFacade.from_parts(
        catalog=catalog,
        purchases=InMemoryPurchaseStore(),
        licenses=licenses,
        billing=billing,
    )
    facade.purchase(account_id="acc-1", catalog_product_id="prod_chatbot")
    rows = billing_store.list_for_account("acc-1")
    assert len(rows) == 1
    assert rows[0].status == "paid"
    assert rows[0].product_id == "prod_chatbot"
    assert rows[0].amount == 2900
    assert rows[0].currency == "EUR"
    assert rows[0].provider == "stub"
    assert ownerships.list_for_account("acc-1")  # ownership via license path


def test_http_list_and_get_after_purchase():
    clear_billing_facade()
    clear_purchase_facade()
    clear_product_activation_facade()
    clear_product_ownership_facade()

    account = new_account(email="a@b.c", display_name="A", status="ready")
    catalog, ownerships, activations, activation, licenses, _, billing_store = (
        _commerce_stack()
    )
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
    billing = register_portal_billing(app, store=billing_store)
    register_portal_purchases(
        app, licenses=licenses, billing=billing, catalog=catalog
    )

    http = TestClient(app)
    try:
        # prod_analytics is coming_soon (not purchasable); happy path uses available catalog id
        bought = http.post("/portal/products/prod_chatbot/purchase")
        assert bought.status_code == 200

        listed = http.get("/portal/billing")
        assert listed.status_code == 200
        assert len(listed.json()) == 1
        row = listed.json()[0]
        assert row["status"] == "paid"
        assert row["product_id"] == "prod_chatbot"
        assert row["amount"] == 2900
        assert set(row.keys()) >= {
            "transaction_id",
            "account_id",
            "product_id",
            "amount",
            "currency",
            "status",
            "provider",
            "created_at",
        }

        got = http.get(f"/portal/billing/{row['transaction_id']}")
        assert got.status_code == 200
        assert got.json()["transaction_id"] == row["transaction_id"]
    finally:
        clear_billing_facade()
        clear_purchase_facade()
        clear_product_activation_facade()
        clear_product_ownership_facade()


def test_anonymous_401():
    clear_billing_facade()
    app = FastAPI()
    register_portal_billing(app)
    try:
        assert TestClient(app).get("/portal/billing").status_code == 401
    finally:
        clear_billing_facade()


def test_billing_never_touches_license_activation_ownership():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "billing.py",
        "billing_service.py",
        "billing_facade.py",
        "portal_billing_router.py",
    ):
        text = (portal / name).read_text(encoding="utf-8")
        assert "from app.portal.product_ownership_store" not in text
        assert "from app.portal.license" not in text
        assert "from app.portal.product_activation" not in text
        assert "ownerships.save" not in text
        assert "stripe" not in text.lower()
        assert "paddle" not in text.lower()


def test_billing_boundary_strict_no_grant_activate():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "billing_service.py",
        "billing_facade.py",
        "portal_billing_router.py",
    ):
        text = (portal / name).read_text(encoding="utf-8").lower()
        assert "licensefacade" not in text
        assert "productactivationfacade" not in text
        assert "productownershipstore" not in text
        assert "licenses.grant" not in text
        assert "activate_from_purchase" not in text
        assert ".redeem(" not in text


def test_router_get_only():
    paths: dict[str, set[str]] = {}
    for route in portal_billing_router.routes:
        path = getattr(route, "path", "")
        methods = set(getattr(route, "methods", set()) or set())
        if path.endswith("/billing") or "/billing/{transaction_id}" in path:
            paths[path] = paths.get(path, set()) | methods
    assert any(p.endswith("/billing") for p in paths)
    assert any("/billing/{transaction_id}" in p for p in paths)
    for methods in paths.values():
        assert methods == {"GET"}


def test_main_wires_billing_before_purchases():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_billing(" in text
    assert text.index("register_portal_billing(") < text.index(
        "register_portal_purchases("
    )
    assert "billing=_portal_billing_facade" in text
