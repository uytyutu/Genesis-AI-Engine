"""Cross-niche pollution: beauty bytes in psychology pack must fail gate."""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.factory.media_gate import (
    invalidate_showcase_md5_index,
    media_fits_section,
    tags_for_media,
)


def test_psychology_pack_has_no_beauty_byte_collisions():
    backend = Path(__file__).resolve().parents[1]
    psych = backend / "_research_3d" / "showcases" / "psychology"
    beauty = backend / "_research_3d" / "showcases" / "beauty"
    bh = {hashlib.md5(p.read_bytes()).hexdigest() for p in beauty.rglob("*.jpg")}
    collisions = [
        p
        for p in psych.rglob("*.jpg")
        if hashlib.md5(p.read_bytes()).hexdigest() in bh
    ]
    assert not collisions, f"psychology still shares beauty bytes: {collisions}"


def test_cross_niche_bytes_denied_for_psychology(tmp_path: Path):
    backend = Path(__file__).resolve().parents[1]
    beauty_laser = (
        backend
        / "_research_3d"
        / "showcases"
        / "beauty"
        / "products"
        / "laser"
        / "preview.jpg"
    )
    assert beauty_laser.is_file()
    # Simulate pollution: same bytes under psychology folder name
    pollute = (
        tmp_path
        / "showcases"
        / "psychology"
        / "hero_pack"
        / "basic"
        / "hero_2.jpg"
    )
    # Use real showcase path for hash index — copy into real psych would be destructive;
    # instead assert tags on the beauty file itself vs psychology niche rule.
    tags = tags_for_media(beauty_laser, source="niche", niche_id="psychology")
    assert "salon" in tags or "cosmetics" in tags or "interior" in tags
    assert not media_fits_section(
        beauty_laser, niche_id="psychology", section="hero", source="niche"
    )


def test_invalidate_index_after_pack_repair():
    invalidate_showcase_md5_index()
    # smoke: index rebuilds
    from app.factory.media_gate import _showcase_md5_index

    idx = _showcase_md5_index()
    assert isinstance(idx, dict)
