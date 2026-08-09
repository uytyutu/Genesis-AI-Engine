"""Hide broken 3D blue hero card on public demos; rebuild distinct food product plates."""
from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PREVIEWS = Path(__file__).resolve().parents[1] / "dashboard" / "frontend" / "public" / "package-previews"

CSS = """
<style id="vitrine-hero-photo-fix">
/* Public vitrine: show photo hero, hide broken 3D blue placeholder card */
#virtus-3d-mount,
.virtus-3d-mount,
#virtus-3d-hero,
.virtus-3d-hero,
#virtus-3d-fallback,
.virtus-3d-fallback,
.virtus-tilt-card { display: none !important; visibility: hidden !important; height: 0 !important; min-height: 0 !important; }
</style>
"""

NICHES = [
    "beauty",
    "cleaning",
    "it_support",
    "dental",
    "restaurant",
    "handwerk",
    "law",
    "auto",
]

PRODUCTS = [
    ("Honey", (212, 160, 40), (255, 236, 180)),
    ("Bread", (170, 120, 70), (245, 220, 180)),
    ("Olive Oil", (90, 120, 50), (220, 230, 180)),
    ("Spice", (160, 60, 40), (240, 200, 160)),
    ("Tea", (60, 100, 70), (200, 230, 200)),
    ("Jam", (160, 40, 70), (245, 190, 200)),
    ("Chocolate", (70, 40, 30), (210, 170, 140)),
    ("Salt", (180, 180, 180), (240, 240, 240)),
    ("Juice", (200, 90, 40), (255, 210, 160)),
    ("Granola", (150, 110, 60), (235, 210, 160)),
    ("Pasta", (210, 180, 90), (250, 235, 190)),
    ("Glaze", (80, 30, 30), (220, 160, 140)),
    ("Coffee", (60, 40, 30), (200, 170, 140)),
    ("Herbs", (50, 110, 60), (190, 230, 190)),
    ("Butter", (230, 190, 80), (255, 240, 200)),
    ("Pickle", (80, 120, 50), (200, 220, 160)),
    ("Cheese", (230, 190, 70), (255, 240, 190)),
    ("Fruit", (200, 60, 70), (255, 200, 190)),
    ("Broth", (140, 90, 50), (230, 200, 160)),
    ("Flour", (230, 220, 200), (250, 245, 235)),
    ("Syrup", (150, 80, 30), (235, 190, 140)),
    ("Chili", (180, 40, 30), (245, 180, 160)),
    ("Gift", (120, 80, 140), (230, 210, 240)),
    ("Box", (90, 110, 140), (200, 220, 240)),
]


def inject_css() -> None:
    for niche in NICHES:
        html = PREVIEWS / "sites" / "premium" / niche / "index.html"
        text = html.read_text(encoding="utf-8")
        if "vitrine-hero-photo-fix" in text:
            print(f"{niche}: css already")
            continue
        if "</head>" in text:
            text = text.replace("</head>", CSS + "\n</head>", 1)
        else:
            text = CSS + text
        html.write_text(text, encoding="utf-8")
        print(f"{niche}: css injected")


def product_plate(label: str, jar: tuple[int, int, int], bg: tuple[int, int, int]) -> Image.Image:
    im = Image.new("RGB", (1000, 1000), bg)
    d = ImageDraw.Draw(im)
    d.ellipse((300, 720, 700, 860), fill=(0, 0, 0))
    d.rounded_rectangle((340, 280, 660, 760), radius=60, fill=jar)
    d.rounded_rectangle((380, 200, 620, 300), radius=20, fill=tuple(max(0, c - 30) for c in jar))
    d.rectangle((400, 160, 600, 210), fill=(230, 230, 230))
    d.rectangle((360, 450, 640, 580), fill=(250, 250, 248))
    try:
        font = ImageFont.truetype("arial.ttf", 48)
        font_sm = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
        font_sm = font
    d.text((500, 515), label, fill=(30, 30, 30), font=font, anchor="mm")
    d.text((500, 900), "FeinKost", fill=(80, 80, 80), font=font_sm, anchor="mm")
    return im


def rebuild_food_products() -> None:
    food = PREVIEWS / "stores" / "premium" / "food" / "assets" / "images"
    food.mkdir(parents=True, exist_ok=True)
    hashes: set[str] = set()
    for i, (label, jar, bg) in enumerate(PRODUCTS, start=1):
        path = food / f"product_{i}.jpg"
        product_plate(label, jar, bg).save(path, "JPEG", quality=90)
        hashes.add(hashlib.md5(path.read_bytes()).hexdigest())
    product_plate(*PRODUCTS[0]).save(food / "product.jpg", "JPEG", quality=90)
    print(f"food unique plates: {len(hashes)}/{len(PRODUCTS)}")


if __name__ == "__main__":
    inject_css()
    rebuild_food_products()
