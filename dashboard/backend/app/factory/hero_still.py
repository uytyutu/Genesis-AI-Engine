"""Copy niche hero still into Factory product assets (offline ZIP)."""

from __future__ import annotations

import shutil
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[2]
_SHOWCASES = _BACKEND / "_research_3d" / "showcases"


def resolve_niche_hero_src(niche_id: str | None) -> Path | None:
    """Return best local preview.jpg for niche, or None."""
    key = (niche_id or "generic").strip().lower() or "generic"
    candidates = [
        _SHOWCASES / key / "preview.jpg",
        _SHOWCASES / "generic" / "preview.jpg",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def write_hero_asset(product_dir: Path, niche_id: str | None) -> bool:
    """Copy niche still to product_dir/assets/hero.jpg. Returns True if written."""
    src = resolve_niche_hero_src(niche_id)
    if src is None:
        return False
    assets = product_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    dest = assets / "hero.jpg"
    shutil.copy2(src, dest)
    return True
