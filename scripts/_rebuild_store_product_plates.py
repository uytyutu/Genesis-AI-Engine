"""Rebuild AI Store demo product images as unique labeled plates (no Live API).

Each product_N.jpg becomes a distinct product shot for that niche + SKU name.
"""
from __future__ import annotations

import colorsys
import hashlib
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
STORES = ROOT / "dashboard" / "frontend" / "public" / "package-previews" / "stores" / "premium"
VITRINE = ROOT / "dashboard" / "frontend" / "public" / "vitrine"

NICHES = {
    "beauty": ((0.92, 0.35, 0.55), (0.98, 0.92, 0.94)),
    "cleaning_shop": ((0.05, 0.55, 0.48), (0.90, 0.98, 0.96)),
    "electronics": ((0.55, 0.75, 0.95), (0.08, 0.10, 0.16)),
    "food": ((0.92, 0.45, 0.12), (0.99, 0.95, 0.88)),
    "furniture": ((0.45, 0.38, 0.30), (0.95, 0.93, 0.88)),
    "fashion": ((0.75, 0.72, 0.68), (0.10, 0.09, 0.08)),
}


def _font(size: int) -> ImageFont.ImageFont:
    for name in (
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ):
        p = Path(name)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def _rgb(t):
    return tuple(int(max(0, min(1, c)) * 255) for c in t)


def parse_products(catalog: Path) -> list[tuple[int, str]]:
    html = catalog.read_text(encoding="utf-8", errors="replace")
    out: list[tuple[int, str]] = []
    for m in re.finditer(
        r'data-name="([^"]+)".*?product_(\d+)\.jpg',
        html,
        flags=re.I | re.S,
    ):
        name, num = m.group(1), int(m.group(2))
        out.append((num, name))
    # fallback: title near product_N
    if not out:
        for m in re.finditer(
            r'product_(\d+)\.jpg".*?<h3>([^<]+)</h3>',
            html,
            flags=re.I | re.S,
        ):
            out.append((int(m.group(1)), m.group(2).strip()))
    # unique by num
    seen = {}
    for num, name in out:
        seen[num] = name
    return sorted(seen.items())


def draw_product(niche: str, num: int, name: str, dest: Path) -> None:
    accent, bg = NICHES[niche]
    seed = int(hashlib.md5(f"{niche}:{num}:{name}".encode()).hexdigest()[:8], 16)
    w, h = 800, 1000
    im = Image.new("RGB", (w, h), _rgb(bg))
    d = ImageDraw.Draw(im)

    # soft vignette circles
    for i in range(6):
        r = 120 + (seed + i * 37) % 180
        cx = (seed * (i + 3)) % w
        cy = (seed * (i + 5)) % (h // 2)
        col = _rgb(
            tuple(
                bg[j] * 0.7 + accent[j] * (0.15 + (i % 3) * 0.08) for j in range(3)
            )
        )
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)

    im = im.filter(ImageFilter.GaussianBlur(radius=18))
    d = ImageDraw.Draw(im)

    # product silhouette varies by niche + num
    shape = (num + seed) % 4
    ax, ay, aw, ah = w // 2, int(h * 0.42), 220, 420
    fill = _rgb(tuple(accent[j] * 0.85 + 0.05 for j in range(3)))
    edge = _rgb(tuple(min(1.0, accent[j] + 0.15) for j in range(3)))
    if shape == 0:  # bottle
        d.rounded_rectangle(
            (ax - 70, ay - 160, ax + 70, ay + 200), radius=40, fill=fill, outline=edge, width=4
        )
        d.rectangle((ax - 28, ay - 220, ax + 28, ay - 160), fill=edge)
    elif shape == 1:  # jar
        d.ellipse((ax - 120, ay - 40, ax + 120, ay + 200), fill=fill, outline=edge, width=4)
        d.rounded_rectangle(
            (ax - 110, ay - 90, ax + 110, ay - 20), radius=18, fill=edge
        )
    elif shape == 2:  # box
        d.rounded_rectangle(
            (ax - 140, ay - 120, ax + 140, ay + 180), radius=28, fill=fill, outline=edge, width=4
        )
        d.line((ax - 140, ay - 40, ax + 140, ay - 40), fill=edge, width=3)
    else:  # tube
        d.rounded_rectangle(
            (ax - 50, ay - 200, ax + 50, ay + 210), radius=24, fill=fill, outline=edge, width=4
        )
        d.ellipse((ax - 50, ay - 230, ax + 50, ay - 180), fill=edge)

    # label plate
    d.rounded_rectangle((60, h - 260, w - 60, h - 80), radius=24, fill=_rgb((0.08, 0.08, 0.1)) if sum(bg) < 1.2 else _rgb((1, 1, 1)))
    title_col = (255, 255, 255) if sum(bg) < 1.2 else (20, 20, 24)
    font_t = _font(36)
    font_s = _font(22)
    # wrap name
    words = name.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        test = (cur + " " + word).strip()
        if d.textlength(test, font=font_t) < w - 160:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    lines = lines[:3] or [name[:28]]
    y = h - 230
    for line in lines:
        d.text((90, y), line, font=font_t, fill=title_col)
        y += 42
    d.text((90, h - 120), f"{niche.replace('_', ' ').title()} · Demo #{num}", font=font_s, fill=_rgb(accent))

    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=90, optimize=True)


def rebuild_niche(niche: str) -> str:
    store = STORES / niche
    catalog = store / "catalog.html"
    if not catalog.exists():
        return f"{niche}: no catalog"
    products = parse_products(catalog)
    if not products:
        # invent 24
        products = [(i, f"Produkt {i}") for i in range(1, 25)]
    assets = store / "assets" / "images"
    assets.mkdir(parents=True, exist_ok=True)
    for num, name in products:
        draw_product(niche, num, name, assets / f"product_{num}.jpg")
    # thumb from product 1
    thumb_map = {
        "beauty": "store-beauty.jpg",
        "cleaning_shop": "store-cleaning.jpg",
        "electronics": "store-electronics.jpg",
        "food": "store-food.jpg",
        "furniture": "store-furniture.jpg",
        "fashion": "store-fashion.jpg",
    }
    p1 = assets / "product_1.jpg"
    if p1.exists():
        thumb_path = VITRINE / thumb_map[niche]
        with Image.open(p1) as im:
            im = im.convert("RGB").resize((960, 640))
            im.save(thumb_path, "JPEG", quality=86, optimize=True)
    return f"{niche}: {len(products)} unique plates"


def main() -> None:
    for niche in NICHES:
        print(rebuild_niche(niche))
    print("done")


if __name__ == "__main__":
    main()
