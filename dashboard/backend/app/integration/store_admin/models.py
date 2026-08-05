"""Store Admin product schema — physical first, other types reserved."""

from __future__ import annotations

from typing import Any, Literal

PRODUCT_TYPE_VALUES: tuple[str, ...] = (
    "physical",
    "digital",
    "service",
    "ticket",
    "booking",
)

# Only physical is fully editable in R3.1.2; others store type for future modules.
PRODUCT_TYPE_ACTIVE: frozenset[str] = frozenset({"physical"})

ProductStatus = Literal["draft", "published"]
StockStatus = Literal[
    "in_stock",
    "low_stock",
    "out_of_stock",
    "preorder",
    "made_to_order",
]

STATUS_VALUES: tuple[str, ...] = ("draft", "published")
STOCK_STATUS_VALUES: tuple[str, ...] = (
    "in_stock",
    "low_stock",
    "out_of_stock",
    "preorder",
    "made_to_order",
)


def empty_variants() -> dict[str, Any]:
    return {
        "size": [],
        "color": [],
        "material": [],
        "weight": None,
    }


def empty_seo() -> dict[str, str]:
    return {"title": "", "description": "", "slug": ""}


def default_product(*, product_type: str = "physical") -> dict[str, Any]:
    pt = product_type if product_type in PRODUCT_TYPE_VALUES else "physical"
    return {
        "id": "",
        "product_type": pt,
        "status": "draft",
        "title": "",
        "short_description": "",
        "description": "",
        "price": 0.0,
        "compare_at_price": None,
        "currency": "EUR",
        "sku": "",
        "stock_qty": 0,
        "stock_status": "in_stock",
        "category": "",
        "subcategory": "",
        "brand": "",
        "variants": empty_variants(),
        "images": [],
        "seo": empty_seo(),
        "created_at": "",
        "updated_at": "",
    }
