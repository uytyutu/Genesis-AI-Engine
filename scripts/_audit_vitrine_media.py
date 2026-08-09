"""One-shot audit: vitrine thumbs + demo HTML image paths."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public"


def main() -> None:
    vitrine = PUBLIC / "vitrine"
    print("VITRINE_DIR", vitrine.exists())
    if vitrine.exists():
        for p in sorted(vitrine.iterdir())[:50]:
            if p.is_file():
                print(f"  {p.name}\t{p.stat().st_size}")

    thumbs = [
        "package-previews/sites/premium/auto/assets/gallery.jpg",
        "package-previews/sites/premium/beauty/assets/gallery.jpg",
        "package-previews/sites/premium/energy/assets/gallery.jpg",
        "package-previews/stores/premium/beauty/assets/images/hero.jpg",
        "package-previews/stores/premium/coffee/assets/images/hero.jpg",
        "package-previews/stores/premium/fashion/assets/images/hero.jpg",
        "vitrine/web-lumia.jpg",
        "vitrine/web-cleaning.jpg",
        "vitrine/web-dental.jpg",
        "vitrine/store-fashion.jpg",
        "vitrine/store-beauty.jpg",
        "vitrine/store-electronics.jpg",
    ]
    print("--- THUMBS ---")
    for t in thumbs:
        p = PUBLIC / t
        print(("OK" if p.is_file() else "MISS"), t, p.stat().st_size if p.is_file() else 0)

    print("--- HTML IMG ---")
    for rel in (
        "package-previews/sites/premium/beauty/index.html",
        "package-previews/sites/premium/auto/index.html",
        "package-previews/stores/premium/beauty/catalog.html",
        "package-previews/stores/premium/coffee/catalog.html",
    ):
        path = PUBLIC / rel
        if not path.is_file():
            print("MISS HTML", rel)
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        srcs = re.findall(r"""src=["']([^"']+)["']""", html)
        print(f"HTML {rel} imgs={len(srcs)}")
        base = path.parent
        miss = 0
        for s in srcs[:20]:
            if s.startswith(("http://", "https://", "data:", "//")):
                print("  remote", s[:70])
                continue
            if s.startswith("/"):
                cand = PUBLIC / s.lstrip("/")
            else:
                cand = (base / s).resolve()
            ok = cand.is_file()
            if not ok:
                miss += 1
            print(("  OK" if ok else "  MISS"), s[:90], cand.stat().st_size if ok else 0)
        print(f"  miss_in_sample={miss}")

    print("--- STORE HERO HASHES ---")
    stores = PUBLIC / "package-previews" / "stores" / "premium"
    hashes: dict[str, list[str]] = {}
    if stores.is_dir():
        for folder in sorted(p.name for p in stores.iterdir() if p.is_dir()):
            hero = stores / folder / "assets" / "images" / "hero.jpg"
            if not hero.is_file():
                print("MISS", folder)
                continue
            dig = hashlib.md5(hero.read_bytes()).hexdigest()[:12]
            hashes.setdefault(dig, []).append(folder)
            print(folder, hero.stat().st_size, dig)
    print("DUPES", {k: v for k, v in hashes.items() if len(v) > 1} or "none")


if __name__ == "__main__":
    main()
