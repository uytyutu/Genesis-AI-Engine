"""Build genesis.ico from concept PNG — all standard Windows sizes."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "genesis-icon.png"
OUTPUT = ROOT / "genesis.ico"

SIZES = (256, 128, 64, 48, 32, 16)


def _crop_focus(im: Image.Image, top_ratio: float, side_ratio: float) -> Image.Image:
    """Center-crop to emphasize the gear + G (drop bottom text band)."""
    w, h = im.size
    crop_h = int(h * top_ratio)
    crop_w = int(w * side_ratio)
    left = (w - crop_w) // 2
    top = int(h * 0.04)
    return im.crop((left, top, left + crop_w, top + crop_h))


def _render(size: int, source: Image.Image) -> Image.Image:
    if size >= 128:
        base = source
    elif size >= 48:
        base = _crop_focus(source, top_ratio=0.82, side_ratio=0.88)
    elif size >= 32:
        base = _crop_focus(source, top_ratio=0.72, side_ratio=0.78)
    else:
        base = _crop_focus(source, top_ratio=0.62, side_ratio=0.68)

    img = base.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    if size <= 32:
        img = ImageEnhance.Contrast(img).enhance(1.12)
        img = ImageEnhance.Sharpness(img).enhance(1.35)
        img = img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=90, threshold=2))
    return img


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Source not found: {SOURCE}")

    source = Image.open(SOURCE)
    frames = [_render(s, source) for s in SIZES]
    frames[0].save(
        OUTPUT,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=frames[1:],
    )
    print(f"Wrote {OUTPUT} ({', '.join(f'{s}x{s}' for s in SIZES)})")


if __name__ == "__main__":
    main()
