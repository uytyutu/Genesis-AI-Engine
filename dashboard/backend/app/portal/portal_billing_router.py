"""Commercial Platform 6.6 — Billing HTTP (read ledger).

GET /portal/billing
GET /portal/billing/{transaction_id}
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.portal.billing_facade import BillingFacade
from app.portal.billing_view import BillingView

ENGINE_ID = "portal_billing_router_v1"

portal_billing_router = APIRouter(
    prefix="/portal",
    tags=["portal-billing"],
)

_billing_facade: BillingFacade | None = None


def set_billing_facade(facade: BillingFacade) -> None:
    global _billing_facade
    _billing_facade = facade


def clear_billing_facade() -> None:
    global _billing_facade
    _billing_facade = None


def get_billing_facade() -> BillingFacade:
    if _billing_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_billing_not_configured"
        )
    return _billing_facade


@portal_billing_router.get("/billing", response_model=None)
def http_list_billing(
    request: Request,
    billing: Annotated[BillingFacade, Depends(get_billing_facade)],
) -> list[BillingView]:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return billing.list_transactions(account_id=account.account_id)


@portal_billing_router.get("/billing/{transaction_id}", response_model=None)
def http_get_billing(
    transaction_id: str,
    request: Request,
    billing: Annotated[BillingFacade, Depends(get_billing_facade)],
) -> BillingView:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    view = billing.get_transaction(
        account_id=account.account_id, transaction_id=transaction_id
    )
    if view is None:
        raise HTTPException(status_code=404, detail="transaction_not_found")
    return view
