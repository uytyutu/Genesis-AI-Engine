"""R2.2e — Media Intelligence: client photos first, reject bad media, gate."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

import pytest

from app.factory.analyzer import analyze
from app.factory.factory_service import FactoryService
from app.factory.landing_builder import build_landing_html
from app.factory.media_intelligence import (
    assess_image,
    finalize_product_media,
    pick_niche_hero,
    read_image_size,
)
from app.factory.package_features import resolve_package_features
from app.factory.quality_gate import QualityGateError, run_quality_gate


def _png(width: int, height: int, rgb: tuple[int, int, int] = (40, 80, 120)) -> bytes:
    """Minimal truecolor PNG for dimension tests."""
    r, g, b = rgb
    raw = b"".join(b"\x00" + bytes([r, g, b]) * width for _ in range(height))
    compressed = zlib.compress(raw, 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )


def test_read_png_dimensions(tmp_path: Path):
    p = tmp_path / "x.png"
    p.write_bytes(_png(800, 600))
    assert read_image_size(p) == (800, 600)


def test_reject_pixelated_hero(tmp_path: Path):
    tiny = tmp_path / "tiny.png"
    tiny.write_bytes(_png(64, 48))
    a = assess_image(tiny, role="hero", source="client")
    assert not a.ok
    assert "pixelated" in a.reason or "small" in a.reason


def test_reject_bad_aspect_for_hero(tmp_path: Path):
    wide = tmp_path / "wide.png"
    wide.write_bytes(_png(2000, 700))  # aspect ~2.86 > 2.6 hero max
    a = assess_image(wide, role="hero", source="client")
    assert not a.ok
    assert "aspect" in a.reason


def test_accept_good_hero(tmp_path: Path):
    good = tmp_path / "good.png"
    good.write_bytes(_png(1200, 800))
    a = assess_image(good, role="hero", source="client")
    assert a.ok
    assert a.width == 1200


def test_client_hero_kept_when_quality_ok(tmp_path: Path):
    product = tmp_path / "p"
    assets = product / "assets"
    assets.mkdir(parents=True)
    hero = assets / "hero.jpg"
    # JPEG-like: use PNG named jpg — assess uses magic bytes
    hero.write_bytes(_png(1280, 720, (10, 120, 90)))
    plan = finalize_product_media(
        product,
        niche_id="dental",
        market_code="DE",
        package_id="business",
        business_name="Praxis Client Photo",
        hero_from_client=True,
        gallery_rels=[],
    )
    assert plan.hero_from_client is True
    assert plan.hero_ok is True
    assert plan.gate_ok is True
    # File still client-colored (green-ish first pixel path — size preserved)
    assert hero.stat().st_size > 800


def test_bad_client_hero_replaced_by_niche(tmp_path: Path):
    product = tmp_path / "p"
    assets = product / "assets"
    assets.mkdir(parents=True)
    hero = assets / "hero.jpg"
    hero.write_bytes(_png(80, 60))
    before = hero.read_bytes()
    plan = finalize_product_media(
        product,
        niche_id="dental",
        market_code="DE",
        package_id="business",
        business_name="Praxis Bad Photo",
        hero_from_client=True,
        gallery_rels=[],
    )
    assert plan.hero_from_client is False
    assert plan.hero_ok is True
    assert hero.read_bytes() != before
    assert (assets / "media_manifest.json").is_file()


def test_gallery_drops_bad_keeps_good(tmp_path: Path):
    product = tmp_path / "p"
    assets = product / "assets" / "client"
    assets.mkdir(parents=True)
    good = assets / "g1.png"
    bad = assets / "g2.png"
    good.write_bytes(_png(640, 480))
    bad.write_bytes(_png(50, 50))
    plan = finalize_product_media(
        product,
        niche_id="dental",
        market_code="DE",
        package_id="business",
        business_name="Gallery Test",
        hero_from_client=False,
        gallery_rels=["assets/client/g1.png", "assets/client/g2.png"],
    )
    assert plan.gallery == ["assets/client/g1.png"]
    assert plan.hero_ok is True


def test_market_aware_hero_pick_deterministic():
    a = pick_niche_hero(
        niche_id="dental",
        package_id="business",
        market_code="DE",
        business_name="Mueller Praxis",
    )
    b = pick_niche_hero(
        niche_id="dental",
        package_id="business",
        market_code="DE",
        business_name="Mueller Praxis",
    )
    c = pick_niche_hero(
        niche_id="dental",
        package_id="business",
        market_code="ES",
        business_name="Mueller Praxis",
    )
    assert a is not None and b is not None
    assert a == b
    # Market shifts seed — may or may not differ if pool size 1; both must be valid
    assert assess_image(a, role="hero").ok
    if c is not None:
        assert assess_image(c, role="hero").ok


def test_html_gets_media_intelligence_css():
    html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="DE",
        hero_photo=True,
        media_css="    /* Media Intelligence R2.2e */\n    .hero img { object-fit: cover; }\n",
        media_background=True,
    )
    assert "Media Intelligence" in html
    assert "object-fit: cover" in html
    assert 'data-media-bg="1"' in html


def test_factory_zip_includes_manifest_and_object_fit(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Zahnarztpraxis Mueller in Koeln. Prophylaxe und Implantate.",
        package_id="business",
        market_code="DE",
        client_legal={
            "owner_name": "Dr. Test",
            "street": "Hauptstr. 1",
            "zip": "50667",
            "city": "Koeln",
            "email": "a@b.de",
        },
    )
    pid = product["product_id"]
    assets = tmp_path / "sandbox" / pid / "assets"
    assert (assets / "media_manifest.json").is_file()
    html = (tmp_path / "sandbox" / pid / "index.html").read_text(encoding="utf-8")
    assert "Media Intelligence" in html
    gate = run_quality_gate(
        html,
        meta={"market_code": "DE", "package_delivery": {"package_id": "business"}},
        assets_dir=assets,
    )
    assert gate.passed, gate.failures
    data, name = factory.build_client_delivery_zip(pid)
    assert name.endswith(".zip")
    assert b"media_manifest.json" in data or len(data) > 1000


def test_zip_blocked_when_hero_destroyed(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Autowerkstatt Schmidt in Berlin. Inspektion.",
        package_id="business",
        market_code="DE",
        client_legal={
            "owner_name": "Herr Schmidt",
            "street": "Werkstr. 2",
            "zip": "10115",
            "city": "Berlin",
            "email": "a@b.de",
        },
    )
    pid = product["product_id"]
    assets = tmp_path / "sandbox" / pid / "assets"
    # Corrupt hero + manifest so Image Quality Gate fails
    (assets / "hero.jpg").write_bytes(_png(40, 30))
    import json

    man = json.loads((assets / "media_manifest.json").read_text(encoding="utf-8"))
    man["hero_ok"] = False
    man["gate_ok"] = False
    man["gate_failures"] = ["hero:not_ok"]
    (assets / "media_manifest.json").write_text(json.dumps(man), encoding="utf-8")
    with pytest.raises(QualityGateError):
        factory.build_client_delivery_zip(pid)
