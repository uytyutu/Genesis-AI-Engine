"""Factory ZIP performance — cache + referenced-assets only."""

from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

from app.factory.factory_service import FactoryService
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.finance_service import FinanceService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.revenue_pipeline_service import RevenuePipelineService
from app.integration.sales_order_service import SalesOrderService


def test_client_zip_skips_duplicate_hero_pack_and_caches(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.setenv("GENESIS_ALLOW_DEMO_PAYMENT", "1")

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
            "business_name": "Perf Bake GmbH",
            "description": "Baeckerei Berlin Broetchen Kuchen Fruehstueck",
            "email": "perf@test.example",
            "package_id": "business",
            "city": "Berlin",
            "niche": "restaurant",
            "market_code": "DE",
            "demo": True,
            "client_legal": {
                "owner_name": "Perf",
                "street": "A 1",
                "zip": "10115",
                "city": "Berlin",
                "email": "perf@test.example",
            },
        }
    )
    order_id = created["order_id"]
    revenue.complete_demo_payment(order_id)
    status = sales.public_status(order_id)
    assert status["download_ready"] is True
    product_id = status["product_id"]

    t0 = time.perf_counter()
    data1, name1 = sales.build_client_download(order_id)
    t1 = time.perf_counter() - t0
    assert name1.endswith(".zip")
    assert data1[:2] == b"PK"

    with zipfile.ZipFile(io.BytesIO(data1)) as zf:
        names = set(zf.namelist())
    assert "index.html" in names
    # Duplicate hero_pack copies must not ship unless HTML references them.
    hero_pack = [n for n in names if "hero_pack/" in n and n.endswith((".jpg", ".jpeg", ".png"))]
    assert len(hero_pack) <= 1, f"unexpected hero_pack images: {hero_pack}"
    # ~15MB was 6× identical JPEGs; referenced-only should drop duplicate hero_pack.
    assert len(data1) < 9_000_000, f"zip still too large: {len(data1)}"
    assert len(data1) < 15_000_000  # hard regression vs pre-optimization

    cache = tmp_path / "sandbox" / product_id / "client_delivery.zip"
    assert cache.is_file()

    t0 = time.perf_counter()
    data2, _ = sales.build_client_download(order_id)
    t2 = time.perf_counter() - t0
    assert data2 == data1
    # Cached serve should be clearly faster than first pack on typical machines.
    assert t2 < max(0.5, t1 * 0.5) or t2 < 0.25
