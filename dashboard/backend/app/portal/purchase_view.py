"""Commercial Platform 6.4 — Purchase View."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.product_ownership_view import MyProductView
from app.portal.purchase import Purchase

ENGINE_ID = "purchase_view_v1"


@dataclass(frozen=True)
class PurchaseView:
    purchase_id: str
    catalog_product_id: str
    product_type: str
    status: str
    provider: str
    provider_reference: str | None
    activated_product: MyProductView | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "purchase_id": self.purchase_id,
            "catalog_product_id": self.catalog_product_id,
            "product_type": self.product_type,
            "status": self.status,
            "provider": self.provider,
            "provider_reference": self.provider_reference,
            "activated_product": (
                self.activated_product.as_dict()
                if self.activated_product is not None
                else None
            ),
        }


def build_purchase_view(
    purchase: Purchase,
    *,
    activated_product: MyProductView | None = None,
) -> PurchaseView:
    return PurchaseView(
        purchase_id=purchase.purchase_id,
        catalog_product_id=purchase.catalog_product_id,
        product_type=purchase.product_type,
        status=purchase.status,
        provider=purchase.provider,
        provider_reference=purchase.provider_reference,
        activated_product=activated_product,
    )
