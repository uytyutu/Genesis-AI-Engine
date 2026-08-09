"""Force visibly unique frames for site services/galleries + cache-bust store imgs."""
from __future__ import annotations

import colorsys
import hashlib
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SITES = ROOT / "dashboard" / "frontend" / "public" / "package-previews" / "sites" / "premium"
STORES = ROOT / "dashboard" / "frontend" / "public" / "package-previews" / "stores" / "premium"

SITE_NICHES = [
    "beauty",
    "cleaning",
    "it_support",
    "dental",
    "restaurant",
    "handwerk",
    "law",
    "auto",
]

PALETTES = {
    "beauty": [(0.75, 0.35, 0.42), (0.97, 0.93, 0.92)],
    "cleaning": [(0.08, 0.55, 0.48), (0.92, 0.98, 0.96)],
    "it_support": [(0.22, 0.55, 0.95), (0.08, 0.11, 0.18)],
    "dental": [(0.15, 0.45, 0.75), (0.94, 0.97, 0.99)],
    "restaurant": [(0.72, 0.28, 0.12), (0.14, 0.10, 0.08)],
    "handwerk": [(0.70, 0.40, 0.12), (0.95, 0.92, 0.85)],
    "law": [(0.35, 0.32, 0.28), (0.96, 0.94, 0.90)],
    "auto": [(0.85, 0.18, 0.16), (0.10, 0.12, 0.16)],
}

LABELS = {
    "law": [
        "Erstberatung",
        "Vertrag",
        "Gesellschaft",
        "Arbeit",
        "Vertretung",
        "Verhandlung",
        "Marke",
        "DSGVO",
        "Kanzlei",
        "Akte",
        "Team",
        "Frankfurt",
    ],
}


def _font(size: int):
    for name in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        if Path(name).exists():
            return ImageFont.truetype(name, size=size)
    return ImageFont.load_default()


def _rgb(t):
    return tuple(int(max(0, min(1, c)) * 255) for c in t)


def make_frame(niche: str, idx: int, label: str, dest: Path, size=(1280, 860)) -> None:
    accent, bg = PALETTES[niche]
    seed = int(hashlib.md5(f"{niche}:{idx}:{label}".encode()).hexdigest()[:8], 16)
    w, h = size
    im = Image.new("RGB", (w, h), _rgb(bg))
    d = ImageDraw.Draw(im)

    # unique geometric composition per idx
    hue = (seed % 360) / 360
    for i in range(8):
        r = 80 + (seed + i * 41) % 220
        cx = (seed * (i + 2) * 17) % w
        cy = (seed * (i + 3) * 13) % h
        col = colorsys.hsv_to_rgb((hue + i * 0.07) % 1.0, 0.35 + (i % 3) * 0.1, 0.55 + (i % 4) * 0.1)
        # blend with niche accent
        col = tuple(col[j] * 0.45 + accent[j] * 0.55 for j in range(3))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_rgb(col))

    # structural shape
    mode = idx % 5
    fill = _rgb(tuple(accent[j] * 0.9 for j in range(3)))
    if mode == 0:
        d.rectangle((w * 0.1, h * 0.2, w * 0.55, h * 0.75), fill=fill)
    elif mode == 1:
        d.polygon([(w * 0.2, h * 0.8), (w * 0.5, h * 0.15), (w * 0.8, h * 0.8)], fill=fill)
    elif mode == 2:
        d.rounded_rectangle((w * 0.15, h * 0.18, w * 0.85, h * 0.7), radius=48, fill=fill)
    elif mode == 3:
        for k in range(6):
            x0 = int(w * (0.12 + k * 0.13))
            d.rectangle((x0, int(h * 0.25), x0 + 50, int(h * 0.75)), fill=fill)
    else:
        d.ellipse((w * 0.25, h * 0.18, w * 0.75, h * 0.78), fill=fill)

    im = im.filter(ImageFilter.GaussianBlur(radius=10))
    # add mild noise via second layer dots
    d = ImageDraw.Draw(im)
    for i in range(40):
        x = (seed * (i + 9)) % w
        y = (seed * (i + 11)) % h
        d.point((x, y), fill=_rgb(accent))

    # label band
    band = _rgb((0.08, 0.08, 0.1)) if sum(bg) > 1.5 else _rgb((0.95, 0.95, 0.93))
    ink = (245, 245, 245) if sum(bg) > 1.5 else (20, 20, 22)
    d.rounded_rectangle((48, h - 150, w - 48, h - 48), radius=20, fill=band)
    d.text((72, h - 120), label, font=_font(44), fill=ink)
    d.text((72, h - 70), f"{niche} · frame {idx}", font=_font(22), fill=_rgb(accent))

    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=90, optimize=True)


def patch_site(niche: str) -> str:
    assets = SITES / niche / "assets"
    labels = LABELS.get(niche) or [f"Motiv {i}" for i in range(1, 13)]
    while len(labels) < 12:
        labels.append(f"Motiv {len(labels)+1}")
    for i in range(1, 9):
        make_frame(niche, i, labels[i - 1], assets / f"service_{i}.jpg")
    for i in range(1, 13):
        make_frame(niche, 20 + i, labels[i - 1], assets / f"gallery_{i}.jpg", size=(1200, 900))
    # Keep photographic heroes — do not overwrite
    return f"{niche}: 8 service + 12 gallery unique"


def cache_bust_store(niche: str) -> str:
    store = STORES / niche
    n = 0
    for path in store.glob("*.html"):
        html = path.read_text(encoding="utf-8", errors="replace")
        html2 = re.sub(
            r'(src="assets/images/product_(\d+)\.jpg)(?:\?[^"]*)?"',
            r'\1?v=u\2"',
            html,
        )
        if html2 != html:
            path.write_text(html2, encoding="utf-8")
            n += 1
    return f"store/{niche}: cache-bust {n} pages"


def main() -> None:
    for niche in SITE_NICHES:
        print(patch_site(niche))
    for niche in ("beauty", "cleaning_shop", "electronics", "food", "furniture", "fashion"):
        print(cache_bust_store(niche))
    print("done")


if __name__ == "__main__":
    main()
