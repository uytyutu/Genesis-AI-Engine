"""Factory ZIP catalog grid for shop niches; service niches keep services-only."""

from __future__ import annotations

from pathlib import Path

from app.factory.analyzer import analyze
from app.factory.catalog_manager import CatalogManager
from app.factory.factory_service import FactoryService
from app.factory.landing_builder import build_landing_html
from app.factory.package_features import resolve_package_features


def test_energy_business_html_has_catalog_grid() -> None:
    """Catalog HTML still works when CatalogView is passed explicitly (engine kept)."""
    analysis = analyze("Solar und Photovoltaik Nord — Module und Wechselrichter in Hamburg")
    assert analysis.niche == "energy"
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        view = CatalogManager(Path(td) / "catalog").resolve_for_build("energy", "business")
        assert view is not None
        html = build_landing_html(
            analysis,
            features=resolve_package_features("business"),
            whatsapp="+491715550100",
            city="Hamburg",
            street="Hafenstraße 1",
            market_code="DE",
            catalog=view,
        )
    assert 'id="catalog"' in html
    assert "solar_panel" in html
    assert "inverter" in html
    assert "SolarPanel" in html
    assert 'id="catalog-search"' in html
    assert 'id="catalog-filter"' in html
    assert 'data-3d="true"' in html
    assert "assets/catalog.js" in html
    assert "Anfragen" in html


def test_dental_basic_has_no_catalog() -> None:
    analysis = analyze("Zahnarztpraxis Müller — Prophylaxe und Implantate in München")
    assert analysis.niche == "dental"
    html = build_landing_html(
        analysis,
        features=resolve_package_features("basic"),
        whatsapp="+491715550100",
        city="München",
        street="Maximilianstraße 1",
        market_code="DE",
        catalog=None,
    )
    assert 'id="catalog"' not in html
    assert 'id="services"' in html
    assert "assets/catalog.js" not in html


def test_factory_energy_writes_catalog_assets(tmp_path: Path) -> None:
    """Path A packages no longer auto-inject catalog — services landing only."""
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Photovoltaik Solar Nord — Module und Wechselrichter in Hamburg",
        package_id="business",
        contacts={"city": "Hamburg", "phone": "+491715550100", "business_name": "Solar Nord"},
        market_code="DE",
    )
    product_id = product["product_id"]
    root = tmp_path / "sandbox" / product_id
    html = (root / "index.html").read_text(encoding="utf-8")
    assert 'id="catalog"' not in html
    assert not (root / "assets" / "catalog.js").is_file()
    assert 'id="services"' in html


def test_factory_dental_no_catalog_dir_products(tmp_path: Path) -> None:
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Zahnarztpraxis Müller — Prophylaxe in München",
        package_id="basic",
        contacts={"city": "München", "phone": "+491715550100"},
        market_code="DE",
    )
    root = tmp_path / "sandbox" / product["product_id"]
    html = (root / "index.html").read_text(encoding="utf-8")
    assert 'id="catalog"' not in html
    assert not (root / "assets" / "catalog.js").is_file()


def test_factory_beauty_no_catalog(tmp_path: Path) -> None:
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Lash Studio Mira — Wimpernverlängerung in Hamburg",
        package_id="basic",
        contacts={"city": "Hamburg", "phone": "+491715550300", "business_name": "Lash Studio Mira"},
        market_code="DE",
    )
    root = tmp_path / "sandbox" / product["product_id"]
    html = (root / "index.html").read_text(encoding="utf-8")
    assert 'id="catalog"' not in html
    assert "Wimpern" in html or "Lash" in html
    # Trust Composer may embed process as data-trust-block or keep standalone #process
    assert (
        'id="process"' in html
        or 'data-trust-block="process"' in html
        or "process-grid" in html
    )
    assert not (root / "assets" / "catalog.js").is_file()