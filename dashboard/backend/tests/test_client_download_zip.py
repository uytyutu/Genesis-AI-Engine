"""Path A — client ZIP download after payment/production."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from app.factory.factory_service import FactoryService
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.finance_service import FinanceService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.revenue_pipeline_service import RevenuePipelineService
from app.integration.sales_order_service import SalesOrderService


def test_client_download_zip_after_sandbox_payment(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")

    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    intent = FactoryIntentService(memory_dir=tmp_path, factory=factory)
    sales = SalesOrderService(tmp_path, intent)
    revenue = RevenuePipelineService(
        sales,
        FinanceService(tmp_path),
        PaymentCheckoutService(tmp_path),
        OwnerNotificationService(tmp_path),
    )

    created = sales.create_order(
        {
            "business_name": "Praxis Download",
            "description": "Zahnarzt Koeln Prophylaxe",
            "email": "a@b.de",
            "package_id": "basic",
            "city": "Koeln",
            "client_legal": {
                "owner_name": "Dr. Test",
                "street": "Testweg 1",
                "zip": "50667",
                "city": "Koeln",
                "email": "a@b.de",
            },
        }
    )
    order_id = created["order_id"]
    before = sales.public_status(order_id)
    assert before["download_ready"] is False

    revenue.begin_checkout(
        order_id,
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
    )
    revenue.complete_sandbox_payment(order_id)

    status = sales.public_status(order_id)
    assert status["paid"] is True
    assert status["download_ready"] is True
    assert status["download_url"] == f"/api/sales/orders/{order_id}/download"

    data, filename = sales.build_client_download(order_id)
    assert filename.endswith(".zip")
    assert data[:2] == b"PK"

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
    assert "index.html" in names
    assert "impressum.html" in names
    assert "datenschutz.html" in names
    assert "README_PUBLISH.txt" in names

    after = sales.public_status(order_id)
    assert after["status"] == "ready"
