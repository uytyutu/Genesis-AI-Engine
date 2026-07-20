"""Gewerbe-launch thin fixes: receipt currency + recursive ZIP assets."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from app.factory.factory_service import FactoryService
from app.integration.receipt_email_service import ReceiptEmailService
from app.integration.revenue_pipeline_service import _render_client_receipt


def test_receipt_uses_price_label_not_forced_euro():
    order = {
        "order_id": "ord-pl-1",
        "business_name": "Salon Kraków",
        "package_name": "Landing Basic",
        "price_eur": 1200,
        "currency": "PLN",
        "symbol": "zł",
        "price_label": "1 200 zł",
        "email": "a@b.pl",
    }
    text = _render_client_receipt(
        order=order, paid=1200.0, status_path="/order/status/ord-pl-1"
    )
    assert "1 200 zł" in text
    assert "1200 €" not in text
    assert "1 200 €" not in text


def test_order_received_email_uses_price_label(monkeypatch):
    sent: dict = {}

    def _fake_send(self, **kwargs):
        sent.update(kwargs)
        return {"ok": True, "skipped": True}

    monkeypatch.setattr(ReceiptEmailService, "_send", _fake_send)
    svc = ReceiptEmailService()
    svc.send_order_received(
        order={
            "order_id": "ord-gb-1",
            "business_name": "London Shop",
            "package_name": "Landing Basic",
            "price_eur": 320,
            "currency": "GBP",
            "symbol": "£",
            "price_label": "320 £",
            "email": "a@b.uk",
        }
    )
    assert "320 £" in sent.get("text", "")
    assert "320 €" not in sent.get("text", "")


def test_client_zip_includes_nested_assets(tmp_path: Path):
    factory = FactoryService(tmp_path)
    product_id = "nested-assets-1"
    product_dir = factory._sandbox / product_id
    product_dir.mkdir(parents=True)
    (product_dir / "index.html").write_text("<html>ok</html>", encoding="utf-8")
    (product_dir / "meta.json").write_text(
        '{"business_name":"Test","market_code":"DE","package_id":"basic"}',
        encoding="utf-8",
    )
    nested = product_dir / "assets" / "hero_pack" / "basic"
    nested.mkdir(parents=True)
    (product_dir / "assets" / "hero.jpg").write_bytes(b"top")
    (nested / "hero_1.jpg").write_bytes(b"nested")

    data, _name = factory._pack_product_zip(
        product_id,
        {"business_name": "Test", "market_code": "DE", "package_id": "basic"},
        mark_download=False,
    )
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
    assert "assets/hero.jpg" in names
    assert "assets/hero_pack/basic/hero_1.jpg" in names
