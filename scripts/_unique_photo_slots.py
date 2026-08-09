"""Fill service_*/gallery_* from real showcase photos with unique crops (no abstracts)."""
from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SHOW = ROOT / "dashboard" / "backend" / "_research_3d" / "showcases"
SITES = ROOT / "dashboard" / "frontend" / "public" / "package-previews" / "sites" / "premium"

MAP = {
    "beauty": SHOW / "beauty",
    "cleaning": SHOW / "green",
    "it_support": SHOW / "computer",
    "dental": SHOW / "dental",
    "restaurant": (
        ROOT / "dashboard" / "frontend" / "public" / "package-previews" / "vitrine"
        if (ROOT / "dashboard" / "frontend" / "public" / "package-previews" / "vitrine").exists()
        else SHOW / "generic"
    ),
    "handwerk": SHOW / "handwerk",
    "law": SHOW / "law",
    "auto": SHOW / "auto",
}


def sources(niche: str) -> list[Path]:
    root = MAP[niche]
    files = [
        p
        for p in sorted(root.rglob("*"))
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and p.is_file()
    ]
    # prefer larger files (real photos)
    files.sort(key=lambda p: -p.stat().st_size)
    return [p for p in files if p.stat().st_size > 80_000] or files


def unique_crop(src: Path, dest: Path, salt: int, size=(1280, 860)) -> None:
    with Image.open(src) as im:
        im = im.convert("RGB")
        w, h = im.size
        # different crop window per salt
        zx = 0.08 + (salt % 7) * 0.02
        zy = 0.08 + (salt % 5) * 0.025
        ox = int(w * ((salt * 17) % 40) / 100 * zx)
        oy = int(h * ((salt * 13) % 40) / 100 * zy)
        left = ox
        top = oy
        right = w - ox - (salt % 30)
        bottom = h - oy - (salt % 25)
        if right - left < 200 or bottom - top < 200:
            left, top, right, bottom = 0, 0, w, h
        im = im.crop((left, top, right, bottom))
        im = ImageOps.fit(im, size, Image.Resampling.LANCZOS)
        im = ImageEnhance.Brightness(im).enhance(0.9 + (salt % 6) * 0.04)
        im = ImageEnhance.Contrast(im).enhance(1.05 + (salt % 5) * 0.05)
        im = ImageEnhance.Color(im).enhance(0.9 + (salt % 7) * 0.05)
        # slight hue bias via color balance channel
        r, g, b = im.split()
        if salt % 3 == 0:
            r = r.point(lambda x: min(255, int(x * 1.06)))
        elif salt % 3 == 1:
            g = g.point(lambda x: min(255, int(x * 1.05)))
        else:
            b = b.point(lambda x: min(255, int(x * 1.07)))
        im = Image.merge("RGB", (r, g, b))
        dest.parent.mkdir(parents=True, exist_ok=True)
        im.save(dest, "JPEG", quality=90, optimize=True)


def patch(niche: str) -> str:
    srcs = sources(niche)
    if not srcs:
        return f"{niche}: no sources"
    assets = SITES / niche / "assets"
    hashes = []
    for i in range(1, 9):
        src = srcs[(i * 2 + hash(niche)) % len(srcs)]
        dest = assets / f"service_{i}.jpg"
        unique_crop(src, dest, salt=i * 31 + (hash(niche) % 97))
        hashes.append(hashlib.md5(dest.read_bytes()).hexdigest()[:8])
    for i in range(1, 13):
        src = srcs[(i * 3 + 1 + hash(niche)) % len(srcs)]
        dest = assets / f"gallery_{i}.jpg"
        unique_crop(src, dest, salt=200 + i * 29 + (hash(niche) % 53), size=(1200, 900))
    uniq = len(set(hashes))
    return f"{niche}: services unique={uniq}/8 from {len(srcs)} photos"


def main() -> None:
    for niche in MAP:
        print(patch(niche))
    print("done")


if __name__ == "__main__":
    main()
