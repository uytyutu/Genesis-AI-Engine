"""R2.1 — niche design systems make Path A landings diverge beyond recolor."""

from __future__ import annotations

from pathlib import Path

from app.factory.analyzer import analyze
from app.factory.factory_service import FactoryService
from app.factory.landing_builder import build_landing_html
from app.factory.niche_profiles import resolve_niche_profile
from app.factory.package_features import resolve_package_features


def test_niche_tokens_diverge_for_key_industries():
    dental = resolve_niche_profile("dental").style
    auto = resolve_niche_profile("auto").style
    law = resolve_niche_profile("law").style
    energy = resolve_niche_profile("energy").style
    beauty = resolve_niche_profile("beauty").style

    assert dental.primary != auto.primary
    assert dental.card_radius != auto.card_radius
    assert dental.font_display != law.font_display or dental.letter_spacing != law.letter_spacing
    assert "serif" in law.font_display.casefold()
    assert energy.surface != beauty.surface
    assert float(dental.card_radius.replace("px", "")) > float(auto.card_radius.replace("px", ""))


def test_dental_vs_auto_html_css_diverge():
    dental_html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe und Implantate."),
        features=resolve_package_features("business"),
        motion_level="css",
    )
    auto_html = build_landing_html(
        analyze("Autowerkstatt Schmidt in Berlin. Inspektion und Reifenwechsel."),
        features=resolve_package_features("business"),
        motion_level="css",
    )

    assert 'data-niche="dental"' in dental_html
    assert 'data-niche="auto"' in auto_html
    assert "Niche Design System: dental" in dental_html
    assert "Niche Design System: auto" in auto_html
    assert "--card-radius: 18px" in dental_html
    assert "--card-radius: 8px" in auto_html
    assert dental_html.split("--p:")[1].split(";")[0].strip() != auto_html.split("--p:")[1].split(";")[0].strip()
    assert "Virtus" not in dental_html
    assert "Virtus" not in auto_html
    assert "tier-switch" not in dental_html.casefold()


def test_business_default_motion_is_css(tmp_path: Path):
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
    product_dir = tmp_path / "sandbox" / product["product_id"]
    assert (product_dir / "assets" / "motion_kit.css").is_file()
    kit = (product_dir / "assets" / "motion_kit.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in kit
    index = (product_dir / "index.html").read_text(encoding="utf-8")
    assert "motion_kit.css" in index


def test_basic_stays_fast_without_forced_css_motion(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Zahnarztpraxis Mueller in Koeln. Prophylaxe.",
        package_id="basic",
    )
    assert product.get("motion_level") == "none"
