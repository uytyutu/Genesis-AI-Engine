"""Public vitrine quality gate — Website/Store by niche; no Basic/Business/Premium."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public"
CATALOG_TS = (
    ROOT
    / "dashboard"
    / "frontend"
    / "app"
    / "lib"
    / "publicVitrineCatalog.ts"
)
HUB_TS = (
    ROOT
    / "dashboard"
    / "frontend"
    / "app"
    / "components"
    / "storefront"
    / "AppStoreHub.tsx"
)
COMMERCIAL_TS = (
    ROOT / "dashboard" / "frontend" / "app" / "lib" / "commercialCatalog.ts"
)

LEGACY_MARKERS = (
    "client-forms/",
    "studio-lumia",
    "PUBLIC_DENTAL_TIER_COMPARE",
    "Gleiche Nische",
    "tierCompare",
)

FORBIDDEN_PUBLIC_HREFS = (
    "/package-previews/sites/basic/",
    "/package-previews/sites/business/",
    "/package-previews/client-forms/",
)


def test_public_vitrine_catalog_exists() -> None:
    assert CATALOG_TS.is_file()
    text = CATALOG_TS.read_text(encoding="utf-8")
    assert "PUBLIC_VITRINE_EXAMPLES" in text
    assert "PUBLIC_VITRINE_WEBSITES" in text
    assert "PUBLIC_VITRINE_STORES" in text
    assert "PUBLIC_VITRINE_LEGACY_BLOCKLIST" in text
    assert "PUBLIC_DENTAL_TIER_COMPARE" not in text


def test_app_store_hub_uses_catalog_not_tiers() -> None:
    hub = HUB_TS.read_text(encoding="utf-8")
    assert "PUBLIC_VITRINE_WEBSITES" in hub
    assert "PUBLIC_VITRINE_STORES" in hub
    assert "PUBLIC_VITRINE_THUMB_VERSION" in hub
    for marker in LEGACY_MARKERS:
        assert marker not in hub, f"legacy still linked: {marker}"


def test_commercial_price_ssot_is_499() -> None:
    text = COMMERCIAL_TS.read_text(encoding="utf-8")
    assert "standalone: 499" in text
    assert "connected: 499" in text
    assert "connected_monthly: 99" in text
    hub = HUB_TS.read_text(encoding="utf-8")
    assert "Starter €199" not in hub
    assert "Business €399" not in hub
    assert "Premium €699" not in hub
    assert "LANDING_PACKAGES_EUR" in hub


def test_all_public_demos_exist_with_media_floor() -> None:
    text = CATALOG_TS.read_text(encoding="utf-8")
    hrefs = sorted(set(re.findall(r'href:\s*"(/package-previews/[^"]+)"', text)))
    thumbs = sorted(set(re.findall(r'thumb:\s*"(/vitrine/[^"]+)"', text)))
    assert len(hrefs) >= 10
    assert len(thumbs) >= 10

    for forbidden in FORBIDDEN_PUBLIC_HREFS:
        for href in hrefs:
            assert forbidden not in href, f"forbidden public href: {href}"

    hero_hashes: dict[str, list[str]] = {}
    for href in hrefs:
        rel = href.lstrip("/")
        if href.endswith("/"):
            index = PUBLIC / rel / "index.html"
        else:
            index = PUBLIC / rel
        assert index.is_file(), f"missing demo: {href}"
        folder = index.parent
        hero_candidates = [
            folder / "assets" / "hero.jpg",
            folder / "assets" / "images" / "hero.jpg",
            folder / "assets" / "gallery.jpg",
        ]
        hero = next((p for p in hero_candidates if p.is_file()), None)
        assert hero is not None, f"missing hero media: {href}"
        assert hero.stat().st_size >= 8000, f"tiny hero: {href}"
        dig = hashlib.md5(hero.read_bytes()).hexdigest()
        hero_hashes.setdefault(dig, []).append(href)

    dupes = {k: v for k, v in hero_hashes.items() if len(v) > 1}
    assert not dupes, f"duplicate heroes across demos: {dupes}"

    for thumb in thumbs:
        p = PUBLIC / thumb.lstrip("/")
        assert p.is_file(), f"missing thumb: {thumb}"
        assert p.stat().st_size >= 8000, f"tiny thumb: {thumb}"


def test_store_demos_have_unique_product_slots() -> None:
    stores = [
        "beauty",
        "cleaning_shop",
        "electronics",
        "food",
        "furniture",
        "fashion",
    ]
    for folder in stores:
        img = PUBLIC / "package-previews" / "stores" / "premium" / folder / "assets" / "images"
        assert img.is_dir(), folder
        hero = img / "hero.jpg"
        assert hero.is_file() and hero.stat().st_size >= 8000
        missing = img / "missing.jpg"
        assert missing.is_file(), f"explicit missing fallback required: {folder}"
        hashes = []
        for i in range(1, 9):
            p = img / f"product_{i}.jpg"
            assert p.is_file(), f"{folder} product_{i}"
            hashes.append(hashlib.md5(p.read_bytes()).hexdigest())
        assert len(set(hashes)) >= 4, f"too many identical products: {folder}"


def test_no_legacy_blocklist_paths_on_public_catalog() -> None:
    text = CATALOG_TS.read_text(encoding="utf-8")
    hrefs = re.findall(r'href:\s*"([^"]+)"', text)
    for h in hrefs:
        for marker in ("client-forms/", "studio-lumia", "/sites/basic/", "/sites/business/"):
            assert marker not in h, f"legacy href in catalog: {h}"
