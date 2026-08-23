"""Rebuild unique /public/vitrine/*.jpg thumbs from niche demos (no live Image API)."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public"
VITRINE = PUBLIC / "vitrine"
SITES = PUBLIC / "package-previews" / "sites" / "premium"
STORES = PUBLIC / "package-previews" / "stores" / "premium"

# dest thumb -> preferred source (first existing wins)
MAP: list[tuple[str, list[Path]]] = [
    ("web-lumia.jpg", [SITES / "beauty" / "assets" / "hero.jpg", SITES / "beauty" / "assets" / "gallery.jpg"]),
    ("web-beauty.jpg", [SITES / "beauty" / "assets" / "gallery.jpg", SITES / "beauty" / "assets" / "hero.jpg"]),
    ("web-cleaning.jpg", [SITES / "cleaning" / "assets" / "hero.jpg", SITES / "cleaning" / "assets" / "gallery.jpg"]),
    ("web-dental.jpg", [SITES / "dental" / "assets" / "hero.jpg", SITES / "dental" / "assets" / "gallery.jpg"]),
    ("web-restaurant.jpg", [SITES / "restaurant" / "assets" / "hero.jpg", SITES / "restaurant" / "assets" / "gallery.jpg"]),
    ("web-handwerk.jpg", [SITES / "handwerk" / "assets" / "hero.jpg", SITES / "handwerk" / "assets" / "gallery.jpg"]),
    ("web-law.jpg", [SITES / "law" / "assets" / "hero.jpg", SITES / "law" / "assets" / "gallery.jpg"]),
    ("web-auto.jpg", [SITES / "auto" / "assets" / "hero.jpg", SITES / "auto" / "assets" / "gallery.jpg"]),
    ("web-it.jpg", [SITES / "it_support" / "assets" / "hero.jpg", SITES / "elektro" / "assets" / "hero.jpg"]),
    ("store-lumia.jpg", [STORES / "beauty" / "assets" / "images" / "hero.jpg", SITES / "beauty" / "assets" / "gallery.jpg"]),
    ("store-beauty.jpg", [STORES / "beauty" / "assets" / "images" / "product_1.jpg", STORES / "beauty" / "assets" / "images" / "hero.jpg"]),
    ("store-cleaning.jpg", [STORES / "cleaning_shop" / "assets" / "images" / "hero.jpg"]),
    ("store-electronics.jpg", [STORES / "electronics" / "assets" / "images" / "hero.jpg"]),
    ("store-fashion.jpg", [STORES / "fashion" / "assets" / "images" / "hero.jpg"]),
    ("store-food.jpg", [STORES / "food" / "assets" / "images" / "hero.jpg"]),
    ("store-furniture.jpg", [STORES / "furniture" / "assets" / "images" / "hero.jpg"]),
]


def main() -> None:
    VITRINE.mkdir(parents=True, exist_ok=True)
    for dest_name, sources in MAP:
        src = next((p for p in sources if p.is_file() and p.stat().st_size >= 8000), None)
        if src is None:
            print("SKIP", dest_name)
            continue
        dest = VITRINE / dest_name
        shutil.copy2(src, dest)
        print("OK", dest_name, "<-", src.relative_to(PUBLIC), dest.stat().st_size)

    hashes: dict[str, list[str]] = {}
    for p in sorted(VITRINE.glob("*.jpg")):
        dig = hashlib.md5(p.read_bytes()).hexdigest()[:12]
        hashes.setdefault(dig, []).append(p.name)
    dupes = {k: v for k, v in hashes.items() if len(v) > 1}
    print("DUPES", dupes or "none")


if __name__ == "__main__":
    main()
