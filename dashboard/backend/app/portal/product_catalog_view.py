"""Mission 6.1 — Product Catalog View (HTTP/API shape).

Presentation only. Contract should remain stable when Ownership / Billing arrive.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.product import Product

ENGINE_ID = "product_catalog_view_v1"


@dataclass(frozen=True)
class ProductCatalogItemView:
    product_id: str
    product_type: str
    display_name: str
    description: str
    availability: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_type": self.product_type,
            "display_name": self.display_name,
            "description": self.description,
            "availability": self.availability,
        }


def build_product_catalog_item_view(product: Product) -> ProductCatalogItemView:
    return ProductCatalogItemView(
        product_id=product.product_id,
        product_type=product.product_type,
        display_name=product.display_name,
        description=product.description,
        availability=product.availability,
    )
