"""Commercial Platform 6.5 — Licenses (entitlement independent of Purchase)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.license_facade import LicenseFacade
from app.portal.license_store import InMemoryLicenseStore
from app.portal.portal_license_registration import register_portal_licenses
from app.portal.portal_license_router import (
    ENGINE_ID,
    clear_license_facade,
    portal_license_router,
)
from app.portal.portal_my_products_registration import register_portal_my_products
from app.portal.portal_my_products_router import clear_product_ownership_facade
from app.portal.portal_product_activation_registration import (
    register_portal_product_activation,
)
from app.portal.portal_product_activation_router import clear_product_activation_facade
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_activation_store import InMemoryProductActivationStore
from app.portal.product_catalog_store import InMemoryProductCatalogStore
from app.portal.product_ownership_store import InMemoryProductOwnershipStore


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
    return catalog, ownerships, activations, activation, licenses


def test_engine_id():
    assert ENGINE_ID == "portal_license_router_v1"


def test_enterprise_license_without_purchase():
    catalog, ownerships, _, _, licenses = _stack()
    granted = licenses.grant(
        account_id="acc-1",
        catalog_product_id="prod_chatbot",
        source="enterprise",
    )
    assert granted.source == "enterprise"
    assert granted.status == "active"

    validation = licenses.validate(
        account_id="acc-1", license_id=granted.license_id
    )
    assert validation.valid is True

    activated = licenses.redeem(
        account_id="acc-1", license_id=granted.license_id
    )
    assert activated.source == "native"
    assert ownerships.list_for_account("acc-1")[0].product_type == "chatbot"
    assert licenses.list_licenses(account_id="acc-1")[0].status == "used"


def test_http_list_and_validate():
    clear_license_facade()
    clear_product_activation_facade()
    clear_product_ownership_facade()

    account = new_account(email="a@b.c", display_name="A", status="ready")
    catalog, ownerships, activations, activation, _ = _stack()
    license_store = InMemoryLicenseStore()
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
    licenses = register_portal_licenses(
        app,
        activation=activation,
        catalog=catalog,
        license_store=license_store,
    )
    granted = licenses.grant(
        account_id=account.account_id,
        catalog_product_id="prod_analytics",
        source="promo",
    )

    http = TestClient(app)
    try:
        listed = http.get("/portal/licenses")
        assert listed.status_code == 200
        assert len(listed.json()) == 1
        assert listed.json()[0]["source"] == "promo"

        validated = http.post(f"/portal/licenses/{granted.license_id}/validate")
        assert validated.status_code == 200
        assert validated.json()["valid"] is True
    finally:
        clear_license_facade()
        clear_product_activation_facade()
        clear_product_ownership_facade()


def test_anonymous_401():
    clear_license_facade()
    catalog, _, _, activation, _ = _stack()
    app = FastAPI()
    register_portal_licenses(app, activation=activation, catalog=catalog)
    try:
        assert TestClient(app).get("/portal/licenses").status_code == 401
    finally:
        clear_license_facade()


def test_license_never_writes_ownership_store_directly():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "license_service.py",
        "license_facade.py",
        "portal_license_router.py",
    ):
        text = (portal / name).read_text(encoding="utf-8")
        assert "from app.portal.product_ownership_store" not in text
        assert "ownerships.save" not in text
    service = (portal / "license_service.py").read_text(encoding="utf-8")
    assert "activate_from_purchase" in service


def test_router_get_and_validate():
    paths: dict[str, set[str]] = {}
    for route in portal_license_router.routes:
        path = getattr(route, "path", "")
        methods = set(getattr(route, "methods", set()) or set())
        if path.endswith("/licenses") or "/licenses/{license_id}/validate" in path:
            paths[path] = paths.get(path, set()) | methods
    assert any(p.endswith("/licenses") for p in paths)
    assert any("/licenses/{license_id}/validate" in p for p in paths)


def test_main_registers_licenses_before_purchases():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert text.index("register_portal_licenses(") < text.index(
        "register_portal_purchases("
    )
