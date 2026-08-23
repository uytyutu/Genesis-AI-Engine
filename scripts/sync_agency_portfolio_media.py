"""Sync premium Factory media into business portfolio artifacts.

Problem: /site cards showed basic/ hero thumbs while Besuchen opened business/
builds with stub placeholders (~29KB). Premium tier folders hold the real media pack.

This script copies assets premium → business for published agency portfolio niches only.
Run after a new Reality PASS export, before eye-review on /site → Besuchen.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITES = ROOT / "dashboard" / "frontend" / "public" / "package-previews" / "sites"

# premium source → business public artifact (matches PUBLIC_AGENCY_PORTFOLIO)
SYNC_PAIRS: tuple[tuple[str, str], ...] = (
    ("premium/auto", "business/auto"),
    ("premium/restaurant", "business/restaurant"),
)

MIN_HERO_BYTES = 80_000
MIN_GALLERY_BYTES = 50_000


def _copy_assets(src_rel: str, dst_rel: str) -> int:
    src = SITES / src_rel / "assets"
    dst = SITES / dst_rel / "assets"
    if not src.is_dir():
        raise FileNotFoundError(f"missing source assets: {src}")
    dst.mkdir(parents=True, exist_ok=True)
    copied = 0
    for path in src.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
    return copied


def _verify_artifact(dst_rel: str) -> list[str]:
    errors: list[str] = []
    assets = SITES / dst_rel / "assets"
    hero = assets / "hero.jpg"
    if not hero.is_file():
        errors.append(f"{dst_rel}: missing assets/hero.jpg")
    elif hero.stat().st_size < MIN_HERO_BYTES:
        errors.append(
            f"{dst_rel}: hero too small ({hero.stat().st_size}B < {MIN_HERO_BYTES}B — placeholder?)"
        )
    gallery_ok = sum(
        1
        for i in range(1, 4)
        if (assets / f"gallery_{i}.jpg").is_file()
        and (assets / f"gallery_{i}.jpg").stat().st_size >= MIN_GALLERY_BYTES
    )
    if gallery_ok < 3:
        errors.append(f"{dst_rel}: need 3 gallery images ≥{MIN_GALLERY_BYTES}B (got {gallery_ok})")
    return errors


def main() -> int:
    total = 0
    all_errors: list[str] = []
    for src_rel, dst_rel in SYNC_PAIRS:
        n = _copy_assets(src_rel, dst_rel)
        total += n
        print(f"OK  {src_rel}/assets -> {dst_rel}/assets ({n} files)")
        all_errors.extend(_verify_artifact(dst_rel))
    if all_errors:
        print("\nVERIFY FAIL:", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"\nPortfolio media sync complete — {total} files, visual floor PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
