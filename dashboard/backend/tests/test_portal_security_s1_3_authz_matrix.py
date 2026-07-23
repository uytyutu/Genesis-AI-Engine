"""S1.3 — Authorization Matrix automated checks."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.billing_facade import BillingFacade
from app.portal.billing_store import InMemoryBillingStore
from app.portal.license_facade import LicenseFacade
from app.portal.license_store import InMemoryLicenseStore
from app.portal.portal_billing_registration import register_portal_billing
from app.portal.portal_billing_router import clear_billing_facade
from app.portal.portal_license_registration import register_portal_licenses
from app.portal.portal_license_router import clear_license_facade
from app.portal.portal_my_products_registration import register_portal_my_products
from app.portal.portal_my_products_router import clear_product_ownership_facade
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_activation_store import InMemoryProductActivationStore
from app.portal.product_catalog_store import InMemoryProductCatalogStore
from app.portal.product_ownership_store import InMemoryProductOwnershipStore
from app.portal.s1_3_authz_matrix import (
    AUTHZ_MATRIX,
    ENGINE_ID,
    client_admin_denied,
    guest_must_be_denied,
    matrix_cell,
    support_admin_denied,
)
from app.security import is_owner_api_path, is_public_api_path, production_api_allowed


def test_engine_and_matrix_shape():
    assert ENGINE_ID == "s1_3_authz_matrix_v1"
    assert set(AUTHZ_MATRIX) == {"guest", "client", "support", "owner"}
    for role in AUTHZ_MATRIX:
        assert set(AUTHZ_MATRIX[role]) == {
            "orders",
            "billing",
            "licenses",
            "support",
            "admin",
        }
    assert guest_must_be_denied("billing")
    assert guest_must_be_denied("orders")
    assert client_admin_denied()
    assert support_admin_denied()
    assert matrix_cell("owner", "admin") == "allow"
    assert matrix_cell("support", "orders") == "read_limited"


def test_guest_denied_on_portal_billing_and_licenses():
    clear_billing_facade()
    clear_license_facade()
    clear_product_ownership_facade()
    catalog = InMemoryProductCatalogStore()
    ownerships = InMemoryProductOwnershipStore()
    activations = InMemoryProductActivationStore()
    activation = ProductActivationFacade.from_parts(
        catalog=catalog, ownerships=ownerships, activations=activations
    )
    app = FastAPI()

    @app.middleware("http")
    async def guest_only(request: Request, call_next):
        request.state.account = None
        return await call_next(request)

    register_portal_billing(app, store=InMemoryBillingStore())
    register_portal_licenses(app, catalog=catalog, activation=activation)
    register_portal_my_products(app, ownership_store=ownerships, catalog=catalog)
    http = TestClient(app)
    try:
        assert http.get("/portal/billing").status_code == 401
        assert http.get("/portal/licenses").status_code == 401
        assert http.get("/portal/my-products").status_code == 401
    finally:
        clear_billing_facade()
        clear_license_facade()
        clear_product_ownership_facade()


def test_client_own_only_billing_not_foreign():
    clear_billing_facade()
    alice = new_account(email="alice@s13.test", display_name="Alice", status="ready")
    bob = new_account(email="bob@s13.test", display_name="Bob", status="ready")
    store = InMemoryBillingStore()
    billing = BillingFacade.from_store(store)
    # Seed Alice transaction via facade purchase path is heavy — write via list after purchase helper
    from app.portal.purchase_facade import PurchaseFacade
    from app.portal.purchase_store import InMemoryPurchaseStore
    from app.portal.product_catalog_store import InMemoryProductCatalogStore
    from app.portal.product_activation_facade import ProductActivationFacade
    from app.portal.product_activation_store import InMemoryProductActivationStore
    from app.portal.product_ownership_store import InMemoryProductOwnershipStore
    from app.portal.license_facade import LicenseFacade
    from app.portal.license_store import InMemoryLicenseStore

    catalog = InMemoryProductCatalogStore()
    ownerships = InMemoryProductOwnershipStore()
    activations = InMemoryProductActivationStore()
    activation = ProductActivationFacade.from_parts(
        catalog=catalog, ownerships=ownerships, activations=activations
    )
    licenses = LicenseFacade.from_parts(
        catalog=catalog, licenses=InMemoryLicenseStore(), activation=activation
    )
    purchase = PurchaseFacade.from_parts(
        catalog=catalog,
        purchases=InMemoryPurchaseStore(),
        licenses=licenses,
        billing=billing,
    )
    purchase.purchase(account_id=alice.account_id, catalog_product_id="prod_chatbot")
    alice_rows = billing.list_transactions(account_id=alice.account_id)
    assert alice_rows
    tx_id = alice_rows[0].transaction_id

    holder: dict[str, object] = {"account": bob}
    app = FastAPI()

    @app.middleware("http")
    async def inject(request: Request, call_next):
        request.state.account = holder["account"]
        return await call_next(request)

    register_portal_billing(app, store=store)
    http = TestClient(app)
    try:
        holder["account"] = bob
        assert http.get(f"/portal/billing/{tx_id}").status_code == 404
        holder["account"] = alice
        assert http.get(f"/portal/billing/{tx_id}").status_code == 200
    finally:
        clear_billing_facade()


def test_owner_paths_not_public_and_client_admin_deny_rule():
    assert is_owner_api_path("/api/owner/dashboard")
    assert not is_public_api_path("/api/owner/dashboard", "GET")
    assert not production_api_allowed("/api/owner/dashboard", "GET")
    assert client_admin_denied()


def test_support_role_has_no_portal_admin_and_no_silent_portal_commerce():
    """Support is not a portal Account role — commerce APIs stay own_only/deny for guests."""
    assert support_admin_denied()
    assert matrix_cell("support", "admin") == "deny"
    assert matrix_cell("support", "billing") == "read_limited"
    # Until Support portal principal exists, Guest/Client rules remain the enforceables.
    assert guest_must_be_denied("billing")
