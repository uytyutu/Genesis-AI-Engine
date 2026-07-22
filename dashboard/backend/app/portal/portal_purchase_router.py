"""Commercial Platform 6.4 — Purchase HTTP.

POST /portal/products/{product_id}/purchase
→ AuthN → PurchaseFacade → Payment stub → ProductActivationFacade
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.portal.purchase import PurchaseError
from app.portal.purchase_facade import PurchaseFacade
from app.portal.purchase_view import PurchaseView

ENGINE_ID = "portal_purchase_router_v1"

portal_purchase_router = APIRouter(
    prefix="/portal",
    tags=["portal-purchases"],
)

_purchase_facade: PurchaseFacade | None = None


def set_purchase_facade(facade: PurchaseFacade) -> None:
    global _purchase_facade
    _purchase_facade = facade


def clear_purchase_facade() -> None:
    global _purchase_facade
    _purchase_facade = None


def get_purchase_facade() -> PurchaseFacade:
    if _purchase_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_purchases_not_configured"
        )
    return _purchase_facade


@portal_purchase_router.post(
    "/products/{product_id}/purchase",
    response_model=None,
)
def http_purchase_product(
    product_id: str,
    request: Request,
    purchases: Annotated[PurchaseFacade, Depends(get_purchase_facade)],
) -> PurchaseView:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    try:
        return purchases.purchase(
            account_id=account.account_id,
            catalog_product_id=product_id,
        )
    except PurchaseError as exc:
        reason = str(exc)
        if reason == "product_not_found":
            raise HTTPException(status_code=404, detail=reason) from None
        raise HTTPException(status_code=400, detail=reason) from None
