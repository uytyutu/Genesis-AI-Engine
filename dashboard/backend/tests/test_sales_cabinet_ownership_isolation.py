"""Sales cabinet ownership — Client A must never see Client B products."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.sales_order_service import SalesOrderService
from app.integration.website_admin.ownership import assert_website_order_access


class _Factory:
    def submit(self, intent):  # noqa: ANN001
        return {"product_id": "prod-x"}

    class _Inner:
        def get_product(self, product_id: str):  # noqa: ANN001
            return {"id": product_id}

    _factory = _Inner()


def _svc(tmp_path: Path) -> SalesOrderService:
    return SalesOrderService(tmp_path, _Factory())


def test_list_orders_excludes_foreign_customer_same_email(tmp_path: Path) -> None:
    sales = _svc(tmp_path)
    # Client B owns a cleaning site with shared email typo / collision surface
    foreign = sales.create_order(
        {
            "business_name": "Putzfee Reinigung",
            "email": "shared@example.com",
            "customer_id": "cust-b",
            "description": "Cleaning",
            "package_id": "basic",
        }
    )
    own = sales.create_order(
        {
            "business_name": "Lorenne Beauty",
            "email": "shared@example.com",
            "customer_id": "cust-a",
            "description": "Beauty",
            "package_id": "premium",
        }
    )
    rows = sales.list_orders_for_customer(
        customer_id="cust-a", email="shared@example.com", limit=50
    )
    ids = {str(r.get("order_id")) for r in rows}
    assert own["order_id"] in ids
    assert foreign["order_id"] not in ids
    assert all("Putzfee" not in str(r.get("business_name") or "") for r in rows)


def test_attach_does_not_steal_foreign_customer_orders(tmp_path: Path) -> None:
    sales = _svc(tmp_path)
    foreign = sales.create_order(
        {
            "business_name": "Putzfee Reinigung",
            "email": "wife@example.com",
            "customer_id": "cust-other",
            "description": "Cleaning",
            "package_id": "basic",
        }
    )
    guest = sales.create_order(
        {
            "business_name": "Guest Site",
            "email": "wife@example.com",
            "description": "Guest",
            "package_id": "basic",
        }
    )
    # Guest has empty customer_id after create — ensure
    g = sales.get_order(guest["order_id"])
    assert g is not None
    g["customer_id"] = ""
    sales._save_order(g)

    linked = sales.attach_customer_by_email(
        customer_id="cust-wife", email="wife@example.com"
    )
    assert linked == 1
    still_foreign = sales.get_order(foreign["order_id"])
    assert still_foreign is not None
    assert still_foreign.get("customer_id") == "cust-other"
    claimed = sales.get_order(guest["order_id"])
    assert claimed is not None
    assert claimed.get("customer_id") == "cust-wife"


def test_boolean_superseded_hidden_from_cabinet(tmp_path: Path) -> None:
    sales = _svc(tmp_path)
    created = sales.create_order(
        {
            "business_name": "Old Lorenne",
            "email": "a@example.com",
            "customer_id": "cust-a",
            "description": "old",
            "package_id": "premium",
        }
    )
    order = sales.get_order(created["order_id"])
    assert order is not None
    order["superseded"] = True
    sales._save_order(order)
    rows = sales.list_orders_for_customer(customer_id="cust-a", email="a@example.com")
    assert all(str(r.get("order_id")) != created["order_id"] for r in rows)


def test_website_admin_forbidden_for_same_email_foreign_owner(tmp_path: Path) -> None:
    sales = _svc(tmp_path)
    created = sales.create_order(
        {
            "business_name": "Foreign Web",
            "email": "same@example.com",
            "customer_id": "cust-b",
            "description": "x",
            "package_id": "basic",
        }
    )
    order = sales.get_order(created["order_id"])
    with pytest.raises(ValueError, match="forbidden"):
        assert_website_order_access(
            order, customer_id="cust-a", email="same@example.com"
        )


def test_shop_owner_forbidden_for_same_email_foreign_owner(tmp_path: Path) -> None:
    sales = _svc(tmp_path)
    created = sales.create_order(
        {
            "business_name": "Foreign Shop",
            "email": "same@example.com",
            "customer_id": "cust-b",
            "description": "shop",
            "package_id": "ecommerce_shop",
            "product_kind": "shop",
            "shop_brief": {
                "company_name": "Foreign",
                "store_name": "Shop",
                "what_is_sold": "goods",
                "category": "other",
                "catalog_size": "10",
                "languages": ["de"],
                "currency": "EUR",
                "payments": ["stripe"],
                "shipping": ["dhl"],
                "pages": ["home", "catalog"],
                "style": "modern",
            },
        }
    )
    with pytest.raises(ValueError, match="forbidden"):
        sales._assert_shop_owner(
            created["order_id"], customer_id="cust-a", email="same@example.com"
        )
