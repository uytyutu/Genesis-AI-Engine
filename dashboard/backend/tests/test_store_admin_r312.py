"""Store Admin R3.1.2 — product catalog service."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import UploadFile

from app.integration.store_admin.catalog_service import StoreCatalogService
from app.integration.store_admin.ai_assist import generate_product_fields


def _png_bytes() -> bytes:
    # Minimal 1x1 PNG
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
    )


def test_crud_and_status(tmp_path: Path):
    svc = StoreCatalogService(tmp_path)
    created = svc.create_product(
        "ord-1",
        {
            "title": "Trail Boots",
            "price": 129.5,
            "status": "draft",
            "category": "Footwear",
            "variants": {"size": ["42", "43"], "color": ["Black"], "weight": "1.2 kg"},
            "seo": {"title": "Trail Boots SEO", "slug": "Trail Boots!"},
        },
    )
    pid = created["product"]["id"]
    assert created["product"]["seo"]["slug"] == "trail-boots"
    assert created["product"]["variants"]["size"] == ["42", "43"]

    listed = svc.list_products("ord-1")
    assert listed["count"] == 1
    assert listed["active_product_types"] == ["physical"]

    updated = svc.update_product(
        "ord-1",
        pid,
        {"status": "published", "stock_qty": 8, "stock_status": "in_stock"},
    )
    assert updated["product"]["status"] == "published"
    assert updated["product"]["stock_qty"] == 8

    pub = svc.list_products("ord-1", status="published")
    assert pub["count"] == 1

    deleted = svc.delete_product("ord-1", pid)
    assert deleted["deleted"] == pid
    assert svc.list_products("ord-1")["count"] == 0


def test_bulk_actions(tmp_path: Path):
    svc = StoreCatalogService(tmp_path)
    a = svc.create_product("ord-2", {"title": "A", "price": 10})["product"]["id"]
    b = svc.create_product("ord-2", {"title": "B", "price": 20})["product"]["id"]
    svc.bulk(
        "ord-2",
        {"action": "set_category", "product_ids": [a, b], "category": "Outdoor"},
    )
    svc.bulk(
        "ord-2",
        {"action": "set_price", "product_ids": [a], "price": 15.5},
    )
    svc.bulk(
        "ord-2",
        {"action": "set_status", "product_ids": [a, b], "status": "published"},
    )
    rows = {p["id"]: p for p in svc.list_products("ord-2")["products"]}
    assert rows[a]["category"] == "Outdoor"
    assert rows[a]["price"] == 15.5
    assert rows[b]["status"] == "published"
    svc.bulk("ord-2", {"action": "delete", "product_ids": [a, b]})
    assert svc.list_products("ord-2")["count"] == 0


def test_media_reorder_and_primary(tmp_path: Path):
    svc = StoreCatalogService(tmp_path)
    pid = svc.create_product("ord-3", {"title": "Bag"})["product"]["id"]
    uploads = []
    for name in ("a.png", "b.png"):
        uploads.append(
            UploadFile(filename=name, file=BytesIO(_png_bytes()))
        )
    after = svc.add_images("ord-3", pid, uploads)
    images = after["product"]["images"]
    assert len(images) == 2
    assert images[0]["is_primary"] is True

    ids = [images[1]["id"], images[0]["id"]]
    reordered = svc.update_images(
        "ord-3",
        pid,
        {"image_ids": ids, "primary_image_id": images[1]["id"]},
    )
    imgs = reordered["product"]["images"]
    assert imgs[0]["id"] == images[1]["id"]
    assert imgs[0]["is_primary"] is True

    path = svc.resolve_media("ord-3", imgs[0]["id"])
    assert path.is_file()


def test_ai_generate_fields():
    out = generate_product_fields(
        hint="leather hiking boots, waterproof",
        store_name="Nordlicht",
        store_category="clothing",
        language="en",
        product_type="physical",
    )
    assert out["title"]
    assert out["seo"]["slug"]
    assert out["variants"]["size"]
    assert "Nordlicht" in out["seo"]["title"]


def test_product_types_reserved(tmp_path: Path):
    svc = StoreCatalogService(tmp_path)
    created = svc.create_product(
        "ord-4",
        {"title": "E-book", "product_type": "digital", "price": 9},
    )
    assert created["product"]["product_type"] == "digital"
    with pytest.raises(ValueError, match="invalid_product_type"):
        svc.create_product("ord-4", {"title": "X", "product_type": "spaceship"})
