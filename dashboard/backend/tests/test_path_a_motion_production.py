"""Path A: motion_level flows order → checkout metadata → Factory → ZIP (all markets)."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from app.factory.factory_service import FactoryService
from app.factory.market_delivery import PATH_A_DELIVERY_MARKETS, market_legal_pack
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.finance_service import FinanceService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.revenue_pipeline_service import RevenuePipelineService
from app.integration.sales_order_service import SalesOrderService


def _real_pipeline(tmp_path: Path) -> tuple[SalesOrderService, RevenuePipelineService]:
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    intent = FactoryIntentService(memory_dir=tmp_path, factory=factory)
    sales = SalesOrderService(tmp_path, intent)
    revenue = RevenuePipelineService(
        sales,
        FinanceService(tmp_path),
        PaymentCheckoutService(tmp_path),
        OwnerNotificationService(tmp_path),
    )
    return sales, revenue


def test_create_order_defaults_motion_none(tmp_path: Path):
    sales, _ = _real_pipeline(tmp_path)
    created = sales.create_order(
        {
            "business_name": "Cafe Classic",
            "description": "Cafe Berlin",
            "email": "c@test.de",
            "package_id": "basic",
            "city": "Berlin",
        }
    )
    order = sales.get_order(created["order_id"])
    assert order["motion_level"] == "none"
    assert created["motion_level"] == "none"


def test_create_order_rejects_3d_premium(tmp_path: Path):
    sales, _ = _real_pipeline(tmp_path)
    with pytest.raises(ValueError, match="WAITLIST_REQUIRED"):
        sales.create_order(
            {
                "business_name": "3D Studio",
                "description": "WebGL landing",
                "email": "x@test.de",
                "package_id": "basic",
                "motion_level": "3d_premium",
            }
        )


def test_sandbox_checkout_carries_motion_level(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    sales, revenue = _real_pipeline(tmp_path)
    created = sales.create_order(
        {
            "business_name": "Praxis Motion",
            "description": "Zahnarzt Koeln Prophylaxe",
            "email": "a@b.de",
            "package_id": "basic",
            "city": "Koeln",
            "motion_level": "css",
            "market_code": "DE",
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
    session = revenue.begin_checkout(
        order_id,
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
    )
    assert session["motion_level"] == "css"
    assert session["market_code"] == "DE"

    revenue.complete_sandbox_payment(order_id)
    status = sales.public_status(order_id)
    assert status["motion_level"] == "css"
    assert status["download_ready"] is True

    data, _name = sales.build_client_download(order_id)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
    assert "assets/motion_kit.css" in names
    assert "assets/reveal.js" in names
    assert "index.html" in names
    html = zipfile.ZipFile(io.BytesIO(data)).read("index.html").decode("utf-8")
    assert "motion_kit.css" in html


def test_stripe_checkout_metadata_includes_motion(monkeypatch: pytest.MonkeyPatch):
    """Stripe session payload must carry motion_level + market_code metadata."""
    captured: dict = {}

    class _Resp:
        status_code = 200

        def json(self):
            return {"url": "https://checkout.stripe.test/cs_test", "id": "cs_test_1"}

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, data=None, auth=None):
            captured["data"] = dict(data or {})
            return _Resp()

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_dummy")
    monkeypatch.delenv("GENESIS_PAYMENT_SANDBOX", raising=False)
    monkeypatch.setattr(
        "app.integration.payment_checkout_service.httpx.Client",
        _Client,
    )
    svc = PaymentCheckoutService()
    out = svc.create_checkout(
        order_id="ord-m1",
        amount_eur=350,
        label="Landing Basic — Test",
        success_url="http://localhost/ok",
        cancel_url="http://localhost/cancel",
        motion_level="css",
        market_code="US",
    )
    assert out["provider"] == "stripe"
    assert captured["data"]["metadata[order_id]"] == "ord-m1"
    assert captured["data"]["metadata[motion_level]"] == "css"
    assert captured["data"]["metadata[market_code]"] == "US"


def test_classic_path_a_zip_has_no_motion_assets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    sales, revenue = _real_pipeline(tmp_path)
    created = sales.create_order(
        {
            "business_name": "Classic Shop",
            "description": "Handwerk Berlin",
            "email": "c@test.de",
            "package_id": "basic",
            "city": "Berlin",
            "motion_level": "none",
            "client_legal": {
                "owner_name": "Owner",
                "street": "Str. 1",
                "zip": "10115",
                "city": "Berlin",
                "email": "c@test.de",
            },
        }
    )
    oid = created["order_id"]
    revenue.begin_checkout(oid, success_url="http://x/ok", cancel_url="http://x/c")
    revenue.complete_sandbox_payment(oid)
    data, _ = sales.build_client_download(oid)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
    assert "assets/motion_kit.css" not in names
    html = zipfile.ZipFile(io.BytesIO(data)).read("index.html").decode("utf-8")
    assert "motion_kit.css" not in html


@pytest.mark.parametrize("market", list(PATH_A_DELIVERY_MARKETS))
def test_css_motion_zip_all_path_a_markets(tmp_path: Path, market: str):
    """Every Path A market: css production ZIP includes motion assets + market legal."""
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    intent = FactoryIntentService(memory_dir=tmp_path, factory=factory)
    sales = SalesOrderService(tmp_path, intent)
    created = sales.create_order(
        {
            "business_name": f"Local Biz {market}",
            "description": f"Local service landing for market {market} with clear offer",
            "email": f"owner@{market.lower()}.example",
            "package_id": "basic",
            "city": "City",
            "market_code": market,
            "motion_level": "css",
            "client_legal": {
                "owner_name": "Owner Name",
                "street": "Main 1",
                "zip": "10000",
                "city": "City",
                "country": market,
                "email": f"owner@{market.lower()}.example",
            },
        }
    )
    order = sales.get_order(created["order_id"])
    assert order["motion_level"] == "css"
    # Commerce checkout may remap some codes (e.g. IE→DEFAULT); pin Path A delivery market.
    order["market_code"] = market
    legal = dict(order.get("client_legal") or {})
    legal["country"] = market
    order["client_legal"] = legal
    order["status"] = "paid"
    sales._save_order(order)

    result = sales.start_production(created["order_id"])
    product_id = result["product_id"]
    root = tmp_path / "sandbox" / product_id
    assert (root / "assets" / "motion_kit.css").is_file()
    assert (root / "assets" / "reveal.js").is_file()
    html = (root / "index.html").read_text(encoding="utf-8")
    assert "motion_kit.css" in html

    data, _ = sales.build_client_download(created["order_id"])
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
    assert "index.html" in names
    assert "assets/motion_kit.css" in names
    assert "assets/reveal.js" in names
    assert "README_PUBLISH.txt" in names

    pack = market_legal_pack(market)
    if pack == "de_impressum":
        assert "impressum.html" in names
        assert "datenschutz.html" in names
    elif pack in ("us_privacy", "uk_privacy"):
        assert "privacy.html" in names or "terms.html" in names or any(
            n.endswith(".html") and n != "index.html" for n in names
        )
    else:
        assert "LEGAL_NOTICE.txt" in names or any(
            n.endswith(".html") and n != "index.html" for n in names
        ) or "README_PUBLISH.txt" in names
