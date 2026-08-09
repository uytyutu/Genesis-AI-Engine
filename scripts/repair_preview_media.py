"""One-shot: repair preview images + overflow CSS on package-previews.

Fixes:
- missing / hero-cloned galleries on sites
- wrong-niche store heroes (jewelry=beauty, pets/sports cloned stock)
- inject typography overflow guard into existing index.html
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.factory.niche_scene_media import write_niche_scene  # noqa: E402

PUBLIC = ROOT / "dashboard" / "frontend" / "public" / "package-previews"

OVERFLOW_CSS = """
/* typography overflow guard · gallery repair */
body, body h1, body h2, body h3, body .hero h1, body .hero-title, body .page-title {
  overflow-wrap: anywhere !important;
  word-break: break-word !important;
  max-width: 100% !important;
  white-space: normal !important;
}
body .hero h1, body .hero-title, body h1 {
  font-size: clamp(1.7rem, 4.2vw, 3.2rem) !important;
}
@media (max-width: 720px) {
  body .hero h1, body .hero-title, body h1 {
    font-size: clamp(1.55rem, 5.8vw, 2.15rem) !important;
  }
}
"""

STORE_FORCE = {
    "jewelry",
    "pets",
    "sports",
    "coffee",
    "furniture",
    "gartenpflege",
    "zaunbau",
    "fashion",
    "accessories",
    "food",
}


def _dedupe_typography(html: str) -> str:
    """Keep only the last Typography Studio block; drop earlier conflicting ones."""
    marker = "/* Typography Studio"
    parts = html.split(marker)
    if len(parts) <= 2:
        return html
    # parts[0] = before first; parts[1..] each start mid-block after marker
    # Keep first preamble + last studio block only
    last = marker + parts[-1]
    # Truncate last at next major comment that isn't continuation? Keep as-is until </style> logic
    # Simpler: remove middle studio blocks by regex
    blocks = list(re.finditer(r"/\*\s*Typography Studio[\s\S]*?(?=/\*\s*Typography Studio|/\*[^*]|\Z)", html))
    if len(blocks) <= 1:
        return html
    # Remove all but last
    out = html
    for b in reversed(blocks[:-1]):
        out = out[: b.start()] + out[b.end() :]
    return out


def _patch_html(index: Path) -> None:
    html = index.read_text(encoding="utf-8", errors="replace")
    html2 = _dedupe_typography(html)
    if "typography overflow guard" not in html2:
        if "</style>" in html2:
            html2 = html2.replace("</style>", OVERFLOW_CSS + "\n</style>", 1)
        else:
            html2 += f"<style>{OVERFLOW_CSS}</style>"
    if html2 != html:
        index.write_text(html2, encoding="utf-8")
        print(f"  patched HTML {index.parent.name}")


def repair_sites(tier: str = "premium") -> None:
    root = PUBLIC / "sites" / tier
    if not root.is_dir():
        return
    for dest in sorted(root.iterdir()):
        if not dest.is_dir():
            continue
        niche = dest.name
        assets = dest / "assets"
        assets.mkdir(parents=True, exist_ok=True)
        hero = assets / "hero.jpg"
        if not hero.is_file() or hero.stat().st_size < 4_000:
            write_niche_scene(
                hero,
                niche_id=niche,
                seed=f"repair-hero|{tier}|{niche}",
                role="hero",
                size=(1600, 900),
            )
            print(f"  site {niche}: hero")
        for i, name in enumerate(("gallery.jpg", "gallery_1.jpg", "gallery_2.jpg", "gallery_3.jpg")):
            target = assets / name
            need = (not target.is_file()) or target.stat().st_size < 4_000
            if (
                not need
                and hero.is_file()
                and target.is_file()
                and target.stat().st_size == hero.stat().st_size
                and target.read_bytes() == hero.read_bytes()
            ):
                need = True
            if need:
                write_niche_scene(
                    target,
                    niche_id=niche,
                    seed=f"repair-gal|{tier}|{niche}|{name}|{i}",
                    role="gallery",
                    size=(1200, 800),
                )
                print(f"  site {niche}: {name}")
        idx = dest / "index.html"
        if idx.is_file():
            _patch_html(idx)


def repair_stores(tier: str = "premium") -> None:
    root = PUBLIC / "stores" / tier
    if not root.is_dir():
        return
    # Detect identical hero blobs across stores
    heroes: dict[int, list[str]] = {}
    for dest in sorted(root.iterdir()):
        if not dest.is_dir():
            continue
        hero = dest / "assets" / "images" / "hero.jpg"
        if hero.is_file():
            heroes.setdefault(hero.stat().st_size, []).append(dest.name)

    cloned = {n for size, names in heroes.items() if len(names) >= 2 for n in names}
    for dest in sorted(root.iterdir()):
        if not dest.is_dir():
            continue
        cat = dest.name
        img = dest / "assets" / "images"
        img.mkdir(parents=True, exist_ok=True)
        force = cat in STORE_FORCE or cat in cloned or cat == "jewelry"
        hero = img / "hero.jpg"
        if force or not hero.is_file() or hero.stat().st_size < 4_000:
            write_niche_scene(
                hero,
                niche_id=cat,
                seed=f"repair-store-hero|{tier}|{cat}",
                role="hero",
                size=(1600, 900),
            )
            print(f"  store {cat}: hero")
        # products 1..6 at least
        for i in range(1, 7):
            p = img / f"product_{i}.jpg"
            if force or not p.is_file() or p.stat().st_size < 4_000:
                write_niche_scene(
                    p,
                    niche_id=cat,
                    seed=f"repair-prod|{tier}|{cat}|{i}",
                    role="product",
                    size=(900, 1120),
                    label=f"Product {i}",
                )
        banner = img / "banner.jpg"
        if force or not banner.is_file() or banner.stat().st_size < 4_000:
            write_niche_scene(
                banner,
                niche_id=cat,
                seed=f"repair-banner|{tier}|{cat}",
                role="banner",
                size=(1600, 600),
            )
        idx = dest / "index.html"
        if idx.is_file():
            _patch_html(idx)


def main() -> None:
    print("Repair sites…")
    repair_sites("premium")
    repair_sites("business")
    print("Repair stores…")
    repair_stores("premium")
    repair_stores("business")
    print("Done.")


if __name__ == "__main__":
    main()
