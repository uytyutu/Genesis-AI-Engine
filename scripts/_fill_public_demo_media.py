"""Fill public premium demos with real niche photos (no Live Image API).

Replaces pillow placeholders in gallery_*, section_*, reputation/*, store products
using showcase packs + existing vitrine photos + unique crops.
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public"
PREVIEWS = PUBLIC / "package-previews"
SHOW = ROOT / "dashboard" / "backend" / "_research_3d" / "showcases"
STOCK = ROOT / "dashboard" / "backend" / "app" / "factory" / "store_factory" / "stock"
OLD_VITRINE = PREVIEWS / "vitrine"
NEW_VITRINE = PUBLIC / "vitrine"

WEBSITES = {
    "beauty": SHOW / "beauty" / "hero_pack" / "business",
    "cleaning": SHOW / "green" / "hero_pack" / "business",
    "it_support": SHOW / "computer" / "hero_pack" / "business",
    "dental": SHOW / "dental" / "hero_pack" / "business",
    "handwerk": SHOW / "handwerk" / "hero_pack" / "business",
    "law": SHOW / "law" / "hero_pack" / "business",
    "auto": SHOW / "auto" / "hero_pack" / "business",
    "restaurant": None,  # filled from local gourmet photos
}

STORES = {
    "beauty": "beauty",
    "cleaning_shop": "cleaning",
    "electronics": "electronics",
    "food": "food",
    "furniture": "furniture",
    "fashion": "fashion",
}

SITE_SLOT_NAMES = [
    "hero.jpg",
    "gallery.jpg",
    "background.jpg",
    "equipment.jpg",
    "process.jpg",
    "team.jpg",
    "illustration.jpg",
    "before.jpg",
    "after.jpg",
    "before_after.jpg",
    "section_contact.jpg",
    "section_process.jpg",
    "section_services.jpg",
    "section_story.jpg",
    "section_team.jpg",
] + [f"gallery_{i}.jpg" for i in range(1, 19)] + [
    f"illustration_{i}.jpg" for i in range(1, 4)
]

HERO_PACK_NAMES = [
    "hero_1.jpg",
    "hero_2.jpg",
    "hero_3.jpg",
    "showcase.jpg",
    "banner.jpg",
    "footer.jpg",
    "gallery.jpg",
    "services.jpg",
    "cta.jpg",
    "calculator.jpg",
    "background_1.jpg",
    "background_2.jpg",
]


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()[:12]


def _load_pool(paths: list[Path]) -> list[Image.Image]:
    out: list[Image.Image] = []
    for p in paths:
        if not p or not p.is_file() or p.stat().st_size < 20000:
            continue
        try:
            im = Image.open(p).convert("RGB")
        except Exception:
            continue
        # skip near-solid placeholders
        small = im.resize((32, 32))
        colors = small.getcolors(maxcolors=1024) or []
        if len(colors) <= 6 and im.size[0] * im.size[1] > 0:
            # very few colors → likely abstract pillow
            if p.stat().st_size < 90000:
                continue
        out.append(im)
    return out


def _variant(im: Image.Image, seed: int, size: tuple[int, int]) -> Image.Image:
    w, h = im.size
    # unique crop window
    zoom = 0.72 + (seed % 7) * 0.03
    cw, ch = int(w * zoom), int(h * zoom)
    ox = (seed * 37) % max(1, w - cw)
    oy = (seed * 53) % max(1, h - ch)
    crop = im.crop((ox, oy, ox + cw, oy + ch)).resize(size, Image.Resampling.LANCZOS)
    # slight grade so slots don't look identical
    crop = ImageEnhance.Color(crop).enhance(0.92 + (seed % 5) * 0.04)
    crop = ImageEnhance.Contrast(crop).enhance(0.95 + (seed % 4) * 0.03)
    if seed % 3 == 0:
        crop = crop.filter(ImageFilter.SMOOTH)
    return crop


def _save_jpeg(im: Image.Image, dest: Path, quality: int = 88) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=quality, optimize=True)


def _write_logo(dest: Path, initials: str, color: tuple[int, int, int]) -> None:
    im = Image.new("RGB", (640, 640), (18, 20, 24))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((48, 48, 592, 592), radius=48, fill=color)
    d.rounded_rectangle((120, 120, 520, 520), radius=28, fill=(250, 250, 248))
    try:
        font = ImageFont.truetype("arial.ttf", 160)
    except Exception:
        font = ImageFont.load_default()
    text = initials[:2].upper()
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((640 - tw) / 2, (640 - th) / 2 - 10), text, fill=color, font=font)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "PNG")


def _restaurant_sources() -> list[Path]:
    cands = [
        OLD_VITRINE / "web-restaurant.jpg",
        OLD_VITRINE / "store-food.jpg",
        OLD_VITRINE / "store-furniture.jpg",  # retail interior fallback only if needed
        PREVIEWS / "stores" / "premium" / "wine_shop" / "assets" / "images" / "product.jpg",
    ]
    # Prefer non-generic hashes
    out = []
    for p in cands:
        if not p.is_file():
            continue
        if _md5(p) == "2e7b00d37aa9":
            continue
        out.append(p)
    return out


def _showcase_paths(folder: Path | None) -> list[Path]:
    if not folder or not folder.is_dir():
        return []
    preferred = [
        "hero_1.jpg",
        "hero_2.jpg",
        "services.jpg",
        "cta.jpg",
        "background_1.jpg",
        "background_2.jpg",
        "gallery.jpg",
        "banner.jpg",
    ]
    paths = []
    for name in preferred:
        p = folder / name
        if p.is_file():
            paths.append(p)
    for p in sorted(folder.glob("*.jpg")):
        if p not in paths:
            paths.append(p)
    return paths


def fill_website(niche: str) -> dict:
    dest = PREVIEWS / "sites" / "premium" / niche / "assets"
    dest.mkdir(parents=True, exist_ok=True)
    if niche == "restaurant":
        src_paths = _restaurant_sources()
        status = "ok_local_gourmet" if src_paths else "missing"
    else:
        src_paths = _showcase_paths(WEBSITES.get(niche))
        status = "ok_showcase" if src_paths else "missing"
    pool = _load_pool(src_paths)
    if not pool:
        return {"niche": niche, "status": "NO_POOL", "filled": 0}

    filled = 0
    # hero + gallery primary
    _save_jpeg(_variant(pool[0], 1, (1600, 1000)), dest / "hero.jpg", 90)
    _save_jpeg(_variant(pool[min(1, len(pool) - 1)], 2, (1600, 1000)), dest / "gallery.jpg", 90)
    filled += 2

    for i, name in enumerate(SITE_SLOT_NAMES):
        if name in ("hero.jpg", "gallery.jpg"):
            continue
        im = pool[i % len(pool)]
        size = (1200, 800) if "gallery" in name or "illustration" in name else (1400, 900)
        _save_jpeg(_variant(im, 10 + i, size), dest / name)
        filled += 1

    pack = dest / "hero_pack"
    pack.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(HERO_PACK_NAMES):
        im = pool[i % len(pool)]
        _save_jpeg(_variant(im, 100 + i, (1600, 1000)), pack / name, 90)
        filled += 1

    # reputation team portraits — square crops
    rep = dest / "reputation"
    rep.mkdir(parents=True, exist_ok=True)
    for i in range(4):
        im = pool[i % len(pool)]
        portrait = _variant(im, 200 + i, (800, 800))
        _save_jpeg(portrait, rep / f"team_{i}.jpg", 90)
        filled += 1
    for i in range(2):
        im = pool[i % len(pool)]
        _save_jpeg(_variant(im, 300 + i, (1200, 800)), rep / f"case_0_{'before' if i == 0 else 'after'}.jpg")
        filled += 1

    colors = {
        "beauty": (166, 48, 121),
        "cleaning": (34, 120, 90),
        "it_support": (40, 90, 160),
        "dental": (50, 130, 150),
        "restaurant": (180, 90, 40),
        "handwerk": (120, 80, 40),
        "law": (40, 55, 90),
        "auto": (160, 50, 40),
    }
    initials = {
        "beauty": "SM",
        "cleaning": "CL",
        "it_support": "IT",
        "dental": "ZA",
        "restaurant": "TL",
        "handwerk": "HW",
        "law": "RA",
        "auto": "AW",
    }
    _write_logo(dest / "logo.png", initials.get(niche, "VC"), colors.get(niche, (16, 185, 129)))
    filled += 1

    return {
        "niche": niche,
        "status": status,
        "filled": filled,
        "hero_hash": _md5(dest / "hero.jpg"),
        "hero_bytes": (dest / "hero.jpg").stat().st_size,
        "pool": len(pool),
    }


def fill_store(folder: str, niche_key: str) -> dict:
    dest = PREVIEWS / "stores" / "premium" / folder / "assets" / "images"
    dest.mkdir(parents=True, exist_ok=True)
    stock_map = {
        "beauty": STOCK / "beauty",
        "electronics": STOCK / "electronics",
        "furniture": STOCK / "furniture",
        "fashion": STOCK / "fashion",
    }
    paths: list[Path] = []
    stock = stock_map.get(folder)
    if stock and stock.is_dir():
        paths.extend(sorted(stock.glob("*.jpg")))
    if folder == "food":
        paths.extend(_restaurant_sources())
        # also furniture/fashion stock as last resort? NO — keep food-only gourmet
    if folder == "cleaning_shop":
        paths.extend(_showcase_paths(SHOW / "green" / "hero_pack" / "business"))
    # demo store may already have a good hero
    existing_hero = dest / "hero.jpg"
    if existing_hero.is_file() and existing_hero.stat().st_size > 80000 and _md5(existing_hero) != "2e7b00d37aa9":
        paths.insert(0, existing_hero)

    pool = _load_pool(paths)
    if not pool and folder == "food":
        # absolute last resort: old vitrine gourmet
        pool = _load_pool([OLD_VITRINE / "web-restaurant.jpg", OLD_VITRINE / "store-food.jpg"])
    if not pool:
        return {"niche": folder, "status": "NO_POOL", "products": 0}

    _save_jpeg(_variant(pool[0], 1, (1600, 900)), dest / "hero.jpg", 90)
    _save_jpeg(_variant(pool[min(1, len(pool) - 1)], 2, (1600, 700)), dest / "banner.jpg", 90)
    products = 0
    for i in range(1, 25):
        im = pool[i % len(pool)]
        _save_jpeg(_variant(im, 50 + i, (1000, 1000)), dest / f"product_{i}.jpg", 88)
        products += 1
    _save_jpeg(_variant(pool[0], 3, (1000, 1000)), dest / "product.jpg", 88)
    # missing.jpg stays niche-colored but not used as silent product fallback content
    miss = Image.new("RGB", (800, 800), (32, 34, 38))
    d = ImageDraw.Draw(miss)
    d.text((260, 380), "Bild fehlt", fill=(180, 180, 180))
    miss.save(dest / "missing.jpg", "JPEG", quality=80)

    return {
        "niche": folder,
        "status": "ok",
        "products": products,
        "hero_hash": _md5(dest / "hero.jpg"),
        "hero_bytes": (dest / "hero.jpg").stat().st_size,
        "pool": len(pool),
    }


def refresh_public_vitrine() -> None:
    NEW_VITRINE.mkdir(parents=True, exist_ok=True)
    mapping = {
        "web-beauty.jpg": PREVIEWS / "sites/premium/beauty/assets/hero.jpg",
        "web-cleaning.jpg": PREVIEWS / "sites/premium/cleaning/assets/hero.jpg",
        "web-it.jpg": PREVIEWS / "sites/premium/it_support/assets/hero.jpg",
        "web-dental.jpg": PREVIEWS / "sites/premium/dental/assets/hero.jpg",
        "web-restaurant.jpg": PREVIEWS / "sites/premium/restaurant/assets/hero.jpg",
        "web-handwerk.jpg": PREVIEWS / "sites/premium/handwerk/assets/hero.jpg",
        "web-law.jpg": PREVIEWS / "sites/premium/law/assets/hero.jpg",
        "web-auto.jpg": PREVIEWS / "sites/premium/auto/assets/hero.jpg",
        "store-beauty.jpg": PREVIEWS / "stores/premium/beauty/assets/images/hero.jpg",
        "store-cleaning.jpg": PREVIEWS / "stores/premium/cleaning_shop/assets/images/hero.jpg",
        "store-electronics.jpg": PREVIEWS / "stores/premium/electronics/assets/images/hero.jpg",
        "store-food.jpg": PREVIEWS / "stores/premium/food/assets/images/hero.jpg",
        "store-furniture.jpg": PREVIEWS / "stores/premium/furniture/assets/images/hero.jpg",
        "store-fashion.jpg": PREVIEWS / "stores/premium/fashion/assets/images/hero.jpg",
    }
    for name, src in mapping.items():
        if src.is_file():
            shutil.copy2(src, NEW_VITRINE / name)


def main() -> None:
    print("niche|kind|status|hero_bytes|hash|detail")
    hashes: dict[str, list[str]] = {}
    for niche in WEBSITES:
        r = fill_website(niche)
        print(
            f"{r.get('niche')}|website|{r.get('status')}|{r.get('hero_bytes')}|{r.get('hero_hash')}|pool={r.get('pool')} filled={r.get('filled')}"
        )
        if r.get("hero_hash"):
            hashes.setdefault(r["hero_hash"], []).append(f"web:{niche}")
    for folder, key in STORES.items():
        r = fill_store(folder, key)
        print(
            f"{r.get('niche')}|store|{r.get('status')}|{r.get('hero_bytes')}|{r.get('hero_hash')}|pool={r.get('pool')} products={r.get('products')}"
        )
        if r.get("hero_hash"):
            hashes.setdefault(r["hero_hash"], []).append(f"store:{folder}")
    refresh_public_vitrine()
    dupes = {k: v for k, v in hashes.items() if len(v) > 1}
    print("DUPES", dupes or "none")
    print("vitrine refreshed")


if __name__ == "__main__":
    main()
