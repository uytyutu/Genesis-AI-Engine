"""Embed client-uploaded logo / photos into Factory Path A ZIP.

Goal: "This is my site" — not an empty template with a README telling them
to insert assets themselves.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
_LOGO_NAME = re.compile(
    r"(logo|logotyp|фирмен|brand|zeichen|marke|эмблем)",
    re.I,
)
_HERO_NAME = re.compile(
    r"(hero|banner|office|empfang|reception|clinic|praxis|studio|"
    r"interior|офис|клиник|салон|werkstatt|storefront|fassade)",
    re.I,
)


@dataclass
class ClientAssetsResult:
    logo: bool = False
    logo_src: str = "assets/logo.png"
    hero_from_client: bool = False
    gallery: list[str] = field(default_factory=list)
    used_files: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "logo": self.logo,
            "logo_src": self.logo_src,
            "hero_from_client": self.hero_from_client,
            "gallery": list(self.gallery),
            "used_files": list(self.used_files),
        }


def _is_image(path: Path, content_type: str = "", filename: str = "") -> bool:
    ext = path.suffix.lower() or Path(filename).suffix.lower()
    if ext in _IMAGE_EXT:
        return True
    return (content_type or "").lower().startswith("image/")


def _score_logo(filename: str, ext: str) -> int:
    name = filename or ""
    score = 0
    if _LOGO_NAME.search(name):
        score += 100
    if ext == ".svg":
        score += 40
    if ext == ".png":
        score += 10
    return score


def _score_hero(filename: str) -> int:
    name = filename or ""
    score = 10
    if _HERO_NAME.search(name):
        score += 80
    if _LOGO_NAME.search(name):
        score -= 50
    return score


def classify_material_images(materials: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Pick logo / hero / gallery candidates from order material metadata."""
    images: list[dict[str, Any]] = []
    for row in materials or []:
        if not isinstance(row, dict):
            continue
        raw_path = str(row.get("path") or "").strip()
        if not raw_path:
            continue
        path = Path(raw_path)
        if not path.is_file():
            continue
        filename = str(row.get("filename") or path.name)
        ctype = str(row.get("content_type") or "")
        if not _is_image(path, ctype, filename):
            continue
        images.append(
            {
                "path": path,
                "filename": filename,
                "ext": path.suffix.lower() or Path(filename).suffix.lower(),
                "content_type": ctype,
            }
        )

    if not images:
        return {"logo": None, "hero": None, "gallery": []}

    logo_candidate = max(images, key=lambda r: _score_logo(r["filename"], r["ext"]))
    logo = logo_candidate if _score_logo(logo_candidate["filename"], logo_candidate["ext"]) >= 40 else None

    remaining = [r for r in images if logo is None or r["path"] != logo["path"]]
    hero = max(remaining, key=lambda r: _score_hero(r["filename"])) if remaining else None
    gallery_src = [
        r
        for r in remaining
        if hero is None or r["path"] != hero["path"]
    ][:6]

    # Single non-logo image → hero (client photo of business)
    if hero is None and remaining:
        hero = remaining[0]
        gallery_src = remaining[1:7]

    return {"logo": logo, "hero": hero, "gallery": gallery_src}


def apply_client_assets(
    product_dir: Path,
    materials: list[dict[str, Any]] | None,
) -> ClientAssetsResult:
    """Copy classified client images into product assets/ for ZIP delivery."""
    result = ClientAssetsResult()
    picked = classify_material_images(materials)
    assets = product_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    gallery_dir = assets / "client"
    gallery_dir.mkdir(parents=True, exist_ok=True)

    logo = picked.get("logo")
    if isinstance(logo, dict):
        src: Path = logo["path"]
        ext = logo["ext"] if logo["ext"] in _IMAGE_EXT else ".png"
        if ext == ".svg":
            shutil.copy2(src, assets / "logo.svg")
            result.logo_src = "assets/logo.svg"
        else:
            shutil.copy2(src, assets / "logo.png")
            result.logo_src = "assets/logo.png"
        result.logo = True
        result.used_files.append(str(logo.get("filename") or src.name))

    hero = picked.get("hero")
    if isinstance(hero, dict):
        src = hero["path"]
        # Canonical CSS looks for assets/hero.jpg
        dest = assets / "hero.jpg"
        shutil.copy2(src, dest)
        result.hero_from_client = True
        result.used_files.append(str(hero.get("filename") or src.name))

    for i, row in enumerate(picked.get("gallery") or [], start=1):
        if not isinstance(row, dict):
            continue
        src = row["path"]
        ext = row["ext"] if row["ext"] in _IMAGE_EXT - {".svg"} else ".jpg"
        if ext == ".jpeg":
            ext = ".jpg"
        name = f"photo_{i}{ext}"
        shutil.copy2(src, gallery_dir / name)
        rel = f"assets/client/{name}"
        result.gallery.append(rel)
        result.used_files.append(str(row.get("filename") or src.name))

    return result
