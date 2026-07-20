"""Hero packs must be unique per niche (no shared dental placeholder)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.factory.hero_still import resolve_niche_hero_src, write_hero_asset
from app.factory.niche_profiles import known_niche_ids


def test_niche_hero_previews_are_unique() -> None:
    show = Path(__file__).resolve().parents[1] / "_research_3d" / "showcases"
    hashes: dict[str, list[str]] = {}
    for niche in known_niche_ids():
        path = show / niche / "preview.jpg"
        assert path.is_file(), f"missing hero for {niche}"
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        hashes.setdefault(digest, []).append(niche)
    collisions = {h: names for h, names in hashes.items() if len(names) > 1}
    assert not collisions, f"duplicate hero stills: {collisions}"


def test_write_hero_asset_uses_niche_file(tmp_path: Path) -> None:
    src = resolve_niche_hero_src("auto")
    assert src is not None
    assert src.suffix.lower() in (".jpg", ".jpeg", ".png")
    assert write_hero_asset(tmp_path, "auto", "business") is True
    dest = tmp_path / "assets" / "hero.jpg"
    assert dest.is_file()
    assert len(dest.read_bytes()) > 1000
    assert (tmp_path / "assets" / "hero_pack" / "manifest.json").is_file()
