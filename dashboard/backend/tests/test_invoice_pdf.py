"""Gen1 PDF Invoice / Credit Note."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.integration.platform_global_analytics import build_gen1_readiness
from app.integration.store_admin.business_profile import BusinessProfileService
from app.integration.store_admin.commerce_settings import StoreCommerceSettingsService
from app.integration.store_admin.invoice_pdf_service import StoreInvoiceService


def _seed_shop_order(memory: Path, store_id: str, shop_order_id: str = "SO-100") -> None:
    shop = memory / "store_admin" / store_id
    shop.mkdir(parents=True, exist_ok=True)
    order = {
        "id": shop_order_id,
        "status": "pending_payment",
        "buyer": {"name": "Anna Müller", "email": "anna@example.de"},
        "address": {
            "line1": "Hauptstr. 1",
            "postal_code": "10115",
            "city": "Berlin",
            "country": "DE",
        },
        "items": [
            {
                "product_id": "p1",
                "title": "Nordlicht Stuhl",
                "unit_price_eur": 199.0,
                "qty": 2,
                "line_total_eur": 398.0,
            }
        ],
        "subtotal_eur": 398.0,
        "shipping_eur": 7.9,
        "tax_eur": 63.0,
        "total_eur": 405.9,
        "currency": "EUR",
        "payment_method": {"id": "invoice", "label": "Invoice"},
        "shipping_method": {"id": "dhl", "label": "DHL Standard"},
    }
    (shop / "orders.json").write_text(
        json.dumps({"orders": [order]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_create_invoice_pdf_and_credit_note(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_SMTP_MOCK", "1")
    store_id = "shop-pdf"
    _seed_shop_order(tmp_path, store_id)

    bp = BusinessProfileService(tmp_path)
    bp.update(
        store_id,
        {
            "company_name": "Nordlicht Möbel GmbH",
            "email_support": "info@nordlicht.de",
            "phone_primary": "030 111",
            "address": {
                "street": "Werkstr. 2",
                "postal_code": "10117",
                "city": "Berlin",
                "country": "DE",
            },
        },
    )
    commerce = StoreCommerceSettingsService(tmp_path)
    commerce.update_tax_config(store_id, {"profile": "de_standard", "company_vat_id": "DE123"})
    commerce.update_invoice_config(
        store_id,
        {
            "prefix": "INV-2026",
            "language": "de",
            "signature_text": "Mit freundlichen Grüßen",
            "show_payment_qr": True,
        },
    )

    svc = StoreInvoiceService(tmp_path)
    out = svc.create_invoice(store_id, shop_order_id="SO-100", language="de")
    assert out["ok"] is True
    doc = out["document"]
    assert doc["number"].startswith("INV-2026-")
    assert doc["seller"]["company_name"] == "Nordlicht Möbel GmbH"
    assert doc["seller"]["vat_id"] == "DE123"
    assert doc["totals"]["total_eur"] == 405.9
    assert out["vector_hint"]["message"].startswith("✅")
    pdf_path = tmp_path / "store_admin" / store_id / doc["pdf_path"]
    assert pdf_path.is_file()
    assert pdf_path.stat().st_size > 500
    assert pdf_path.read_bytes()[:4] == b"%PDF"

    data, number = svc.read_pdf_bytes(store_id, doc["id"])
    assert number == doc["number"]
    assert data[:4] == b"%PDF"

    cn = svc.create_credit_note(
        store_id,
        invoice_doc_id=doc["id"],
        reason="Defekt",
        refund_type="full",
    )
    assert cn["document"]["type"] == "credit_note"
    assert cn["document"]["credit_of"] == doc["number"]
    assert cn["document"]["reason"] == "Defekt"
    assert (tmp_path / "store_admin" / store_id / cn["document"]["pdf_path"]).is_file()

    listed = svc.list_documents(store_id)
    assert listed["count"] >= 2

    ready = build_gen1_readiness(tmp_path)
    pdf_item = next(i for i in ready["items"] if i["id"] == "pdf")
    assert pdf_item["status"] == "done"


def test_invoice_localization_en(tmp_path: Path):
    store_id = "shop-en"
    _seed_shop_order(tmp_path, store_id, "SO-EN")
    BusinessProfileService(tmp_path).update(store_id, {"company_name": "Demo Ltd"})
    svc = StoreInvoiceService(tmp_path)
    out = svc.create_invoice(store_id, shop_order_id="SO-EN", language="en")
    assert out["document"]["language"] == "en"
    assert out["document"]["pdf_path"]
