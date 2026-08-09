"""Give each public vitrine demo a unique background treatment + hero refresh.

Uses existing showcase / local assets only (no Live Image API).
Applies niche-specific color grade so sites/stores do not share the same look.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public"
PREVIEWS = PUBLIC / "package-previews"
SHOW = ROOT / "dashboard" / "backend" / "_research_3d" / "showcases"
VITRINE = PUBLIC / "vitrine"

SITE_SOURCES = {
    "beauty": SHOW / "beauty" / "hero_pack" / "business",
    "cleaning": SHOW / "green" / "hero_pack" / "business",
    "it_support": SHOW / "computer" / "hero_pack" / "business",
    "dental": SHOW / "dental" / "hero_pack" / "business",
    "handwerk": SHOW / "handwerk" / "hero_pack" / "business",
    "law": SHOW / "law" / "hero_pack" / "business",
    "auto": SHOW / "auto" / "hero_pack" / "business",
    "restaurant": PREVIEWS / "vitrine",  # gourmet if present
}

# (brightness, contrast, color, optional colorize hex or None)
GRADES = {
    "beauty": (1.05, 1.08, 1.12, (255, 220, 220)),
    "cleaning": (1.1, 1.05, 1.05, (200, 255, 240)),
    "it_support": (0.85, 1.2, 0.9, (180, 210, 255)),
    "dental": (1.12, 1.05, 0.95, (210, 235, 255)),
    "restaurant": (0.9, 1.15, 1.2, (255, 200, 150)),
    "handwerk": (0.95, 1.18, 1.05, (255, 220, 170)),
    "law": (1.0, 1.1, 0.85, (230, 225, 210)),
    "auto": (0.8, 1.25, 1.05, (255, 160, 140)),
}

STORE_GRADES = {
    "beauty": (1.08, 1.1, 1.15, (255, 200, 220)),
    "cleaning_shop": (1.1, 1.05, 1.05, (180, 255, 230)),
    "electronics": (0.75, 1.3, 0.85, (120, 220, 255)),
    "food": (1.05, 1.15, 1.25, (255, 190, 120)),
    "furniture": (1.0, 1.08, 0.9, (220, 210, 190)),
    "fashion": (0.7, 1.2, 0.8, (200, 190, 180)),
}


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()[:12]


def _list_jpgs(folder: Path) -> list[Path]:
    if not folder or not folder.exists():
        return []
    out: list[Path] = []
    for p in sorted(folder.rglob("*")):
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and p.is_file():
            out.append(p)
    return out


def grade(img: Image.Image, bright: float, contrast: float, color: float, tint) -> Image.Image:
    im = img.convert("RGB")
    im = ImageEnhance.Brightness(im).enhance(bright)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(color)
    if tint:
        wash = Image.new("RGB", im.size, tint)
        im = Image.blend(im, wash, 0.18)
    return im


def save_graded(src: Path, dest: Path, g) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        out = grade(im, *g)
        out.save(dest, "JPEG", quality=88, optimize=True)


def pick(sources: list[Path], i: int) -> Path | None:
    if not sources:
        return None
    return sources[i % len(sources)]


def refresh_site(niche: str) -> str:
    dest_root = PREVIEWS / "sites" / "premium" / niche / "assets"
    src_dir = SITE_SOURCES.get(niche)
    sources = _list_jpgs(src_dir) if src_dir else []
    if niche == "restaurant":
        # Prefer food/restaurant named files
        gourmet = [
            p
            for p in sources
            if any(k in p.name.lower() for k in ("food", "rest", "dish", "gourmet", "plate", "dining"))
        ]
        if gourmet:
            sources = gourmet + [p for p in sources if p not in gourmet]
    if not sources:
        # fall back to existing assets
        sources = _list_jpgs(dest_root)
    if not sources:
        return f"{niche}: no media"
    g = GRADES[niche]
    slots = [
        ("hero.jpg", 0),
        ("background.jpg", 1),
        ("gallery.jpg", 2),
        ("section_story.jpg", 3),
        ("section_services.jpg", 4),
        ("section_contact.jpg", 5),
        ("hero_pack/hero_1.jpg", 0),
        ("hero_pack/background_1.jpg", 1),
        ("hero_pack/footer.jpg", 6),
        ("hero_pack/banner.jpg", 2),
        ("hero_pack/showcase.jpg", 3),
    ]
    written = 0
    for rel, idx in slots:
        src = pick(sources, idx + written)
        if not src:
            continue
        save_graded(src, dest_root / rel, g)
        written += 1
    # thumb
    hero = dest_root / "hero.jpg"
    if hero.exists():
        thumb = VITRINE / f"web-{niche if niche != 'it_support' else 'it'}.jpg"
        if niche == "it_support":
            thumb = VITRINE / "web-it.jpg"
        with Image.open(hero) as im:
            im = ImageOps.fit(im.convert("RGB"), (960, 640), Image.Resampling.LANCZOS)
            im = grade(im, *g)
            thumb.parent.mkdir(parents=True, exist_ok=True)
            im.save(thumb, "JPEG", quality=86, optimize=True)
    return f"{niche}: {written} slots h={_md5(hero) if hero.exists() else '?'}"


def refresh_store(niche: str) -> str:
    dest_root = PREVIEWS / "stores" / "premium" / niche
    assets = dest_root / "assets"
    sources = _list_jpgs(assets) or _list_jpgs(dest_root)
    if not sources:
        return f"store/{niche}: no media"
    g = STORE_GRADES[niche]
    # Grade product images lightly + hero-like first images
    targets = []
    for name in ("hero.jpg", "banner.jpg", "store_hero.jpg", "cover.jpg"):
        for p in assets.rglob(name) if assets.exists() else []:
            targets.append(p)
    products = sorted(assets.rglob("product*.jpg"))[:12] if assets.exists() else []
    targets.extend(products)
    if not targets:
        targets = sources[:16]
    n = 0
    for i, dest in enumerate(targets):
        src = pick(sources, i)
        if not src or not dest:
            continue
        try:
            save_graded(src, dest, g)
            n += 1
        except Exception:
            continue
    # thumb
    thumb_name = {
        "beauty": "store-beauty.jpg",
        "cleaning_shop": "store-cleaning.jpg",
        "electronics": "store-electronics.jpg",
        "food": "store-food.jpg",
        "furniture": "store-furniture.jpg",
        "fashion": "store-fashion.jpg",
    }[niche]
    src = targets[0] if targets else sources[0]
    with Image.open(src) as im:
        im = ImageOps.fit(im.convert("RGB"), (960, 640), Image.Resampling.LANCZOS)
        im = grade(im, *g)
        (VITRINE / thumb_name).parent.mkdir(parents=True, exist_ok=True)
        im.save(VITRINE / thumb_name, "JPEG", quality=86, optimize=True)
    return f"store/{niche}: graded {n}"


def main() -> None:
    for niche in SITE_SOURCES:
        print(refresh_site(niche))
    for niche in STORE_GRADES:
        print(refresh_store(niche))
    print("done")


if __name__ == "__main__":
    main()
