"""Website Admin ownership gate — customer owns a Website order (not shop)."""

from __future__ import annotations

from typing import Any


def assert_website_order_access(
    order: dict[str, Any] | None,
    *,
    customer_id: str | None,
    email: str | None,
) -> dict[str, Any]:
    """
    Raise ValueError with stable codes:
      order_not_found | forbidden | not_a_website_order
    """
    if not order or not isinstance(order, dict):
        raise ValueError("order_not_found")

    oid_cid = str(order.get("customer_id") or "").strip()
    oid_email = str(order.get("email") or "").strip().lower()
    cid = str(customer_id or "").strip()
    mail = str(email or "").strip().lower()

    owns = False
    if cid and oid_cid and cid == oid_cid:
        owns = True
    elif mail and oid_email and mail == oid_email:
        owns = True
    if not owns:
        raise ValueError("forbidden")

    kind = str(order.get("product_kind") or "").strip().lower()
    package_id = str(order.get("package_id") or "").strip().lower()
    if kind == "shop" or package_id == "ecommerce_shop":
        raise ValueError("not_a_website_order")

    return order
