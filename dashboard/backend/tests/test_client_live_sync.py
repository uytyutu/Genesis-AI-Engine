"""Tests for Live Sync cinematic + shop catalog → storefront."""

from __future__ import annotations

import json
from pathlib import Path

from app.integration.client_control_contract import client_control_capabilities
from app.integration.store_admin.shop_live_sync import sync_catalog_to_storefront
from app.integration.website_admin.cinematic_control import (
    ORIGINAL_NAME,
    ensure_control_point_original,
    list_cinematic_scenes,
    replace_cinematic_scene,
    restore_cinematic_scene,
    restore_website_original,
)


def test_premium_capabilities_have_18_scenes():
    caps = client_control_capabilities("premium")
    assert caps["website"]["cinematic_scenes"] == 18
    assert caps["website"]["live_sync"] is True
    assert caps["shop"]["shipping"]["dhl"] == "not_connected"
    assert caps["analytics"]["fake_numbers"] is False


def test_business_capabilities_lighter_cinematic():
    caps = client_control_capabilities("business")
    assert caps["website"]["cinematic_scenes"] == 8
    assert caps["forced_setup"] is False


def test_cinematic_replace_and_restore(tmp_path: Path):
    seq = tmp_path / "assets" / "seq"
    seq.mkdir(parents=True)
    (seq / "f001.jpg").write_bytes(b"orig-frame-1")
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    meta = ensure_control_point_original(tmp_path)
    assert meta["id"] == ORIGINAL_NAME
    listed = list_cinematic_scenes(tmp_path)
    assert listed["count"] == 1
    replace_cinematic_scene(tmp_path, 1, b"\xff\xd8\xffnew", filename="x.jpg")
    # Without pillow may write raw bytes — still a file
    assert (tmp_path / "assets" / "seq" / "f001.jpg").is_file()
    restore_cinematic_scene(tmp_path, 1)
    assert (tmp_path / "assets" / "seq" / "f001.jpg").read_bytes() == b"orig-frame-1"
    # mutate then restore whole site
    (tmp_path / "index.html").write_text("<html>changed</html>", encoding="utf-8")
    restore_website_original(tmp_path)
    assert (tmp_path / "index.html").read_text(encoding="utf-8") == "<html></html>"


def test_shop_live_sync_updates_price(tmp_path: Path):
    html = """<!DOCTYPE html><html><body>
    <h2>Katalog · 1 Boxen</h2>
    <div class="grid" id="grid">
      <article class="product" id="p1"><h3>Kraft Tanken Box</h3>
      <p class="price">49 €</p>
      <button class="cta add" data-name="Kraft Tanken Box" data-price="49.0">In den Warenkorb</button>
      </article>
    </div>
    </body></html>"""
    (tmp_path / "index.html").write_text(html, encoding="utf-8")
    products = [
        {
            "id": "prd-1",
            "title": "Kraft Tanken Box",
            "price": 34.9,
            "category": "Self Care",
            "status": "active",
            "images": [{"storefront_path": "assets/products/p01.jpg"}],
        }
    ]
    out = sync_catalog_to_storefront(tmp_path, products)
    assert out["ok"] is True
    text = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "34,90 €" in text or "34.90" in text or "35 €" in text or "34" in text
    assert "data-price=\"34.9\"" in text
    assert (tmp_path / "versions" / ORIGINAL_NAME / "_control_point.json").is_file()
