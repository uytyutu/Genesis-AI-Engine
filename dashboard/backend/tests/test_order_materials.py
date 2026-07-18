"""Buyer materials + honest insights (Path A)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from app.integration.order_materials_service import OrderMaterialsService
from app.integration.sales_order_service import SalesOrderService


class _Factory:
    def submit(self, intent):  # noqa: ANN001
        return {"product_id": "prod-test-1"}

    class _Inner:
        def get_product(self, product_id: str):  # noqa: ANN001
            return {"id": product_id}

    _factory = _Inner()


class _Upload:
    def __init__(self, name: str, data: bytes, content_type: str) -> None:
        self.filename = name
        self.content_type = content_type
        self.file = BytesIO(data)


def test_save_image_and_txt_findings(tmp_path: Path):
    svc = OrderMaterialsService(tmp_path)
    img = svc.save(_Upload("logo.png", b"\x89PNG\r\n\x1a\nfake", "image/png"))
    assert img["id"].startswith("mat-")
    assert any(f.get("id") == "image" for f in img["findings"])
    assert any(f.get("id") == "logo_name" for f in img["findings"])

    txt = svc.save(
        _Upload("notes.txt", b"Kontakt: hello@firma.de Tel +49 221 123456", "text/plain")
    )
    assert any(f.get("id") == "email" for f in txt["findings"])


def test_unsupported_ext_rejected(tmp_path: Path):
    svc = OrderMaterialsService(tmp_path)
    try:
        svc.save(_Upload("virus.exe", b"MZ", "application/octet-stream"))
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "nicht unterstützt" in str(exc)


def test_create_order_attaches_materials_and_social(tmp_path: Path):
    mats = OrderMaterialsService(tmp_path)
    uploaded = mats.save(_Upload("flyer.txt", b"Instagram @demo", "text/plain"))
    sales = SalesOrderService(tmp_path, _Factory())
    created = sales.create_order(
        {
            "business_name": "Demo GmbH",
            "description": "Handwerk Köln",
            "email": "buyer@demo.de",
            "package_id": "basic",
            "domain_status": "none",
            "instagram": "https://instagram.com/demo",
            "material_ids": [uploaded["id"]],
        }
    )
    order = sales.get_order(created["order_id"])
    assert order is not None
    assert order["domain_status"] == "none"
    assert order["domain_help_message"]
    assert order["social_links"]["instagram"]
    assert order["materials"]["count"] == 1
    assert order["project_workspace"]["materials"]
    checks = (created.get("buyer_insights") or {}).get("checks") or []
    labels = " ".join(str(c.get("label_de") or "") for c in checks)
    assert "Instagram" in labels
    assert "Domain später" in labels or "Datei" in labels
