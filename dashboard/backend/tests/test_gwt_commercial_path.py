"""Golden Website Test — commercial path checklist (GWT Stage 1).

Checklist (product SSOT):
  package → form → order → pay → Factory → site → cabinet → ZIP → status
  Full pass without manual operator intervention.

In-process E2E with real Factory (not stub).
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from app.factory.factory_service import FactoryService
from app.integration.customer_identity.service import CustomerIdentityService
from app.integration.demo_payment import is_demo_order
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.finance_service import FinanceService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.pricing_engine import resolve_path_a_offer
from app.integration.revenue_pipeline_service import RevenuePipelineService
from app.integration.sales_order_service import SalesOrderService
from app.security import is_public_api_path, production_api_allowed


GWT_EMAIL = "gwt-buyer@virtuscore-test.example"
GWT_COMPANY = "Golden Website Test Baeckerei"


@pytest.fixture()
def gwt_stack(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.setenv("GENESIS_ALLOW_DEMO_PAYMENT", "1")
    monkeypatch.setenv("GENESIS_SMTP_MOCK", "1")
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "gwt-test-jwt-secret-32chars!!")
    monkeypatch.setenv("GENESIS_STORE_BUYER_JWT_SECRET", "gwt-test-jwt-secret-32chars!!")

    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    intent = FactoryIntentService(memory_dir=tmp_path, factory=factory)
    sales = SalesOrderService(tmp_path, intent)
    revenue = RevenuePipelineService(
        sales,
        FinanceService(tmp_path),
        PaymentCheckoutService(tmp_path),
        OwnerNotificationService(tmp_path),
    )
    identity = CustomerIdentityService(tmp_path)
    return sales, revenue, identity


def test_pay_demo_is_public_in_production_allowlist():
    """GWT: guest Demo Payment must work when GENESIS_PRODUCTION=1."""
    path = "/api/sales/orders/ord-demo123/pay-demo"
    assert is_public_api_path(path, "POST") is True
    assert production_api_allowed(path, "POST") is True


def test_gwt_commercial_path_order_to_zip_and_cabinet(gwt_stack):
    """Stage 1 GWT — Virtus Core sells websites end-to-end."""
    sales, revenue, identity = gwt_stack

    # 1) Package selection (SSOT prices)
    business = resolve_path_a_offer("business", "DE")
    assert int(business.amount) == 399

    # 2–3) Form → create order (guest)
    created = sales.create_order(
        {
            "business_name": GWT_COMPANY,
            "description": "Bäckerei mit Café — Brötchen, Kuchen, Frühstück in Berlin",
            "email": GWT_EMAIL,
            "phone": "+49 30 1234567",
            "package_id": "business",
            "city": "Berlin",
            "niche": "restaurant",
            "market_code": "DE",
            "ui_lang": "de",
            "demo": True,
            "instagram": "https://instagram.com/gwt-baeckerei",
            "client_legal": {
                "owner_name": "GWT Tester",
                "street": "Musterstr. 1",
                "zip": "10115",
                "city": "Berlin",
                "email": GWT_EMAIL,
            },
        }
    )
    order_id = created["order_id"]
    assert created["price_eur"] > 0
    assert created.get("demo") is True or created.get("payment_mode") == "demo"
    assert created.get("demo_payment_available") is True

    before = sales.public_status(order_id)
    assert before["paid"] is False
    assert before["download_ready"] is False

    # 4) Payment (Demo Bridge)
    order = sales.get_order(order_id)
    assert order is not None
    assert is_demo_order(order) is True
    paid = revenue.complete_demo_payment(order_id)
    assert paid["ok"] is True

    # 5–6) Factory auto-start + site generated
    mid = sales.public_status(order_id)
    assert mid["paid"] is True
    assert mid.get("product_id"), "Factory must attach product_id without manual start"
    assert mid["download_ready"] is True
    assert mid["download_url"] == f"/api/sales/orders/{order_id}/download"

    # 8–9) ZIP download + status ready
    data, filename = sales.build_client_download(order_id)
    assert filename.endswith(".zip")
    assert data[:2] == b"PK"
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
    assert "index.html" in names
    assert "README_PUBLISH.txt" in names

    after = sales.public_status(order_id)
    assert after["status"] in {"ready", "delivered", "in_production"}
    assert after["download_ready"] is True
    # Prefer ready after successful pack
    assert after["status"] == "ready"

    # 7) Order appears in Client Workspace after register (same email)
    session = identity.register(
        name="GWT Buyer",
        email=GWT_EMAIL,
        password="GwtTestPass1!",
        locale="de",
        country="DE",
    )
    assert session.get("token")
    customer_id = identity._store.find_customer_by_email(GWT_EMAIL)
    assert customer_id
    rows = sales.list_orders_for_customer(customer_id=customer_id, email=GWT_EMAIL)
    assert any(r.get("order_id") == order_id for r in rows), (
        "Paid guest order must appear in cabinet after register with same email"
    )
