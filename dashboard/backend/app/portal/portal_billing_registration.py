"""Commercial Platform 6.6 — Register Billing ledger."""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.billing_facade import BillingFacade
from app.portal.billing_store import BillingStore, InMemoryBillingStore
from app.portal.portal_billing_router import (
    portal_billing_router,
    set_billing_facade,
)

ENGINE_ID = "portal_billing_registration_v1"


def register_portal_billing(
    app: FastAPI,
    *,
    store: BillingStore | None = None,
) -> BillingFacade:
    ledger = store if store is not None else InMemoryBillingStore()
    facade = BillingFacade.from_store(ledger)
    set_billing_facade(facade)
    app.include_router(portal_billing_router)
    return facade
