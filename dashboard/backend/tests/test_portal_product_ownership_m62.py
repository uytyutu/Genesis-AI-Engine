"""Mission 6.2 — Product Ownership (bridge from WebsiteOwnership)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.client import new_client, website_for_client
from app.portal.ownership import WebsiteOwnership, grant_website_ownership
from app.portal.ownership_directory import InMemoryOwnershipDirectory
from app.portal.portal_my_products_registration import register_portal_my_products
from app.portal.portal_my_products_router import (
    ENGINE_ID,
    clear_product_ownership_facade,
    portal_my_products_router,
)
from app.portal.product_catalog_store import InMemoryProductCatalogStore
from app.portal.product_ownership import new_product_ownership
from app.portal.product_ownership_facade import ProductOwnershipFacade
from app.portal.product_ownership_store import InMemoryProductOwnershipStore
from app.portal.website_ownership_bridge import (
    WebsiteOwnershipBridge,
    website_product_id,
)


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
    assert ENGINE_ID == "portal_my_products_router_v1"


def test_bridge_projects_website_ownership_without_mutating():
    account, website_id, ownerships = _account_with_website()
    before = ownerships.all_ownerships()
    bridge = WebsiteOwnershipBridge(ownerships)
    bridged = bridge.list_for_account(account.account_id)
    assert len(bridged) == 1
    row = bridged[0]
    assert row.product_type == "website"
    assert row.product_id == website_product_id(website_id)
    assert row.source == "website_bridge"
    assert row.status == "active"
    assert ownerships.all_ownerships() == before
    assert isinstance(before[0], WebsiteOwnership)


def test_facade_merges_bridge_and_native_with_catalog_names():
    account, website_id, ownerships = _account_with_website()
    store = InMemoryProductOwnershipStore()
    store.save(
        new_product_ownership(
            account_id=account.account_id,
            product_id="prod_chatbot_demo",
            product_type="chatbot",
            status="active",
            source="native",
        )
    )
    facade = ProductOwnershipFacade.from_parts(
        store,
        WebsiteOwnershipBridge(ownerships),
        InMemoryProductCatalogStore(),
    )
    items = facade.list_my_products(account.account_id)
    by_type = {item.product_type: item for item in items}
    assert by_type["website"].source == "website_bridge"
    assert by_type["website"].display_name == "Website"
    assert by_type["website"].product_id == website_product_id(website_id)
    assert by_type["chatbot"].source == "native"
    assert by_type["chatbot"].display_name == "ChatBot"


def test_anonymous_401():
    clear_product_ownership_facade()
    app = FastAPI()
    register_portal_my_products(app)
    try:
        assert TestClient(app).get("/portal/my-products").status_code == 401
    finally:
        clear_product_ownership_facade()


def test_authenticated_my_products_via_bridge():
    clear_product_ownership_facade()
    account, website_id, ownerships = _account_with_website()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_my_products(app, website_ownerships=ownerships)
    try:
        r = TestClient(app).get("/portal/my-products")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["product_type"] == "website"
        assert body[0]["status"] == "active"
        assert body[0]["source"] == "website_bridge"
        assert body[0]["product_id"] == website_product_id(website_id)
        assert body[0]["display_name"] == "Website"
    finally:
        clear_product_ownership_facade()


def test_router_get_only_platform_level():
    methods: set[str] = set()
    matched = False
    for route in portal_my_products_router.routes:
        path = getattr(route, "path", "")
        if path.endswith("/my-products"):
            matched = True
            methods |= set(getattr(route, "methods", set()) or set())
            assert "{website_id}" not in path
    assert matched
    assert methods == {"GET"}

    router_src = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "portal"
        / "portal_my_products_router.py"
    ).read_text(encoding="utf-8")
    assert "from app.portal.authorization_facade" not in router_src
    assert "check_website_access" not in router_src


def test_main_registers_my_products():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_my_products(" in text
    assert "include_router(portal_my_products_router)" not in text


def test_website_ownership_unchanged_and_modules_intact():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    ownership_src = (portal / "ownership.py").read_text(encoding="utf-8")
    assert "class WebsiteOwnership" in ownership_src
    assert "ProductOwnership" not in ownership_src
    assert "migrate" not in ownership_src.lower()

    for name in (
        "website_settings.py",
        "analytics.py",
        "chatbot.py",
        "product.py",
        "authorization_facade.py",
    ):
        assert (portal / name).is_file(), name

    main = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(
        encoding="utf-8"
    )
    assert "register_portal_website_settings(app)" in main
    assert "register_portal_product_catalog(" in main


def test_bridge_not_a_data_migration():
    bridge_src = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "portal"
        / "website_ownership_bridge.py"
    ).read_text(encoding="utf-8")
    assert "WebsiteOwnershipBridge" in bridge_src
    assert "grant_website_ownership" not in bridge_src
    assert "def save" not in bridge_src
    assert "_rows[" not in bridge_src
