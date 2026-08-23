"""Website preview + shop catalog media URL materialization."""

from __future__ import annotations

from pathlib import Path

from app.factory.factory_service import FactoryService
from app.factory.store_factory.service import StoreFactoryService
from app.integration.store_admin.shop_live_sync import (
    materialize_catalog_images,
    sync_catalog_to_storefront,
)
from app.portal.website_catalog import default_factory_sandbox_dirs
from app.security import is_public_api_path, production_api_allowed


def test_factory_preview_asset_child_path_is_public():
    """Regression: Security Gate must allow preview/assets/* (not only exact /preview)."""
    html = "/api/factory/products/prod-lorenne/preview"
    asset = "/api/factory/products/prod-lorenne/preview/assets/hero.webp"
    nested = "/api/factory/products/prod-lorenne/preview/assets/virtus-owner/logo.png"
    assert is_public_api_path(html, "GET")
    assert production_api_allowed(html, "GET")
    assert is_public_api_path(asset, "GET")
    assert production_api_allowed(asset, "GET")
    assert is_public_api_path(nested, "GET")
    assert production_api_allowed(nested, "GET")
    # Do not widen factory internals
    assert not is_public_api_path("/api/factory/products", "GET")
    assert not is_public_api_path("/api/factory/products/prod-lorenne", "GET")
    assert not is_public_api_path(asset, "POST")


def test_rewrite_preview_html_rewrites_relative_assets():
    html = (
        "<html><head></head><body>"
        '<img src="assets/hero.jpg" />'
        '<link rel="stylesheet" href="assets/theme.css" />'
        "<style>.x{background:url(./assets/bg.webp)}</style>"
        "</body></html>"
    )
    out = FactoryService.rewrite_preview_html(html, "prod-demo")
    assert 'src="/api/factory/products/prod-demo/preview/assets/hero.jpg"' in out
    assert 'href="/api/factory/products/prod-demo/preview/assets/theme.css"' in out
    assert "/api/factory/products/prod-demo/preview/assets/bg.webp" in out
    assert 'base href="/api/factory/products/prod-demo/preview/"' in out


def test_rewrite_live_html_rewrites_css_urls():
    html = (
        "<html><head></head><body>"
        '<img src="assets/products/p01.jpg" />'
        "<style>.x{background:url('../lorenne/assets/x.jpg')}</style>"
        "</body></html>"
    )
    out = StoreFactoryService.rewrite_live_html(html, "ord-1")
    assert 'src="/api/client/stores/ord-1/live/assets/products/p01.jpg"' in out
    # ../lorenne/assets from document root normalizes under live base
    assert "/api/client/stores/ord-1/live/lorenne/assets/x.jpg" in out
    assert 'base href="/api/client/stores/ord-1/live/"' in out


def test_materialize_catalog_images_copies_into_storefront(tmp_path: Path):
    media = tmp_path / "media"
    src_dir = media / "ord-1" / "prd-1"
    src_dir.mkdir(parents=True)
    src = src_dir / "img-abc.webp"
    src.write_bytes(b"webp-bytes")
    storefront = tmp_path / "shop"
    storefront.mkdir()
    (storefront / "index.html").write_text(
        '<html><body><div class="grid" id="grid"></div></body></html>',
        encoding="utf-8",
    )
    products = [
        {
            "id": "prd-1",
            "title": "Test",
            "price": 10,
            "status": "active",
            "images": [
                {
                    "id": "img-abc",
                    "path": "ord-1/prd-1/img-abc.webp",
                }
            ],
        }
    ]
    out = materialize_catalog_images(storefront, products, media)
    assert out[0]["images"][0]["storefront_path"] == "assets/catalog/img-abc.webp"
    assert (storefront / "assets" / "catalog" / "img-abc.webp").read_bytes() == b"webp-bytes"
    sync = sync_catalog_to_storefront(storefront, products, media_root=media)
    assert sync["ok"] is True
    html = (storefront / "index.html").read_text(encoding="utf-8")
    assert "assets/catalog/img-abc.webp" in html


def test_default_sandbox_includes_memory_dir(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GENESIS_MEMORY_DIR", str(tmp_path))
    roots = default_factory_sandbox_dirs()
    assert any(r == tmp_path / "sandbox" for r in roots)
