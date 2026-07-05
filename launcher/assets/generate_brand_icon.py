"""DEPRECATED — use scripts/generate_brand_assets.py from brand/genesis-mark-master.svg."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "genesis-icon.png"
SIZE = 512

# Brand tokens (RC2)
COLOR_TOP = (91, 141, 239)  # #5b8def
COLOR_BOTTOM = (79, 70, 229)  # #4f46e5
RADIUS = int(SIZE * 0.25)


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _gradient_bg() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for y in range(SIZE):
        t = y / max(SIZE - 1, 1)
        r = _lerp(COLOR_TOP[0], COLOR_BOTTOM[0], t)
        g = _lerp(COLOR_TOP[1], COLOR_BOTTOM[1], t)
        b = _lerp(COLOR_TOP[2], COLOR_BOTTOM[2], t)
        for x in range(SIZE):
            img.putpixel((x, y), (r, g, b, 255))
    # Rounded mask
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), RADIUS, fill=255)
    bg = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    bg.paste(img, mask=mask)
    return bg


def main() -> None:
    img = _gradient_bg()
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arialbd.ttf", int(SIZE * 0.42))
    except OSError:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", int(SIZE * 0.42))
        except OSError:
            font = ImageFont.load_default()
    text = "G"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (SIZE - tw) // 2 - bbox[0]
    y = (SIZE - th) // 2 - bbox[1] - int(SIZE * 0.02)
    draw.text((x, y), text, fill=(255, 255, 255, 242), font=font)
    img.save(OUTPUT, format="PNG")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
