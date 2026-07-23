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
    """Pack must recurse into assets/ (hero_pack/…); use a real Factory build for QG."""
    factory = FactoryService(memory_dir=tmp_path / "mem", sandbox_dir=tmp_path / "sandbox")
    built = factory.build_landing(
        "Autowerkstatt Bergmann — Inspektion in Köln",
        package_id="basic",
        contacts={
            "business_name": "Autowerkstatt Bergmann",
            "phone": "+49 221 555",
            "email": "a@b.de",
            "city": "Köln",
        },
        market_code="DE",
    )
    product_id = built["product_id"]
    product_dir = tmp_path / "sandbox" / product_id
    nested = product_dir / "assets" / "hero_pack" / "basic"
    nested.mkdir(parents=True, exist_ok=True)
    (nested / "hero_1.jpg").write_bytes(b"nested-marker")

    data, _name = factory._pack_product_zip(
        product_id,
        factory._load_meta(product_id) or {},
        mark_download=False,
    )
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
    assert "assets/hero.jpg" in names or any(n.startswith("assets/") for n in names)
    assert "assets/hero_pack/basic/hero_1.jpg" in names
