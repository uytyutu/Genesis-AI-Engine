"""Mission 6.2 — My Products View (HTTP/API shape).

Stable contract for GET /portal/my-products.
Enrichment fields from Product Catalog must not require Ownership changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.product_ownership import ProductOwnership

ENGINE_ID = "product_ownership_view_v1"


@dataclass(frozen=True)
class MyProductView:
    product_id: str
    product_type: str
    display_name: str
    status: str
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_type": self.product_type,
            "display_name": self.display_name,
            "status": self.status,
            "source": self.source,
        }


def build_my_product_view(
    ownership: ProductOwnership,
    *,
    display_name: str,
) -> MyProductView:
    return MyProductView(
        product_id=ownership.product_id,
        product_type=ownership.product_type,
        display_name=display_name,
        status=ownership.status,
        source=ownership.source,
    )
