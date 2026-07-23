"""Mission 6.3 — Product Activation (native ProductOwnership, no payments)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.client import new_client, website_for_client
from app.portal.ownership import grant_website_ownership
from app.portal.ownership_directory import InMemoryOwnershipDirectory
from app.portal.portal_my_products_registration import register_portal_my_products
from app.portal.portal_my_products_router import clear_product_ownership_facade
from app.portal.portal_product_activation_registration import (
    register_portal_product_activation,
)
from app.portal.portal_product_activation_router import (
    ENGINE_ID,
    clear_product_activation_facade,
    portal_product_activation_router,
)
from app.portal.product_activation import (
    ProductActivationError,
    new_activation_request,
)
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_activation_service import ProductActivationService
from app.portal.product_activation_store import InMemoryProductActivationStore
from app.portal.product_catalog_store import InMemoryProductCatalogStore
from app.portal.product_ownership_store import InMemoryProductOwnershipStore
from app.portal.website_ownership_bridge import WebsiteOwnershipBridge


def _account_with_website():
    client = new_client(display_name="EL3", primary_email="owner@example.com")
    site = website_for_client(client, product_id="p1", market_code="DE")
    account = new_account(
        email="owner@example.com", display_name="Owner", status="ready"
    )
    ownerships = InMemoryOwnershipDirectory(
        ownerships=[grant_website_ownership(account, site)]
    )
    return account, site.website_id, ownerships


def test_engine_id():
    assert ENGINE_ID == "portal_product_activation_router_v1"


def test_service_creates_native_ownership():
    catalog = InMemoryProductCatalogStore()
    ownerships = InMemoryProductOwnershipStore()
    activations = InMemoryProductActivationStore()
    service = ProductActivationService(
        catalog=catalog, ownerships=ownerships, activations=activations
    )
    row = service.activate(
        new_activation_request(
            account_id="acc-1",
            catalog_product_id="prod_chatbot",
            activation_code="DEMO-CHATBOT",
        )
    )
    assert row.source == "native"
    assert row.product_type == "chatbot"
    assert row.status == "active"
    assert row.product_id.startswith("native_chatbot_")
    assert ownerships.list_for_account("acc-1") == (row,)

    again = service.activate(
        new_activation_request(
            account_id="acc-1",
            catalog_product_id="prod_chatbot",
            activation_code="DEMO-CHATBOT",
        )
    )
    assert again.ownership_id == row.ownership_id


def test_service_rejects_coming_soon_and_bad_code():
    service = ProductActivationService(
        catalog=InMemoryProductCatalogStore(),
        ownerships=InMemoryProductOwnershipStore(),
        activations=InMemoryProductActivationStore(),
    )
    try:
        service.activate(
            new_activation_request(
                account_id="a",
                catalog_product_id="prod_crm",
                activation_code="DEMO-CRM",
            )
        )
        assert False, "expected ProductActivationError"
    except ProductActivationError as exc:
        assert str(exc) == "product_not_activatable"

    try:
        service.activate(
            new_activation_request(
                account_id="a",
                catalog_product_id="prod_chatbot",
                activation_code="WRONG",
            )
        )
        assert False, "expected ProductActivationError"
    except ProductActivationError as exc:
        assert str(exc) == "activation_code_invalid"


def test_http_activate_and_my_products_merge_bridge_plus_native():
    clear_product_activation_facade()
    clear_product_ownership_facade()
    account, _, website_ownerships = _account_with_website()
    shared = InMemoryProductOwnershipStore()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_my_products(
        app, website_ownerships=website_ownerships, ownership_store=shared
    )
    register_portal_product_activation(app, ownership_store=shared)
    http = TestClient(app)
    try:
        before = http.get("/portal/my-products")
        assert before.status_code == 200
        assert len(before.json()) == 1
        assert before.json()[0]["source"] == "website_bridge"

        activated = http.post(
            "/portal/products/prod_chatbot/activate",
            json={"activation_code": "DEMO-CHATBOT"},
        )
        assert activated.status_code == 200
        body = activated.json()
        assert body["product_type"] == "chatbot"
        assert body["source"] == "native"
        assert body["status"] == "active"
        assert body["display_name"] == "AI Business Employee (Vector)"

        after = http.get("/portal/my-products")
        assert after.status_code == 200
        sources = {row["source"] for row in after.json()}
        types = {row["product_type"] for row in after.json()}
        assert sources == {"website_bridge", "native"}
        assert "website" in types
        assert "chatbot" in types
    finally:
        clear_product_activation_facade()
        clear_product_ownership_facade()


def test_anonymous_activate_401():
    clear_product_activation_facade()
    app = FastAPI()
    register_portal_product_activation(app)
    try:
        assert (
            TestClient(app)
            .post(
                "/portal/products/prod_chatbot/activate",
                json={"activation_code": "DEMO-CHATBOT"},
            )
            .status_code
            == 401
        )
    finally:
        clear_product_activation_facade()


def test_bridge_file_untouched_by_activation_imports():
    bridge = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "portal"
        / "website_ownership_bridge.py"
    ).read_text(encoding="utf-8")
    assert "WebsiteOwnershipBridge" in bridge
    assert "grant_website_ownership" not in bridge
    assert "ProductActivation" not in bridge
    assert "product_activation" not in bridge


def test_router_post_only_activate():
    methods: set[str] = set()
    matched = False
    for route in portal_product_activation_router.routes:
        path = getattr(route, "path", "")
        if "/products/{product_id}/activate" in path:
            matched = True
            methods |= set(getattr(route, "methods", set()) or set())
    assert matched
    assert methods == {"POST"}


def test_main_shares_ownership_store_and_registers_activation():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_product_activation(" in text
    assert "_portal_product_ownership_store" in text
    assert "ownership_store=_portal_product_ownership_store" in text
    assert "include_router(portal_product_activation_router)" not in text


def test_no_payment_dependency():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "product_activation.py",
        "product_activation_service.py",
        "product_activation_facade.py",
        "portal_product_activation_router.py",
    ):
        text = (portal / name).read_text(encoding="utf-8")
        assert "stripe" not in text.lower()
        assert "paddle" not in text.lower()
        assert "from app.portal.authorization_facade" not in text
