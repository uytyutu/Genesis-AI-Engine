"""Path A — client Impressum / Datenschutz templates for Factory."""

from __future__ import annotations

from pathlib import Path

from app.factory.client_legal_pages import ClientLegalInfo, write_client_legal_pages
from app.factory.factory_service import FactoryService


def test_legal_pages_mark_incomplete_without_address(tmp_path: Path):
    info = ClientLegalInfo(business_name="Praxis Test", email="a@b.de")
    assert "street" in info.missing_impressum_fields()
    assert info.is_impressum_ready() is False
    meta = write_client_legal_pages(tmp_path, info)
    assert meta["impressum_ready"] is False
    assert (tmp_path / "impressum.html").is_file()
    assert (tmp_path / "datenschutz.html").is_file()
    text = (tmp_path / "impressum.html").read_text(encoding="utf-8")
    assert "Noch nicht publish-ready" in text
    assert "keine Rechtsberatung" in text.lower() or "Rechtsberatung" in text


def test_factory_build_writes_legal_and_footer_links(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Zahnarztpraxis Mueller in Koeln. Prophylaxe und Implantate.",
        client_legal={
            "owner_name": "Dr. Anna Mueller",
            "street": "Hauptstr. 1",
            "zip": "50667",
            "city": "Koeln",
            "email": "praxis@mueller-zahn.de",
            "phone": "+49 221 555",
            "legal_form": "Einzelunternehmen",
            "uses_maps": True,
        },
    )
    product_dir = tmp_path / "sandbox" / product["product_id"]
    index = (product_dir / "index.html").read_text(encoding="utf-8")
    assert "impressum.html" in index
    assert "datenschutz.html" in index
    impressum = (product_dir / "impressum.html").read_text(encoding="utf-8")
    assert "Dr. Anna Mueller" in impressum
    assert "Hauptstr. 1" in impressum
    assert "Noch nicht publish-ready" not in impressum
    datenschutz = (product_dir / "datenschutz.html").read_text(encoding="utf-8")
    assert "Google Maps" in datenschutz
    meta = product_dir / "meta.json"
    assert meta.is_file()
    import json

    data = json.loads(meta.read_text(encoding="utf-8"))
    assert data.get("publish_ready_de") is True
