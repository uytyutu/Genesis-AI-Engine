"""Client-uploaded logo / photos embedded into Factory Path A ZIP."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

from app.factory.client_assets import apply_client_assets, classify_material_images
from app.factory.factory_service import FactoryService
from app.factory.landing_builder import build_landing_html
from app.factory.analyzer import analyze
from app.factory.package_features import resolve_package_features


def _write_png(path: Path, label: bytes = b"x") -> None:
    # Minimal valid-ish PNG header + bytes — browsers not required for this test
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        + b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        + label
    )


def _png(width: int, height: int, rgb: tuple[int, int, int] = (40, 80, 120)) -> bytes:
    """Truecolor PNG large enough for Media Intelligence hero floor."""
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


def test_classify_logo_and_hero(tmp_path: Path):
    logo = tmp_path / "company_logo.png"
    office = tmp_path / "office_reception.jpg"
    work = tmp_path / "work1.jpg"
    _write_png(logo)
    _write_png(office)
    _write_png(work)
    picked = classify_material_images(
        [
            {"path": str(logo), "filename": "company_logo.png", "content_type": "image/png"},
            {
                "path": str(office),
                "filename": "office_reception.jpg",
                "content_type": "image/jpeg",
            },
            {"path": str(work), "filename": "work1.jpg", "content_type": "image/jpeg"},
        ]
    )
    assert picked["logo"]["filename"] == "company_logo.png"
    assert picked["hero"]["filename"] == "office_reception.jpg"
    assert len(picked["gallery"]) == 1


def test_apply_client_assets_writes_files(tmp_path: Path):
    logo = tmp_path / "logo.png"
    photo = tmp_path / "team.jpg"
    _write_png(logo, b"logo")
    _write_png(photo, b"team")
    product = tmp_path / "product"
    product.mkdir()
    result = apply_client_assets(
        product,
        [
            {"path": str(logo), "filename": "logo.png", "content_type": "image/png"},
            {"path": str(photo), "filename": "team.jpg", "content_type": "image/jpeg"},
        ],
    )
    assert result.logo is True
    assert (product / "assets" / "logo.png").is_file()
    assert result.hero_from_client is True
    assert (product / "assets" / "hero.jpg").is_file()
    html = build_landing_html(
        analyze("Zahnarzt Praxis München Premium"),
        features=resolve_package_features("basic"),
        market_code="DE",
        client_logo=True,
        client_logo_src=result.logo_src,
        client_gallery=["assets/client/photo_1.jpg"],
    )
    assert "assets/logo.png" in html
    assert 'id="gallery"' in html
    assert "assets/client/" in html


def test_factory_build_embeds_client_materials(tmp_path: Path):
    logo = tmp_path / "mein_logo.png"
    hero = tmp_path / "praxis_empfang.png"
    _write_png(logo, b"L")
    # Media Intelligence: hero must clear size/dimension floor (≥720×480, ≥800 bytes)
    hero.write_bytes(_png(1280, 720, (10, 120, 90)))
    factory = FactoryService(memory_dir=tmp_path / "mem", sandbox_dir=tmp_path / "sandbox")
    result = factory.build_landing(
        "Zahnarztpraxis Müller in München — moderne Zahnheilkunde",
        package_id="basic",
        contacts={
            "business_name": "Zahnarztpraxis Müller",
            "phone": "+49 89 111",
            "email": "a@b.de",
            "city": "München",
            "market_code": "DE",
            "materials": [
                {
                    "path": str(logo),
                    "filename": "mein_logo.png",
                    "content_type": "image/png",
                },
                {
                    "path": str(hero),
                    "filename": "praxis_empfang.png",
                    "content_type": "image/png",
                },
            ],
        },
        market_code="DE",
    )
    product_id = result["product_id"]
    product_dir = tmp_path / "sandbox" / product_id
    assert (product_dir / "assets" / "logo.png").is_file()
    assert (product_dir / "assets" / "hero.jpg").is_file() or (
        product_dir / "assets" / "hero.png"
    ).is_file()
    html = (product_dir / "index.html").read_text(encoding="utf-8")
    assert "assets/logo.png" in html
    import json

    meta = json.loads((product_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta.get("client_assets", {}).get("logo") is True
    assert meta.get("client_assets", {}).get("hero_from_client") is True
