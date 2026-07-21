"""R3.2 — Section-Aware Media Gate (no LLM)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.factory.analyzer import analyze
from app.factory.hero_pack import resolve_slot
from app.factory.media_gate import (
    evaluate_section_media,
    media_fits_section,
    tags_for_media,
)
from app.factory.media_intelligence import finalize_product_media, pick_niche_hero
from app.factory.factory_service import FactoryService


_SHOWCASES = Path(__file__).resolve().parents[1] / "_research_3d" / "showcases"


def test_beauty_rejects_restaurant_tags():
    check = evaluate_section_media(
        niche_id="beauty",
        section="hero",
        tags=frozenset({"restaurant", "interior"}),
        path="x.jpg",
    )
    assert not check.ok
    assert "denied" in check.detail


def test_computer_rejects_florist_tags():
    check = evaluate_section_media(
        niche_id="computer",
        section="hero",
        tags=frozenset({"florist", "retail", "interior"}),
        path="x.jpg",
    )
    assert not check.ok


def test_green_rejects_cosmetics_tags():
    check = evaluate_section_media(
        niche_id="green",
        section="hero",
        tags=frozenset({"cosmetics", "salon"}),
        path="x.jpg",
    )
    assert not check.ok


def test_generic_preview_fails_computer_hero():
    preview = _SHOWCASES / "generic" / "preview.jpg"
    if not preview.is_file():
        pytest.skip("generic preview missing")
    assert not media_fits_section(
        preview, niche_id="computer", section="hero", source="niche"
    )
    assert not media_fits_section(
        preview, niche_id="beauty", section="hero", source="niche"
    )


def test_niche_owned_heroes_pass():
    for niche in ("beauty", "computer", "green", "dental", "auto", "law"):
        hero = resolve_slot(niche, "business", "hero_1")
        if hero is None or not hero.is_file():
            continue
        # Skip if resolve fell through to generic (wrong ownership)
        tags = tags_for_media(hero, source="niche", niche_id=niche)
        if "retail" in tags or "florist" in tags:
            continue
        assert media_fits_section(
            hero, niche_id=niche, section="hero", source="niche"
        ), f"{niche} hero should pass Media Gate"


def test_pick_niche_hero_never_returns_denied_generic():
    for niche in ("beauty", "computer", "green"):
        picked = pick_niche_hero(
            niche_id=niche,
            package_id="business",
            market_code="DE",
            business_name=f"Test {niche}",
        )
        assert picked is not None, f"{niche} must have a Media Gate–passing hero"
        assert media_fits_section(
            picked, niche_id=niche, section="hero", source="niche"
        )


def test_analyzer_detects_de_niches():
    assert analyze("Salon Mira Berlin — Haarschnitt, Farbe, Pflege").niche == "beauty"
    assert analyze("PC-Service Neon — Reparatur, Netzwerke in Düsseldorf").niche == "computer"
    assert analyze("Gartenpflege Grün GmbH — Rasen, Hecken, Pflege in Stuttgart").niche == "green"
    assert analyze("Trattoria Luna — Restaurant und Pizza in München").niche == "restaurant"


def test_finalize_media_gate_fields(tmp_path: Path):
    product = tmp_path / "p"
    (product / "assets").mkdir(parents=True)
    plan = finalize_product_media(
        product,
        niche_id="beauty",
        market_code="DE",
        package_id="business",
        business_name="Salon Mira",
        hero_from_client=False,
        gallery_rels=[],
    )
    assert plan.hero_ok is True
    assert plan.media_gate_ok is True
    assert plan.gate_ok is True
    assert plan.media_gate is not None


def test_factory_beauty_passes_media_gate(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Salon Mira Berlin — Haarschnitt, Farbe, Pflege.",
        package_id="business",
        market_code="DE",
        client_legal={
            "owner_name": "Mira Test",
            "street": "Friedrichstr. 1",
            "zip": "10117",
            "city": "Berlin",
            "email": "a@b.de",
        },
    )
    assert product["niche"] == "beauty"
    pid = product["product_id"]
    meta_path = tmp_path / "sandbox" / pid / "meta.json"
    import json

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta.get("media_plan", {}).get("media_gate_ok") is True
    data, name = factory.build_client_delivery_zip(pid)
    assert name.endswith(".zip")
    assert len(data) > 500
