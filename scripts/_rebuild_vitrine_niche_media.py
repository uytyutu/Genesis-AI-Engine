"""Rebuild public vitrine niche media from existing showcase/stock photos (no live Image API)."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public"
SHOW = ROOT / "dashboard" / "backend" / "_research_3d" / "showcases"
STOCK = ROOT / "dashboard" / "backend" / "app" / "factory" / "store_factory" / "stock"
VITRINE = PUBLIC / "vitrine"

# Prefer unique real photos per niche. If None → inventory gap (Pillow niche scene as last resort).
WEBSITE_HERO_SRC: dict[str, Path | None] = {
    "beauty": SHOW / "beauty" / "hero_pack" / "business" / "hero_1.jpg",
    "cleaning": SHOW / "green" / "hero_pack" / "business" / "hero_1.jpg",  # clean/outdoor inventory
    "it_support": SHOW / "computer" / "hero_pack" / "business" / "hero_1.jpg",
    "dental": SHOW / "dental" / "hero_pack" / "business" / "hero_1.jpg",
    "restaurant": None,  # no restaurant showcase pack
    "handwerk": SHOW / "handwerk" / "hero_pack" / "business" / "hero_1.jpg",
    "law": SHOW / "law" / "hero_pack" / "business" / "hero_1.jpg",
    "auto": SHOW / "auto" / "hero_pack" / "business" / "hero_1.jpg",
}

WEBSITE_GALLERY_SRC: dict[str, Path | None] = {
    "beauty": SHOW / "beauty" / "hero_pack" / "business" / "services.jpg",
    "cleaning": SHOW / "green" / "hero_pack" / "business" / "services.jpg",
    "it_support": SHOW / "computer" / "hero_pack" / "business" / "services.jpg",
    "dental": SHOW / "dental" / "hero_pack" / "business" / "services.jpg",
    "restaurant": None,
    "handwerk": SHOW / "handwerk" / "hero_pack" / "business" / "services.jpg",
    "law": SHOW / "law" / "hero_pack" / "business" / "services.jpg",
    "auto": SHOW / "auto" / "hero_pack" / "business" / "services.jpg",
}

STORE_HERO_SRC: dict[str, Path | None] = {
    "beauty": STOCK / "beauty" / "banner.jpg",
    # No dedicated cleaning product hero — do not reuse website green garden.
    "cleaning_shop": None,
    "electronics": STOCK / "electronics" / "hero.jpg",
    "food": None,  # no food stock
    "furniture": STOCK / "furniture" / "hero.jpg",
    "fashion": STOCK / "fashion" / "hero.jpg",
}

STORE_FOLDER = {
    "beauty": "beauty",
    "cleaning_shop": "cleaning_shop",
    "electronics": "electronics",
    "food": "food",
    "furniture": "furniture",
    "fashion": "fashion",
}

VITRINE_MAP = {
    "web-beauty.jpg": ("website", "beauty"),
    "web-cleaning.jpg": ("website", "cleaning"),
    "web-it.jpg": ("website", "it_support"),
    "web-dental.jpg": ("website", "dental"),
    "web-restaurant.jpg": ("website", "restaurant"),
    "web-handwerk.jpg": ("website", "handwerk"),
    "web-law.jpg": ("website", "law"),
    "web-auto.jpg": ("website", "auto"),
    "store-beauty.jpg": ("store", "beauty"),
    "store-cleaning.jpg": ("store", "cleaning_shop"),
    "store-electronics.jpg": ("store", "electronics"),
    "store-food.jpg": ("store", "food"),
    "store-furniture.jpg": ("store", "furniture"),
    "store-fashion.jpg": ("store", "fashion"),
}


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()[:12]


def _copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def _pillow_fallback(dest: Path, niche: str, *, role: str, seed: str) -> None:
    import sys

    sys.path.insert(0, str(ROOT / "dashboard" / "backend"))
    from app.factory.niche_scene_media import write_niche_scene

    write_niche_scene(
        dest,
        niche_id=niche,
        seed=seed,
        role=role,  # type: ignore[arg-type]
        size=(1600, 900) if role == "hero" else (1200, 800),
        label=niche.replace("_", " "),
    )


def apply_website(niche: str) -> dict:
    dest_dir = PUBLIC / "package-previews" / "sites" / "premium" / niche / "assets"
    hero_src = WEBSITE_HERO_SRC.get(niche)
    gal_src = WEBSITE_GALLERY_SRC.get(niche)
    status = "ok"
    hero = dest_dir / "hero.jpg"
    gallery = dest_dir / "gallery.jpg"
    if hero_src and hero_src.is_file() and hero_src.stat().st_size >= 80000:
        _copy(hero_src, hero)
        # also replace known generic hero_pack slots so CSS packs aren't identical
        pack = dest_dir / "hero_pack"
        if pack.is_dir():
            for name in ("hero_1.jpg", "hero_3.jpg", "showcase.jpg", "banner.jpg", "footer.jpg"):
                target = pack / name
                if target.exists() or True:
                    _copy(hero_src if name != "showcase.jpg" else (gal_src or hero_src), target)
    else:
        _pillow_fallback(hero, niche if niche != "it_support" else "it_support", role="hero", seed=f"vitrine-web-hero|{niche}")
        status = "missing_showcase_pillow_fallback"
    if gal_src and gal_src.is_file() and gal_src.stat().st_size >= 80000:
        _copy(gal_src, gallery)
    else:
        _pillow_fallback(gallery, niche if niche != "it_support" else "computer", role="gallery", seed=f"vitrine-web-gal|{niche}")
        if status == "ok":
            status = "gallery_pillow_fallback"
    return {
        "niche": niche,
        "demo": f"sites/premium/{niche}",
        "hero": str(hero.relative_to(PUBLIC)),
        "hero_bytes": hero.stat().st_size,
        "hero_hash": _md5(hero),
        "gallery": str(gallery.relative_to(PUBLIC)),
        "gallery_bytes": gallery.stat().st_size,
        "gallery_hash": _md5(gallery),
        "status": status,
    }


def apply_store(folder: str, niche_key: str) -> dict:
    dest_dir = (
        PUBLIC / "package-previews" / "stores" / "premium" / folder / "assets" / "images"
    )
    hero_src = STORE_HERO_SRC.get(folder)
    hero = dest_dir / "hero.jpg"
    status = "ok"
    products_ok = 0
    if hero_src and hero_src.is_file() and hero_src.stat().st_size >= 40000:
        _copy(hero_src, hero)
    else:
        niche = "food" if folder == "food" else ("cleaning" if folder == "cleaning_shop" else niche_key)
        _pillow_fallback(hero, niche, role="hero", seed=f"vitrine-store-hero|{folder}")
        status = "missing_stock_pillow_fallback"

    # seed products from stock when available (never treat STOCK root as a niche folder)
    stock_map = {
        "beauty": "beauty",
        "electronics": "electronics",
        "furniture": "furniture",
        "fashion": "fashion",
    }
    stock_key = stock_map.get(folder)
    stock_dir = (STOCK / stock_key) if stock_key else None
    products: list[Path] = sorted(stock_dir.glob("product_*.jpg")) if stock_dir and stock_dir.is_dir() else []
    if products:
        for i, src in enumerate(products[:12], start=1):
            _copy(src, dest_dir / f"product_{i}.jpg")
            products_ok += 1
        # pad to 8 unique niche scenes if stock is short
        for i in range(products_ok + 1, 9):
            niche = niche_key
            _pillow_fallback(
                dest_dir / f"product_{i}.jpg",
                niche,
                role="product",
                seed=f"vitrine-store-prod|{folder}|{i}",
            )
            products_ok += 1
    else:
        niche = (
            "food"
            if folder == "food"
            else "cleaning"
            if folder == "cleaning_shop"
            else niche_key
        )
        for i in range(1, 9):
            p = dest_dir / f"product_{i}.jpg"
            _pillow_fallback(p, niche, role="product", seed=f"vitrine-store-prod|{folder}|{i}")
            products_ok += 1
        if "missing" not in status:
            status = "products_pillow_no_stock"

    # never leave shared product.jpg as generic showcase
    default_p = dest_dir / "product.jpg"
    first = dest_dir / "product_1.jpg"
    if first.is_file():
        _copy(first, default_p)

    miss = dest_dir / "missing.jpg"
    niche = "food" if folder == "food" else ("cleaning" if folder == "cleaning_shop" else niche_key)
    _pillow_fallback(miss, niche, role="gallery", seed=f"missing|{folder}")

    return {
        "niche": folder,
        "demo": f"stores/premium/{folder}",
        "hero": str(hero.relative_to(PUBLIC)),
        "hero_bytes": hero.stat().st_size,
        "hero_hash": _md5(hero),
        "gallery": "-",
        "product_assets": products_ok,
        "status": status,
    }


def rebuild_vitrine(rows: list[dict]) -> None:
    VITRINE.mkdir(parents=True, exist_ok=True)
    by_demo = {r["demo"]: r for r in rows}
    for thumb, (kind, key) in VITRINE_MAP.items():
        demo = f"sites/premium/{key}" if kind == "website" else f"stores/premium/{key}"
        row = by_demo.get(demo)
        if not row:
            continue
        src = PUBLIC / row["hero"]
        if src.is_file():
            _copy(src, VITRINE / thumb)
    # drop legacy lumia thumbs from public set (leave files but unused)
    print("vitrine thumbs refreshed")


def main() -> None:
    rows: list[dict] = []
    print("niche|demo|hero_bytes|hash|products|status")
    for niche in WEBSITE_HERO_SRC:
        r = apply_website(niche)
        rows.append(r)
        print(f"{r['niche']}|website|{r['hero_bytes']}|{r['hero_hash']}|-| {r['status']}")
    for folder, niche_key in STORE_FOLDER.items():
        r = apply_store(folder, niche_key)
        rows.append(r)
        print(
            f"{r['niche']}|store|{r['hero_bytes']}|{r['hero_hash']}|{r.get('product_assets')}| {r['status']}"
        )
    rebuild_vitrine(rows)
    hashes: dict[str, list[str]] = {}
    for r in rows:
        hashes.setdefault(r["hero_hash"], []).append(r["demo"])
    dupes = {k: v for k, v in hashes.items() if len(v) > 1}
    print("DUPES", dupes or "none")
    missing = [r for r in rows if "missing" in r["status"] or "pillow" in r["status"]]
    print("INVENTORY_GAPS", [r["demo"] for r in missing] or "none")


if __name__ == "__main__":
    main()
