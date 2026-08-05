"""AI Store R2 — factory generation, quality gate, versions, publish."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.factory.store_factory import StoreFactoryService
from app.factory.store_factory.quality import run_shop_quality_gate
from app.integration.sales_order_service import SalesOrderService
from app.integration.shop_brief import SHOP_PIPELINE_PUBLISHED, validate_shop_brief


class _Factory:
    def submit(self, intent):  # noqa: ANN001
        return {"product_id": "prod-shop"}

    class _Inner:
        def get_product(self, product_id: str):  # noqa: ANN001
            return {"id": product_id}

    _factory = _Inner()


def _brief(**over):
    base = {
        "company_name": "Demo GmbH",
        "store_name": "Nordic Boots",
        "what_is_sold": "Outdoor boots and bags",
        "category": "clothing",
        "catalog_size": "100",
        "languages": ["de"],
        "currency": "EUR",
        "payments": ["stripe"],
        "shipping": ["dhl"],
        "pages": ["home", "catalog", "pdp", "about", "contact", "legal", "returns"],
        "style": "modern",
    }
    base.update(over)
    return base


def _paid_shop(tmp_path: Path) -> tuple[SalesOrderService, str]:
    sales = SalesOrderService(tmp_path, _Factory())
    created = sales.create_order(
        {
            "business_name": "Nordic Boots",
            "email": "shop@test.local",
            "package_id": "ecommerce_shop",
            "description": "Outdoor boots and bags",
            "customer_id": "cust-r2-1",
            "shop_brief": _brief(),
        }
    )
    order_id = created["order_id"]
    order = sales.get_order(order_id)
    assert order is not None
    order["status"] = "paid"
    order["paid_at"] = "2026-08-04T10:00:00+00:00"
    sales._save_order(order)  # noqa: SLF001
    return sales, order_id


def test_paid_pipeline_reaches_published(tmp_path: Path):
    sales, order_id = _paid_shop(tmp_path)
    result = sales.start_shop_pipeline(order_id)
    assert result["ok"] is True
    assert result["shop_pipeline"] == SHOP_PIPELINE_PUBLISHED
    assert result["product_id"]
    assert result["published_url"]
    assert result["factory_hook"]["status"] == "completed"

    order = sales.get_order(order_id)
    assert order is not None
    assert order["shop_pipeline"] == SHOP_PIPELINE_PUBLISHED
    product_id = str(order["product_id"])
    index = tmp_path / "sandbox" / product_id / "index.html"
    assert index.is_file()
    html = index.read_text(encoding="utf-8")
    assert "Nordic Boots" in html
    assert "clothing" in html.lower() or "Outdoor" in html

    again = sales.enqueue_shop_factory(order_id)
    assert again["shop_pipeline"] == SHOP_PIPELINE_PUBLISHED
    assert again["product_id"] == product_id


def test_quality_gate_pass(tmp_path: Path):
    brief = validate_shop_brief(_brief())
    factory = StoreFactoryService(tmp_path)
    order = {
        "order_id": "ord-qg",
        "business_name": "Nordic Boots",
        "shop_brief": brief,
        "market_code": "DE",
    }
    gen = factory.generate_from_order(order)
    assert gen["ok"] is True
    product_dir = tmp_path / "sandbox" / gen["product_id"]
    q = run_shop_quality_gate(
        product_dir,
        brief=brief,
        colors={"accent": "#c45c26"},
    )
    assert q.passed is True, q.errors
    assert (product_dir / "cart.html").is_file()
    assert (product_dir / "assets" / "store.js").is_file()
    css = (product_dir / "assets" / "store.css").read_text(encoding="utf-8")
    assert "--store-bg" in css
    assert not re.search(r"--store-bg\s*:\s*#fff(?:fff)?\s*;", css, re.I)
    catalog = (product_dir / "catalog.html").read_text(encoding="utf-8")
    assert 'data-action="add-cart"' in catalog
    assert 'data-action="buy-now"' in catalog
    assert 'id="nav-drawer"' in catalog
    assert 'data-cart-badge' in catalog


def test_r21_premium_markers(tmp_path: Path):
    brief = validate_shop_brief(_brief(market_code="DE"))
    factory = StoreFactoryService(tmp_path)
    gen = factory.generate_from_order(
        {
            "order_id": "ord-r21",
            "business_name": "Nordic Boots",
            "shop_brief": brief,
            "market_code": "DE",
        }
    )
    assert gen["ok"] is True
    root = tmp_path / "sandbox" / gen["product_id"]
    index = (root / "index.html").read_text(encoding="utf-8")
    assert 'id="new-arrivals"' in index
    assert 'id="reviews"' in index
    assert "review-card" in index
    assert "Neuheiten" in index or "New arrivals" in index
    assert "Kundenstimmen" in index or "Customer reviews" in index
    assert "Empfohlen" in index or "Featured" in index
    assert "Kategorien" in index or "Categories" in index
    assert 'class="brand" href="index.html"' in index
    assert 'lang="de"' in index
    catalog = (root / "catalog.html").read_text(encoding="utf-8")
    assert "In den Warenkorb" in catalog
    assert "Jetzt kaufen" in catalog
    js = (root / "assets" / "store.js").read_text(encoding="utf-8")
    assert "store_cart_v1" in js
    assert "Zum Warenkorb hinzugefügt" in js
    cart = (root / "cart.html").read_text(encoding="utf-8")
    assert "Warenkorb" in cart
    assert "Zur Kasse" in cart
    assert "localStorage" in cart or "Demo" in cart or "demo" in cart.lower()
    assert 'id="wish-lines"' in cart
    assert 'id="wishlist"' in cart
    assert 'href="cart.html#wishlist"' in index
    assert 'class="mobile-bar"' in index
    assert 'data-id="header"' not in index
    js = (root / "assets" / "store.js").read_text(encoding="utf-8")
    assert "renderWishPage" in js
    assert "catalog.html?q=" in js


def test_warm_backgrounds_all_niches():
    from app.factory.store_factory.templates import StoreTemplateRegistry, _CATEGORY_THEMES

    pure = {"#fff", "#ffffff", "white"}
    for cat, theme in _CATEGORY_THEMES.items():
        assert theme.background.strip().lower() not in pure, cat
        assert theme.surface.strip().lower() not in pure, cat
    reg = StoreTemplateRegistry()
    for cat in _CATEGORY_THEMES:
        resolved = reg.resolve({"category": cat, "style": "minimal", "currency": "EUR"})
        assert resolved.colors["background"].strip().lower() not in pure
        assert resolved.colors["surface"].strip().lower() not in pure


def test_ownership_store_actions(tmp_path: Path):
    sales, order_id = _paid_shop(tmp_path)
    sales.start_shop_pipeline(order_id)

    store = sales.get_store_for_customer(
        order_id, customer_id="cust-r2-1", email="shop@test.local"
    )
    assert store["shop_pipeline"] == SHOP_PIPELINE_PUBLISHED
    assert store["published_url"]
    assert store["version"] == 1
    assert store["generation_log"]

    with pytest.raises(ValueError, match="forbidden"):
        sales.regenerate_shop_store(
            order_id, customer_id="other", email="x@y.z"
        )

    with pytest.raises(ValueError, match="forbidden"):
        sales.get_store_status_for_customer(
            order_id, customer_id="other", email="x@y.z"
        )


def test_regenerate_bumps_version_and_rollback(tmp_path: Path):
    sales, order_id = _paid_shop(tmp_path)
    sales.start_shop_pipeline(order_id)

    regen = sales.regenerate_shop_store(
        order_id, customer_id="cust-r2-1", email="shop@test.local"
    )
    assert regen["ok"] is True
    assert regen["version"] == 2

    store = sales.get_store_for_customer(
        order_id, customer_id="cust-r2-1", email="shop@test.local"
    )
    assert store["version"] == 2
    assert len(store["versions"]) >= 2

    rolled = sales.rollback_shop_store(
        order_id, version=1, customer_id="cust-r2-1", email="shop@test.local"
    )
    assert rolled["version"] == 1
    store2 = sales.get_store_for_customer(
        order_id, customer_id="cust-r2-1", email="shop@test.local"
    )
    assert store2["version"] == 1

    html, _order = sales.get_store_live_html(order_id)
    assert "Nordic Boots" in html
