"""R2.2c — Premium Interactions: light CSS/vanilla motion only."""

from __future__ import annotations

from pathlib import Path

from app.factory.analyzer import analyze
from app.factory.css_motion import write_motion_assets
from app.factory.factory_service import FactoryService
from app.factory.landing_builder import build_landing_html
from app.factory.package_features import resolve_package_features


def test_motion_kit_has_reduced_motion_and_premium_hooks():
    root = Path(__file__).resolve().parents[1] / "app" / "factory" / "assets"
    css = (root / "motion_kit.css").read_text(encoding="utf-8")
    js = (root / "reveal.js").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in css
    assert "hero-parallax" in css
    assert "vcFaqIn" in css or "faq-acc" in css
    assert "prefers-reduced-motion" in js
    assert "parallax" in js.lower() or "--parallax-y" in js
    assert "runCounter" in js or "data-vc-counted" in js
    # No heavy libs
    assert "gsap" not in js.lower()
    assert "framer" not in js.lower()
    assert "three" not in js.lower()
    assert "jquery" not in js.lower()


def test_business_landing_wires_parallax_and_motion_attr():
    html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        motion_level="css",
    )
    assert 'data-motion="css"' in html
    assert "hero-parallax" in html
    assert "motion_kit.css" in html
    assert "reveal.js" in html
    assert " class=\"section reveal\"" in html or 'class="section reveal"' in html


def test_basic_stays_without_forced_premium_motion():
    html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("basic"),
        motion_level="none",
    )
    assert 'data-motion="none"' in html
    assert "hero-parallax" not in html
    assert "motion_kit.css" not in html


def test_factory_copies_updated_motion_assets(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Zahnarztpraxis Mueller in Koeln. Prophylaxe.",
        package_id="business",
        client_legal={
            "owner_name": "Dr. Test",
            "street": "Hauptstr. 1",
            "zip": "50667",
            "city": "Koeln",
            "email": "a@b.de",
        },
    )
    assert product.get("motion_level") == "css"
    kit = (tmp_path / "sandbox" / product["product_id"] / "assets" / "motion_kit.css").read_text(
        encoding="utf-8"
    )
    js = (tmp_path / "sandbox" / product["product_id"] / "assets" / "reveal.js").read_text(
        encoding="utf-8"
    )
    assert "prefers-reduced-motion" in kit
    assert "hero-parallax" in kit
    assert "prefers-reduced-motion" in js


def test_write_motion_assets_is_static_copy(tmp_path: Path):
    written = write_motion_assets(tmp_path)
    assert written == ["assets/motion_kit.css", "assets/reveal.js"]
    assert (tmp_path / "assets" / "reveal.js").is_file()
