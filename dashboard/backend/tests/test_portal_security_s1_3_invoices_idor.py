"""S1.3 — Invoices IDOR (portal billing transactions = client invoices)."""

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
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_activation_store import InMemoryProductActivationStore
from app.portal.product_catalog_store import InMemoryProductCatalogStore
from app.portal.product_ownership_store import InMemoryProductOwnershipStore
from app.portal.purchase_facade import PurchaseFacade
from app.portal.purchase_store import InMemoryPurchaseStore


def test_invoice_transaction_idor_cross_account():
    """Portal has no /invoices route — billing transactions are the invoice ledger."""
    clear_billing_facade()
    alice = new_account(email="inv-a@s13.test", display_name="A", status="ready")
    bob = new_account(email="inv-b@s13.test", display_name="B", status="ready")
    catalog = InMemoryProductCatalogStore()
    ownerships = InMemoryProductOwnershipStore()
    activations = InMemoryProductActivationStore()
    activation = ProductActivationFacade.from_parts(
        catalog=catalog, ownerships=ownerships, activations=activations
    )
    licenses = LicenseFacade.from_parts(
        catalog=catalog, licenses=InMemoryLicenseStore(), activation=activation
    )
    billing_store = InMemoryBillingStore()
    billing = BillingFacade.from_store(billing_store)
    purchase = PurchaseFacade.from_parts(
        catalog=catalog,
        purchases=InMemoryPurchaseStore(),
        licenses=licenses,
        billing=billing,
    )
    purchase.purchase(account_id=alice.account_id, catalog_product_id="prod_chatbot")
    tx_id = billing.list_transactions(account_id=alice.account_id)[0].transaction_id

    holder: dict[str, object] = {"account": bob}
    app = FastAPI()

    @app.middleware("http")
    async def inject(request: Request, call_next):
        request.state.account = holder["account"]
        return await call_next(request)

    register_portal_billing(app, store=billing_store)
    http = TestClient(app)
    try:
        holder["account"] = bob
        assert http.get(f"/portal/billing/{tx_id}").status_code == 404
        assert http.get("/portal/billing").json() == []
        holder["account"] = alice
        assert http.get(f"/portal/billing/{tx_id}").status_code == 200
    finally:
        clear_billing_facade()
