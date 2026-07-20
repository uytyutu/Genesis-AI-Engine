"""CatalogManager CRUD + shop-niche resolve."""

from __future__ import annotations

from pathlib import Path

from app.factory.catalog_manager import CatalogManager, is_shop_niche


def test_shop_niche_allowlist() -> None:
    assert is_shop_niche("energy")
    assert is_shop_niche("beauty")
    assert not is_shop_niche("dental")
    assert not is_shop_niche("auto")
    assert not is_shop_niche("law")


def test_catalog_crud_import_delete(tmp_path: Path) -> None:
    mgr = CatalogManager(tmp_path / "catalog")
    mgr.import_catalog(
        {
            "version": 1,
            "mode": "catalog",
            "niche_id": "energy",
            "currency": "EUR",
            "categories": [{"id": "pv", "label": "Solar"}],
            "products": [
                {
                    "sku": "solar_panel",
                    "name": "SolarPanel 400W",
                    "category_id": "pv",
                    "price": 189,
                    "summary": "PV",
                    "cta": "buy",
                    "3d_model_enabled": True,
                    "vxp_product_id": "solar_panel",
                }
            ],
        }
    )
    loaded = mgr.load()
    assert len(loaded.products) == 1
    assert loaded.products[0].cta == "request"  # Layer A: buy → request
    assert loaded.products[0].three_d_model_enabled is True
    assert loaded.products[0].content_type == "product"

    mgr.upsert_product(
        "inverter",
        {
            "name": "Inverter",
            "category_id": "power",
            "price": 890,
            "summary": "WR",
        },
    )
    assert len(mgr.load().products) == 2
    assert mgr.delete_product("inverter") is True
    assert len(mgr.load().products) == 1


def test_resolve_dental_is_none(tmp_path: Path) -> None:
    mgr = CatalogManager(tmp_path / "catalog")
    assert mgr.resolve_for_build("dental", "business") is None


def test_resolve_energy_seeds_solar_and_inverter(tmp_path: Path) -> None:
    mgr = CatalogManager(tmp_path / "catalog")
    view = mgr.resolve_for_build("energy", "business", seed_if_missing=True)
    assert view is not None
    skus = {p.sku for p in view.products}
    assert "solar_panel" in skus
    assert "inverter" in skus
    assert view.search and view.filters and view.request_cart
    assert not view.rich_cards
    solar = next(p for p in view.products if p.sku == "solar_panel")
    assert solar.three_d_model_enabled is True
    assert "hotspots" in solar.vxp_hotspots_ref
    assert (tmp_path / "catalog" / "catalog.json").is_file()
    assert (tmp_path / "catalog" / "products" / "solar_panel.json").is_file()


def test_premium_rich_cards(tmp_path: Path) -> None:
    mgr = CatalogManager(tmp_path / "catalog")
    view = mgr.resolve_for_build("energy", "premium")
    assert view is not None
    assert view.rich_cards is True
    assert view.mode == "storefront"
