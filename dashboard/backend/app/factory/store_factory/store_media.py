"""Commercial Store media — real hero + product photos (not letter placeholders).

Seeds assets/images/ during write_storefront so Premium Store can answer:
«Купил бы я здесь товар?»
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

# Category → showcase niche for hero/banner fallbacks (must match niche character)
_CATEGORY_SHOWCASE: dict[str, str] = {
    # Map store category → niche_scene palette (unique per niche — Law №4)
    "clothing": "fashion",
    "fashion": "fashion",
    "beauty": "beauty",
    "electronics": "electronics",
    "computer": "it_support",
    "furniture": "furniture",
    "realestate": "realestate",
    "accessories": "accessories",
    "jewelry": "jewelry",
    "auto": "auto",
    "food": "food",
    "restaurant": "restaurant",
    "coffee": "coffee",
    "pets": "pets",
    "sports": "sports",
    "fitness": "fitness",
    "handwerk": "handwerk",
    "dachreinigung": "dachreinigung",
    "zaunbau": "zaunbau",
    "gartenpflege": "gartenpflege",
    "psychology": "psychology",
    "therapy": "psychology",
    "cleaning": "cleaning",
    "auto_detailing": "auto_detailing",
    "orthodontics": "orthodontics",
    "books": "psychology",
    "it_parts": "it_support",
    "solar": "energy",
    "auto_parts": "auto_parts",
    "maler": "maler",
    "wine": "restaurant",
    "optics": "electronics",
    "other": "generic",
}

# Soft studio palettes live in niche_scene_media — store_media only seeds files.


def _repo_showcases() -> Path:
    # …/dashboard/backend/app/factory/store_factory → …/dashboard/backend
    return Path(__file__).resolve().parents[3] / "_research_3d" / "showcases"


def _stock_root() -> Path:
    return Path(__file__).resolve().parent / "stock"


def _write_studio_jpeg(
    dest: Path,
    *,
    category: str,
    seed: str,
    label: str = "",
    size: tuple[int, int] = (900, 1120),
    hero: bool = False,
) -> None:
    """Niche-character still (DE form brief) — same family for all package tiers."""
    from app.factory.niche_scene_media import write_niche_scene

    cat = (category or "other").strip().lower()
    niche = _CATEGORY_SHOWCASE.get(cat, cat)
    write_niche_scene(
        dest,
        niche_id=niche if niche != "generic" else cat,
        seed=seed,
        label=label,
        role="hero" if hero else "product",
        size=size if not hero else (1600, 900),
    )


def _pick_showcase_hero(category: str, package_id: str = "business") -> Path | None:
    niche = _CATEGORY_SHOWCASE.get((category or "").lower(), "generic")
    root = _repo_showcases() / niche
    if not root.is_dir():
        root = _repo_showcases() / "generic"
    pid = (package_id or "business").strip().lower() or "business"
    # Prefer the purchased tier pack, then step down / up — never always Premium first
    tier_order = {
        "basic": ("basic", "business", "premium"),
        "business": ("business", "premium", "basic"),
        "premium": ("premium", "business", "basic"),
    }.get(pid, ("business", "premium", "basic"))
    candidates: list[Path] = []
    for tier in tier_order:
        sub = root / "hero_pack" / tier
        if not sub.is_dir():
            continue
        for name in ("hero_1.jpg", "hero_2.jpg", "hero_3.jpg", "banner.jpg", "showcase.jpg", "preview.jpg"):
            p = sub / name
            if p.is_file():
                candidates.append(p)
        candidates.extend(sorted(sub.glob("*.jpg"))[:6])
    if root.is_dir():
        for name in ("hero_1.jpg", "banner.jpg", "showcase.jpg", "preview.jpg"):
            p = root / name
            if p.is_file():
                candidates.append(p)
    for p in candidates:
        if "hero" in p.name.lower():
            return p
    return candidates[0] if candidates else None


def _pick_showcase_product(category: str, index: int) -> Path | None:
    niche = _CATEGORY_SHOWCASE.get((category or "").lower(), "generic")
    products = _repo_showcases() / niche / "products"
    if not products.is_dir():
        return None
    previews = sorted(products.glob("*/preview.jpg"))
    if not previews:
        previews = sorted(products.glob("**/*.jpg"))
    if not previews:
        return None
    return previews[index % len(previews)]


def _stock_file(category: str, name: str) -> Path | None:
    cat = (category or "other").strip().lower()
    for key in (cat, _CATEGORY_SHOWCASE.get(cat, ""), "other"):
        if not key:
            continue
        p = _stock_root() / key / name
        if p.is_file():
            return p
    return None


def _pick_public_preview_hero(category: str, package_id: str = "premium") -> Path | None:
    """Prefer real site-gallery heroes already proven readable (Owner gold standard)."""
    niche_map = {
        "food": "restaurant",
        "coffee": "restaurant",
        "beauty": "beauty",
        "auto": "auto",
        "clothing": "fashion",
        "fashion": "fashion",
        "accessories": "fashion",
        "jewelry": "jewelry",
        "psychology": "psychology",
        "furniture": "realestate",
        "electronics": "computer",
        "pets": "gartenpflege",
        "sports": "fitness",
        "handwerk": "handwerk",
        "dachreinigung": "dachreinigung",
        "zaunbau": "zaunbau",
        "gartenpflege": "gartenpflege",
    }
    niche = niche_map.get((category or "").lower(), "")
    if not niche:
        return None
    # dashboard/backend/app/factory/store_factory → dashboard/frontend/public
    public = Path(__file__).resolve().parents[4] / "frontend" / "public" / "package-previews" / "sites"
    pid = (package_id or "premium").strip().lower() or "premium"
    for tier in (pid, "premium", "business", "basic"):
        base = public / tier / niche / "assets"
        for name in ("hero.jpg", "gallery.jpg", "background.jpg"):
            p = base / name
            if p.is_file() and p.stat().st_size > 20_000:
                return p
        pack = base / "hero_pack"
        if pack.is_dir():
            for name in ("hero_1.jpg", "hero_2.jpg", "banner.jpg", "gallery.jpg"):
                p = pack / name
                if p.is_file() and p.stat().st_size > 20_000:
                    return p
    return None


def seed_store_media(
    product_dir: Path,
    *,
    category: str,
    products: list[dict[str, Any]],
    package_id: str = "business",
) -> dict[str, Any]:
    """Write hero/banner/product JPGs and attach ``image`` paths on products."""
    img_dir = product_dir / "assets" / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    cat = (category or "other").strip().lower()
    written: list[str] = []

    # --- Hero ---
    # Always prefer niche-character stills for categories without proven stock.
    # Never map jewelry/pets/sports onto beauty/generic salon photos.
    hero_dest = img_dir / "hero.jpg"
    craft = cat in (
        "dachreinigung",
        "zaunbau",
        "gartenpflege",
        "handwerk",
        "jewelry",
        "pets",
        "sports",
        "coffee",
        "fitness",
    )
    hero_src = None
    if not craft:
        hero_src = (
            _pick_public_preview_hero(cat, package_id)
            or _stock_file(cat, "hero.jpg")
            or _pick_showcase_hero(cat, package_id)
        )
    if hero_src and hero_src.is_file():
        shutil.copy2(hero_src, hero_dest)
    else:
        _write_studio_jpeg(
            hero_dest,
            category=cat,
            seed=f"hero-{package_id}-{cat}",
            label="",
            hero=True,
        )
    written.append("assets/images/hero.jpg")

    # --- Banner ---
    banner_dest = img_dir / "banner.jpg"
    banner_src = _stock_file(cat, "banner.jpg")
    if not banner_src:
        niche = _CATEGORY_SHOWCASE.get(cat, "generic")
        pid = (package_id or "business").strip().lower() or "business"
        tier_order = {
            "basic": ("basic", "business", "premium"),
            "business": ("business", "premium", "basic"),
            "premium": ("premium", "business", "basic"),
        }.get(pid, ("business", "premium", "basic"))
        for tier in tier_order:
            for name in ("banner.jpg", "showcase.jpg", "cta.jpg"):
                p = _repo_showcases() / niche / "hero_pack" / tier / name
                if p.is_file():
                    banner_src = p
                    break
            if banner_src:
                break
    if banner_src and banner_src.is_file():
        shutil.copy2(banner_src, banner_dest)
    else:
        _write_studio_jpeg(
            banner_dest,
            category=cat,
            seed=f"banner-{package_id}",
            label="Collection",
            size=(1600, 600),
            hero=True,
        )
    written.append("assets/images/banner.jpg")

    # --- Category strip fallback ---
    cat_dest = img_dir / "category.jpg"
    shutil.copy2(banner_dest, cat_dest)
    written.append("assets/images/category.jpg")

    # --- Products ---
    default_product = img_dir / "product.jpg"
    for i, p in enumerate(products):
        if not isinstance(p, dict):
            continue
        fname = f"product_{i + 1}.jpg"
        dest = img_dir / fname
        src = None if craft else (_stock_file(cat, fname) or _pick_showcase_product(cat, i))
        name = str(p.get("name") or f"Product {i + 1}")
        if src and src.is_file():
            shutil.copy2(src, dest)
        else:
            _write_studio_jpeg(
                dest,
                category=cat,
                seed=str(p.get("id") or i),
                label=name,
            )
        rel = f"assets/images/{fname}"
        p["image"] = rel
        p["image_slot"] = rel
        written.append(rel)
        if i == 0:
            shutil.copy2(dest, default_product)
            written.append("assets/images/product.jpg")

    if products and not default_product.is_file():
        shutil.copy2(hero_dest, default_product)

    # Explicit labeled fallback — never silently reuse one product plate.
    missing = img_dir / "missing.jpg"
    _write_studio_jpeg(
        missing,
        category=cat,
        seed=f"missing-{package_id}-{cat}",
        label="Bild fehlt",
        size=(900, 1120),
    )
    written.append("assets/images/missing.jpg")

    return {
        "ok": True,
        "category": cat,
        "hero": "assets/images/hero.jpg",
        "banner": "assets/images/banner.jpg",
        "files": written,
        "product_images": sum(1 for p in products if isinstance(p, dict) and p.get("image")),
    }


__all__ = ["seed_store_media"]
