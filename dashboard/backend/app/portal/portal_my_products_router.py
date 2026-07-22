"""Mission 6.2 — My Products HTTP.

GET /portal/my-products
→ RequestPrincipal (authenticated) → ProductOwnershipFacade

Platform-level · AuthN required · no website AuthorizationFacade.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.portal.product_ownership_facade import ProductOwnershipFacade
from app.portal.product_ownership_view import MyProductView

ENGINE_ID = "portal_my_products_router_v1"

portal_my_products_router = APIRouter(
    prefix="/portal",
    tags=["portal-my-products"],
)

_ownership_facade: ProductOwnershipFacade | None = None


def set_product_ownership_facade(facade: ProductOwnershipFacade) -> None:
    global _ownership_facade
    _ownership_facade = facade


def clear_product_ownership_facade() -> None:
    global _ownership_facade
    _ownership_facade = None


def get_product_ownership_facade() -> ProductOwnershipFacade:
    if _ownership_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_my_products_not_configured"
        )
    return _ownership_facade


@portal_my_products_router.get(
    "/my-products",
    response_model=None,
)
def http_get_my_products(
    request: Request,
    ownership: Annotated[
        ProductOwnershipFacade, Depends(get_product_ownership_facade)
    ],
) -> list[MyProductView]:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return ownership.list_my_products(account.account_id)
