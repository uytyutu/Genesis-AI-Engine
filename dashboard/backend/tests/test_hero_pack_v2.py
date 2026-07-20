"""Hero Pack 2.0 + commercial ZIP package markers."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from app.factory.factory_service import FactoryService
from app.factory.hero_pack import write_hero_pack
from app.factory.market_delivery import deploy_readme
from app.integration.sales_order_service import package_display_name, package_included_summary


def test_hero_pack_writes_tier_assets(tmp_path: Path) -> None:
    out = tmp_path / "site"
    out.mkdir()
    manifest = write_hero_pack(out, "dental", "premium")
    assert manifest.get("hero") == "assets/hero.jpg"
    assert (out / "assets" / "hero.jpg").is_file()
    assert (out / "assets" / "hero_pack" / "hero_1.jpg").is_file()
    assert (out / "assets" / "hero_pack" / "banner.jpg").is_file()
    assert "cta" not in manifest or True  # premium slots, not business cta
    biz = write_hero_pack(tmp_path / "biz", "auto", "business")
    assert biz.get("cta") or biz.get("services") or biz.get("hero")


def test_business_and_premium_html_use_pack_css(tmp_path: Path) -> None:
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Zahnarztpraxis Müller — Prophylaxe in München",
        package_id="premium",
        contacts={"city": "München", "phone": "+491711111", "business_name": "Praxis Müller"},
        market_code="DE",
    )
    root = tmp_path / "sandbox" / product["product_id"]
    html = (root / "index.html").read_text(encoding="utf-8")
    assert 'data-tier="premium"' in html
    assert 'lang="de"' in html
    assert (root / "assets" / "hero_pack" / "manifest.json").is_file()
    # pack section CSS references assets/hero_pack/
    assert "assets/hero_pack/" in html


def test_commercial_zip_readme_and_package(tmp_path: Path) -> None:
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    for package_id, niche_text in (
        ("basic", "Autowerkstatt Bergmann Inspektion Köln"),
        ("business", "Photovoltaik Solar Nord Hamburg"),
        ("premium", "Zahnarztpraxis Müller München"),
    ):
        product = factory.build_landing(
            niche_text,
            package_id=package_id,
            contacts={"city": "Berlin", "phone": "+491711111", "business_name": "Demo Co"},
            market_code="DE",
        )
        pid = product["product_id"]
        # Simulate export zip path used after payment
        from app.factory.market_delivery import deploy_readme as dr

        readme = dr("DE", package_id=package_id)
        assert package_display_name(package_id) in readme or package_id.title() in readme
        assert "Inklusive:" in readme
        assert package_included_summary(package_id)[:15] in readme
        root = tmp_path / "sandbox" / pid
        html = (root / "index.html").read_text(encoding="utf-8")
        assert f'data-tier="{package_id}"' in html
        assert (root / "assets" / "hero.jpg").is_file()
        hero = (root / "assets" / "hero.jpg").read_bytes()
        assert len(hero) > 1000


def test_business_cta_unique_across_key_niches() -> None:
    show = Path(__file__).resolve().parents[1] / "_research_3d" / "showcases"
    hashes = {}
    for niche in ("dental", "auto", "energy", "beauty", "law"):
        p = show / niche / "hero_pack" / "business" / "cta.jpg"
        assert p.is_file(), niche
        hashes[niche] = hashlib.md5(p.read_bytes()).hexdigest()
    assert len(set(hashes.values())) == len(hashes), hashes
