"""Copy niche hero still into Factory product assets (offline ZIP)."""

from __future__ import annotations

from pathlib import Path

from app.factory.hero_pack import primary_hero_src, write_hero_pack


def resolve_niche_hero_src(niche_id: str | None) -> Path | None:
    """Return best local preview / pack hero for niche."""
    return primary_hero_src(niche_id, "basic")


def write_hero_asset(
    product_dir: Path,
    niche_id: str | None,
    package_id: str | None = None,
) -> bool:
    """Write Hero Pack 2.0 assets + canonical hero.jpg for the package tier."""
    manifest = write_hero_pack(product_dir, niche_id, package_id)
    return bool(manifest.get("hero"))
