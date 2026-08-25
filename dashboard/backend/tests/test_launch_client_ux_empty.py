"""Launch Client UX — purchase routes + empty/owned SSOT (frontend constants)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "frontend" / "app"


def test_launch_purchase_routes_exist_in_client_page():
    page = (ROOT / "client" / "page.tsx").read_text(encoding="utf-8")
    lib = (ROOT / "lib" / "launchClientUx.ts").read_text(encoding="utf-8")
    assert 'website: "/order?form=1"' in lib
    assert 'shop: "/order/shop"' in lib
    assert 'ai: "/order/bot"' in lib
    assert "Noch kein Produkt aktiviert" in page
    assert "Vector kennenlernen" in page
    assert "ab 299 €" in lib
    assert "LAUNCH_PURCHASE_ROUTES" in page


def test_order_route_pages_exist():
    assert (ROOT / "order" / "page.tsx").is_file()
    assert (ROOT / "order" / "shop" / "page.tsx").is_file()
    assert (ROOT / "order" / "bot" / "page.tsx").is_file()


def test_website_price_hint_ssot_299():
    catalog = (ROOT / "lib" / "bccModuleCatalog.ts").read_text(encoding="utf-8")
    assert 'priceHint: "Ab 299 €"' in catalog
    assert "Ab 199 €" not in catalog


def test_coming_soon_label_is_demnaechst():
    status = (ROOT / "lib" / "clientProductStatus.ts").read_text(encoding="utf-8")
    assert 'coming_soon: "Demnächst"' in status
    assert 'label: "Demnächst"' in status
