"""Mission 6.3 — Product Activation HTTP.

POST /portal/products/{product_id}/activate
→ RequestPrincipal → ProductActivationFacade → native ProductOwnership

Does not touch WebsiteOwnershipBridge · AuthZ website rules · payments.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.portal.product_activation import ProductActivationError
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_ownership_view import MyProductView

ENGINE_ID = "portal_product_activation_router_v1"

portal_product_activation_router = APIRouter(
    prefix="/portal",
    tags=["portal-product-activation"],
)

_activation_facade: ProductActivationFacade | None = None


class ProductActivateBody(BaseModel):
    activation_code: str = Field(min_length=1, max_length=64)


def set_product_activation_facade(facade: ProductActivationFacade) -> None:
    global _activation_facade
    _activation_facade = facade


def clear_product_activation_facade() -> None:
    global _activation_facade
    _activation_facade = None


def get_product_activation_facade() -> ProductActivationFacade:
    if _activation_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_product_activation_not_configured"
        )
    return _activation_facade


@portal_product_activation_router.post(
    "/products/{product_id}/activate",
    response_model=None,
)
def http_activate_product(
    product_id: str,
    body: ProductActivateBody,
    request: Request,
    activation: Annotated[
        ProductActivationFacade, Depends(get_product_activation_facade)
    ],
) -> MyProductView:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    try:
        return activation.activate(
            account_id=account.account_id,
            catalog_product_id=product_id,
            activation_code=body.activation_code,
        )
    except ProductActivationError as exc:
        reason = str(exc)
        if reason == "product_not_found":
            raise HTTPException(status_code=404, detail=reason) from None
        raise HTTPException(status_code=400, detail=reason) from None
