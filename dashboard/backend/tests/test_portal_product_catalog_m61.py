"""Mission 6.1 — Product Catalog (platform-level, independent of Website)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.portal_product_catalog_registration import (
    register_portal_product_catalog,
)
from app.portal.portal_product_catalog_router import (
    ENGINE_ID,
    clear_product_catalog_facade,
    portal_product_catalog_router,
)
from app.portal.product import Product, default_product_catalog
from app.portal.product_catalog_facade import ProductCatalogFacade
from app.portal.product_catalog_store import InMemoryProductCatalogStore


def test_engine_id():
    assert ENGINE_ID == "portal_product_catalog_router_v1"


def test_product_independent_of_website():
    products = default_product_catalog()
    assert len(products) >= 3
    types = {p.product_type for p in products}
    assert "website" in types
    assert "chatbot" in types
    assert "crm" in types
    for product in products:
        assert isinstance(product, Product)
        assert product.product_id
        assert "website_id" not in product.as_dict()


def test_facade_lists_catalog():
    facade = ProductCatalogFacade.from_store(InMemoryProductCatalogStore())
    items = facade.list_products()
    assert any(i.product_type == "website" and i.display_name == "Website" for i in items)
    assert any(i.product_type == "chatbot" for i in items)
    assert any(i.product_type == "crm" for i in items)


def test_anonymous_401():
    clear_product_catalog_facade()
    app = FastAPI()
    register_portal_product_catalog(app)
    try:
        assert TestClient(app).get("/portal/products").status_code == 401
    finally:
        clear_product_catalog_facade()


def test_authenticated_get_products():
    clear_product_catalog_facade()
    account = new_account(email="a@b.c", display_name="A", status="ready")
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_product_catalog(app)
    try:
        r = TestClient(app).get("/portal/products")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        assert len(body) >= 3
        by_type = {row["product_type"]: row for row in body}
        assert by_type["website"]["display_name"] == "Website"
        assert by_type["chatbot"]["display_name"] == "ChatBot"
        assert by_type["crm"]["display_name"] == "CRM"
        for row in body:
            assert "product_id" in row
            assert "availability" in row
            assert "website_id" not in row
    finally:
        clear_product_catalog_facade()


def test_router_get_only_no_website_authz():
    methods: set[str] = set()
    matched = False
    for route in portal_product_catalog_router.routes:
        path = getattr(route, "path", "")
        if path.endswith("/products") and "{website_id}" not in path:
            matched = True
            methods |= set(getattr(route, "methods", set()) or set())
    assert matched
    assert methods == {"GET"}

    router_src = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "portal"
        / "portal_product_catalog_router.py"
    ).read_text(encoding="utf-8")
    assert "from app.portal.authorization_facade" not in router_src
    assert "from app.portal.ownership" not in router_src
    assert "check_website_access" not in router_src


def test_main_registers_product_catalog():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_product_catalog(app)" in text
    assert "include_router(portal_product_catalog_router)" not in text


def test_backward_compatibility_website_modules_untouched():
    """Existing Website modules and ownership must still be present."""
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "website_settings.py",
        "analytics.py",
        "website_domain.py",
        "chatbot.py",
        "ownership.py",
        "authorization_facade.py",
    ):
        assert (portal / name).is_file(), name

    ownership = (portal / "ownership.py").read_text(encoding="utf-8")
    assert "class WebsiteOwnership" in ownership
    assert "ProductOwnership" not in ownership

    main = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(
        encoding="utf-8"
    )
    assert "register_portal_website_settings(app)" in main
    assert "register_portal_analytics(app)" in main
    assert "register_portal_website_domain(app)" in main
    assert "register_portal_chatbot(app)" in main


def test_extensibility_contract_fields():
    """Ownership / Billing can arrive later without changing catalog field names."""
    view = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "portal"
        / "product_catalog_view.py"
    ).read_text(encoding="utf-8")
    for field in (
        "product_id",
        "product_type",
        "display_name",
        "description",
        "availability",
    ):
        assert field in view

    domain = (
        Path(__file__).resolve().parents[1] / "app" / "portal" / "product.py"
    ).read_text(encoding="utf-8")
    assert "from app.portal.website import" not in domain
    assert "from app.portal.ownership import" not in domain
    assert "def purchase" not in domain
    assert "license_key" not in domain.lower()
