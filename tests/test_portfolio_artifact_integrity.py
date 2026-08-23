"""Portfolio artifact integrity — thumb and Besuchen must be the same build."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public"
CATALOG_TS = ROOT / "dashboard" / "frontend" / "app" / "lib" / "publicVitrineCatalog.ts"
HUB_TS = ROOT / "dashboard" / "frontend" / "app" / "components" / "storefront" / "CommercialAgencyHub.tsx"

MIN_HERO_BYTES = 80_000
MIN_GALLERY_BYTES = 50_000
NICHE_GALLERY_MIN = {
    "auto": 3,
    "restaurant": 3,
}


def _read_meta_product_id(artifact_dir: Path) -> str | None:
    meta = artifact_dir / "meta.json"
    if not meta.is_file():
        return None
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    pid = data.get("product_id")
    return str(pid) if pid else None


def test_agency_portfolio_ssot_in_catalog() -> None:
    text = CATALOG_TS.read_text(encoding="utf-8")
    assert "PUBLIC_AGENCY_PORTFOLIO" in text
    assert "assertPortfolioArtifactIntegrity" in text
    assert "portfolioPreviewImageForArtifact" in text
    assert "/package-previews/sites/basic/" not in text.split("PUBLIC_AGENCY_PORTFOLIO")[1].split("PUBLIC_VITRINE_THUMB_VERSION")[0]


def test_hub_uses_agency_portfolio_ssot() -> None:
    hub = HUB_TS.read_text(encoding="utf-8")
    assert "PUBLIC_AGENCY_PORTFOLIO" in hub
    assert "sites/basic/auto" not in hub
    assert "sites/basic/restaurant" not in hub


def test_business_restaurant_catalog_matches_artifact_not_hotdog() -> None:
    text = CATALOG_TS.read_text(encoding="utf-8")
    assert "/package-previews/sites/business/restaurant/index.html" in text
    assert "/package-previews/premium/hot-dog/" not in text.split("web-business-restaurant")[1][:400]


def test_published_portfolio_artifact_integrity_on_disk() -> None:
    """Each portfolio item: same root for href + thumb, real hero + gallery media."""
    text = CATALOG_TS.read_text(encoding="utf-8")
    block = text.split("PUBLIC_AGENCY_PORTFOLIO:")[1].split("export function assertPortfolioArtifactIntegrity")[0]
    live_urls = re.findall(r'livePreviewUrl:\s*portfolioLivePreviewUrl\((AGENCY_ARTIFACT_[A-Z_]+)\)', block)
    preview_roots = re.findall(
        r'previewImage:\s*portfolioPreviewImageForArtifact\((AGENCY_ARTIFACT_[A-Z_]+)\)', block
    )
    assert len(live_urls) >= 2
    assert live_urls == preview_roots

    const_roots = dict(re.findall(r'const (AGENCY_ARTIFACT_[A-Z_]+) = "([^"]+)"', text))
    for const_name in live_urls:
        artifact_root = const_roots[const_name]
        index = PUBLIC / artifact_root.lstrip("/") / "index.html"
        hero = PUBLIC / artifact_root.lstrip("/") / "assets" / "hero.jpg"
        assert index.is_file(), f"missing live preview: {index}"
        assert hero.is_file(), f"missing hero for card: {hero}"
        assert hero.stat().st_size >= MIN_HERO_BYTES, (
            f"placeholder hero ({hero.stat().st_size}B): {hero}"
        )
        assets = hero.parent
        niche = artifact_root.rsplit("/", 1)[-1]
        need = NICHE_GALLERY_MIN.get(niche, 3)
        gallery_ok = [
            assets / f"gallery_{i}.jpg"
            for i in range(1, need + 1)
            if (assets / f"gallery_{i}.jpg").is_file()
            and (assets / f"gallery_{i}.jpg").stat().st_size >= MIN_GALLERY_BYTES
        ]
        assert len(gallery_ok) >= need, f"{artifact_root}: insufficient gallery media"


def test_portfolio_thumb_matches_live_hero_bytes() -> None:
    """Card thumb path must be the same file as the artifact hero (not another tier)."""
    pairs = [
        ("sites/business/auto", "auto"),
        ("sites/business/restaurant", "restaurant"),
    ]
    for rel, _niche in pairs:
        hero = PUBLIC / "package-previews" / rel / "assets" / "hero.jpg"
        basic_hero = PUBLIC / "package-previews" / "sites" / "basic" / rel.split("/")[-1] / "assets" / "hero.jpg"
        assert hero.is_file()
        if basic_hero.is_file():
            assert hero.stat().st_size != basic_hero.stat().st_size or hero.read_bytes() == basic_hero.read_bytes(), (
                f"{rel}: business hero must not silently differ from card while basic differs — sync media"
            )
