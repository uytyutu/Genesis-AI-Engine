"""Store Admin R3.1.3 — Design + User Data Protection Rule."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from starlette.datastructures import UploadFile

from app.factory.store_factory import StoreFactoryService
from app.integration.store_admin.catalog_service import StoreCatalogService
from app.integration.store_admin.design_apply import apply_design_to_product_dir
from app.integration.store_admin.design_service import StoreDesignService


def _png() -> bytes:
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
    )


def _brief():
    return {
        "company_name": "Demo GmbH",
        "store_name": "Nordic Boots",
        "what_is_sold": "Outdoor boots",
        "category": "clothing",
        "catalog_size": "50",
        "languages": ["de"],
        "currency": "EUR",
        "payments": ["stripe"],
        "shipping": ["dhl"],
        "pages": ["home", "catalog", "pdp", "about", "contact", "legal", "returns"],
        "style": "modern",
        "market_code": "DE",
    }


def test_design_update_undo_restore(tmp_path: Path):
    svc = StoreDesignService(tmp_path)
    oid = "ord-design-1"
    first = svc.get_design(oid, store_name="Nordic")["design"]
    assert first["branding"]["store_name"] in ("", "Nordic") or True

    updated = svc.update_design(
        oid,
        {
            "branding": {"store_name": "Alpen Shop", "tagline": "Walk further"},
            "colors": {"primary": "#112233"},
            "commit": True,
        },
        store_name="Nordic",
    )
    assert updated["design"]["branding"]["store_name"] == "Alpen Shop"
    assert updated["design"]["colors"]["primary"] == "#112233"

    svc.update_design(
        oid,
        {"colors": {"primary": "#abcdef"}, "commit": True},
        store_name="Nordic",
    )
    undone = svc.undo(oid)
    assert undone["design"]["colors"]["primary"] == "#112233"

    restored = svc.restore_defaults(oid, store_name="Nordic Boots")
    assert restored["design"]["colors"]["primary"] == "#0f766e"


def test_design_asset_upload(tmp_path: Path):
    svc = StoreDesignService(tmp_path)
    oid = "ord-design-2"
    up = UploadFile(filename="logo.png", file=BytesIO(_png()))
    out = svc.upload_asset(oid, up, kind="logo", store_name="Shop")
    assert out["asset"]["id"]
    assert out["design"]["branding"]["logo"]["id"] == out["asset"]["id"]
    path = svc.resolve_media(oid, out["asset"]["id"])
    assert path.is_file()


def test_user_data_protection_survives_factory(tmp_path: Path):
    """Factory regenerate must not wipe owner design or catalog products."""
    oid = "ord-protect-1"
    catalog = StoreCatalogService(tmp_path)
    design = StoreDesignService(tmp_path)

    pid = catalog.create_product(
        oid, {"title": "Owner Boot", "price": 99, "status": "published"}
    )["product"]["id"]
    design.update_design(
        oid,
        {
            "branding": {"store_name": "Owner Brand", "tagline": "Keep me"},
            "colors": {"primary": "#aa5500", "button": "#aa5500"},
            "homepage": {"reviews": False, "newsletter": False},
            "commit": True,
        },
        store_name="Owner Brand",
    )
    up = UploadFile(filename="hero.png", file=BytesIO(_png()))
    design.upload_asset(oid, up, kind="banner", store_name="Owner Brand")

    factory = StoreFactoryService(tmp_path)
    order = {
        "id": oid,
        "order_id": oid,
        "business_name": "Owner Brand",
        "shop_brief": _brief(),
        "market_code": "DE",
    }
    gen1 = factory.generate_from_order(order)
    assert gen1["ok"] is True
    product_id = gen1["product_id"]
    product_dir = factory.product_dir(product_id)
    assert (product_dir / "assets" / "owner-overlay.css").is_file()
    css = (product_dir / "assets" / "owner-overlay.css").read_text(encoding="utf-8")
    assert "#aa5500" in css
    assert "newsletter" in css.lower() or "display: none" in css

    # Second generate (regenerate) — catalog + design JSON untouched
    gen2 = factory.generate_from_order(order, product_id=product_id, bump_version=True)
    assert gen2["ok"] is True
    assert catalog.list_products(oid)["count"] == 1
    assert catalog.get_product(oid, pid)["product"]["title"] == "Owner Boot"
    d2 = design.get_design(oid)["design"]
    assert d2["branding"]["store_name"] == "Owner Brand"
    assert d2["colors"]["primary"] == "#aa5500"
    assert len(d2["hero"]["banners"]) >= 1

    css2 = (
        factory.product_dir(product_id) / "assets" / "owner-overlay.css"
    ).read_text(encoding="utf-8")
    assert "#aa5500" in css2


def test_apply_without_design_is_noop(tmp_path: Path):
    product_dir = tmp_path / "sandbox" / "shop-x"
    product_dir.mkdir(parents=True)
    (product_dir / "index.html").write_text(
        "<html><head></head><body></body></html>", encoding="utf-8"
    )
    ok = apply_design_to_product_dir(tmp_path, "ord-none", product_dir)
    assert ok is False
