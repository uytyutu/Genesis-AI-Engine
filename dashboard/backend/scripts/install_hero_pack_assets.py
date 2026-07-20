"""Install generated Cursor assets into Hero Pack 2.0 slots + create visual variants."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from PIL import Image

from app.factory.hero_pack import BUSINESS_SLOTS, PREMIUM_SLOTS, slot_path
from app.factory.niche_profiles import known_niche_ids

ASSETS = Path(r"C:\Users\hppav\.cursor\projects\d-Games-Genesis-AI-Engine\assets")
SHOW = Path(__file__).resolve().parents[1] / "_research_3d" / "showcases"

# Direct installs: (filename, niche, tier, slot)
INSTALLS = [
    ("dental_biz_cta.jpg", "dental", "business", "cta"),
    ("dental_biz_services.jpg", "dental", "business", "services"),
    ("dental_prem_banner.jpg", "dental", "premium", "banner"),
    ("dental_prem_gallery.jpg", "dental", "premium", "gallery"),
    ("auto_biz_cta.jpg", "auto", "business", "cta"),
    ("auto_biz_services.jpg", "auto", "business", "services"),
    ("auto_prem_banner.jpg", "auto", "premium", "banner"),
    ("auto_prem_gallery.jpg", "auto", "premium", "gallery"),
    ("energy_biz_cta.jpg", "energy", "business", "cta"),
    ("energy_biz_services.jpg", "energy", "business", "services"),
    ("energy_prem_banner.jpg", "energy", "premium", "banner"),
    ("energy_prem_gallery.jpg", "energy", "premium", "gallery"),
    ("beauty_biz_cta.jpg", "beauty", "business", "cta"),
    ("beauty_biz_services.jpg", "beauty", "business", "services"),
    ("beauty_prem_banner.jpg", "beauty", "premium", "banner"),
    ("law_biz_cta.jpg", "law", "business", "cta"),
    ("law_biz_services.jpg", "law", "business", "services"),
    ("law_prem_banner.jpg", "law", "premium", "banner"),
    ("computer_biz_cta.jpg", "computer", "business", "cta"),
    ("computer_biz_services.jpg", "computer", "business", "services"),
    ("appliance_biz_cta.jpg", "appliance", "business", "cta"),
    ("appliance_biz_services.jpg", "appliance", "business", "services"),
    ("green_biz_cta.jpg", "green", "business", "cta"),
    ("green_biz_services.jpg", "green", "business", "services"),
    ("handwerk_biz_cta.jpg", "handwerk", "business", "cta"),
    ("handwerk_biz_services.jpg", "handwerk", "business", "services"),
    ("generic_biz_cta.jpg", "generic", "business", "cta"),
    ("generic_biz_services.jpg", "generic", "business", "services"),
]


def _variant(src: Path, dest: Path, kind: str) -> None:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if kind == "left":
        im = im.crop((0, 0, int(w * 0.72), h))
    elif kind == "right":
        im = im.crop((int(w * 0.28), 0, w, h))
    elif kind == "center":
        im = im.crop((int(w * 0.15), int(h * 0.1), int(w * 0.85), int(h * 0.9)))
    elif kind == "top":
        im = im.crop((0, 0, w, int(h * 0.7)))
    elif kind == "bottom":
        im = im.crop((0, int(h * 0.3), w, h))
    elif kind == "wide":
        im = im.crop((0, int(h * 0.2), w, int(h * 0.8)))
    im = im.resize((1600, 900), Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, format="JPEG", quality=88, optimize=True)


def main() -> None:
    installed = 0
    for fname, niche, tier, slot in INSTALLS:
        src = ASSETS / fname
        if not src.is_file():
            print("skip missing", fname)
            continue
        dest = slot_path(niche, tier, slot)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        installed += 1
        print("install", niche, tier, slot)

    # hero_1 = niche preview; hero_2 / other slots = variants from cta/services/preview
    kinds = {
        "hero_2": "center",
        "background_1": "left",
        "background_2": "right",
        "hero_3": "wide",
        "showcase": "top",
        "calculator": "bottom",
        "footer": "left",
    }
    for niche in known_niche_ids():
        preview = SHOW / niche / "preview.jpg"
        cta = slot_path(niche, "business", "cta")
        services = slot_path(niche, "business", "services")
        base = preview if preview.is_file() else SHOW / "generic" / "preview.jpg"
        # basic heroes
        h1 = slot_path(niche, "basic", "hero_1")
        if base.is_file():
            shutil.copy2(base, h1)
            _variant(base, slot_path(niche, "basic", "hero_2"), "center")
        # business backgrounds from cta/services when present
        src_a = cta if cta.is_file() else base
        src_b = services if services.is_file() else base
        if src_a.is_file():
            _variant(src_a, slot_path(niche, "business", "background_1"), "left")
            _variant(src_a, slot_path(niche, "business", "hero_2"), "center")
            shutil.copy2(src_a if cta.is_file() else base, slot_path(niche, "business", "hero_1"))
        if src_b.is_file():
            _variant(src_b, slot_path(niche, "business", "background_2"), "right")
        # premium fills
        for slot, kind in kinds.items():
            if slot in ("hero_2",):
                continue
            src = src_b if slot in ("showcase", "gallery", "calculator") else src_a
            if not src.is_file():
                src = base
            if not src.is_file():
                continue
            dest = slot_path(niche, "premium", slot)
            # keep banner/gallery if already unique installs
            if slot in ("banner", "gallery") and dest.is_file():
                # only overwrite if still identical to preview
                if hashlib.md5(dest.read_bytes()).hexdigest() == hashlib.md5(base.read_bytes()).hexdigest():
                    _variant(src, dest, kind)
            else:
                _variant(src, dest, kind)
        # premium hero_1/2/3
        if base.is_file():
            shutil.copy2(base, slot_path(niche, "premium", "hero_1"))
            _variant(src_a if src_a.is_file() else base, slot_path(niche, "premium", "hero_2"), "center")
            _variant(src_b if src_b.is_file() else base, slot_path(niche, "premium", "hero_3"), "wide")
        # copy business cta/services into premium when missing unique
        for slot in ("cta", "services"):
            # premium doesn't use cta/services slots — skip
            pass

    print("installed_direct", installed)
    # uniqueness report for business cta across niches
    print("--- business cta hashes ---")
    for niche in known_niche_ids():
        p = slot_path(niche, "business", "cta")
        if p.is_file():
            print(niche, hashlib.md5(p.read_bytes()).hexdigest()[:10], p.stat().st_size)


if __name__ == "__main__":
    main()
