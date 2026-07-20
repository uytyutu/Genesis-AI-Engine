"""Hero Pack 2.0 — tiered stills per niche for Path A Factory ZIP."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[2]
_SHOWCASES = _BACKEND / "_research_3d" / "showcases"

# Slots relative to showcases/{niche}/hero_pack/
BASIC_SLOTS = ("hero_1", "hero_2")
BUSINESS_SLOTS = (
    "hero_1",
    "hero_2",
    "background_1",
    "background_2",
    "cta",
    "services",
)
PREMIUM_SLOTS = (
    "hero_1",
    "hero_2",
    "hero_3",
    "banner",
    "gallery",
    "showcase",
    "calculator",
    "footer",
)

_TIER_SLOTS = {
    "basic": BASIC_SLOTS,
    "business": BUSINESS_SLOTS,
    "premium": PREMIUM_SLOTS,
}


def pack_root(niche_id: str | None) -> Path:
    key = (niche_id or "generic").strip().lower() or "generic"
    return _SHOWCASES / key / "hero_pack"


def slot_path(niche_id: str | None, tier: str, slot: str) -> Path:
    return pack_root(niche_id) / tier / f"{slot}.jpg"


def resolve_slot(
    niche_id: str | None,
    package_id: str | None,
    slot: str,
) -> Path | None:
    """Best file for a slot: exact → same slot lower tier → niche preview.jpg."""
    tier = (package_id or "basic").strip().lower()
    if tier not in _TIER_SLOTS:
        tier = "basic"
    key = (niche_id or "generic").strip().lower() or "generic"
    candidates: list[Path] = [slot_path(key, tier, slot)]
    # Prefer higher-quality premium assets when requesting business hero, etc.
    if tier == "premium":
        candidates.append(slot_path(key, "business", slot))
        candidates.append(slot_path(key, "basic", slot))
    elif tier == "business":
        candidates.append(slot_path(key, "basic", slot))
        candidates.append(slot_path(key, "premium", slot))
    else:
        candidates.append(slot_path(key, "business", slot))
    # Cross-slot fallbacks for hero
    if slot.startswith("hero"):
        for t in ("premium", "business", "basic"):
            for s in ("hero_1", "hero_2", "hero_3"):
                candidates.append(slot_path(key, t, s))
    candidates.append(_SHOWCASES / key / "preview.jpg")
    candidates.append(_SHOWCASES / "generic" / "preview.jpg")
    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        if path.is_file():
            return path
    return None


def primary_hero_src(niche_id: str | None, package_id: str | None) -> Path | None:
    return resolve_slot(niche_id, package_id, "hero_1")


def write_hero_pack(
    product_dir: Path,
    niche_id: str | None,
    package_id: str | None,
) -> dict:
    """Copy pack assets into product_dir/assets and set hero.jpg.

    Returns manifest used by landing CSS (relative paths that exist).
    """
    tier = (package_id or "basic").strip().lower()
    if tier not in _TIER_SLOTS:
        tier = "basic"
    assets = product_dir / "assets"
    pack_out = assets / "hero_pack"
    pack_out.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, str] = {"package_id": tier, "niche_id": (niche_id or "generic")}
    slots = _TIER_SLOTS[tier]
    for slot in slots:
        src = resolve_slot(niche_id, tier, slot)
        if src is None:
            continue
        dest_name = f"{slot}.jpg"
        dest = pack_out / dest_name
        shutil.copy2(src, dest)
        manifest[slot] = f"assets/hero_pack/{dest_name}"

    # Canonical hero.jpg = primary hero for this tier
    hero_src = primary_hero_src(niche_id, tier)
    if hero_src is not None:
        shutil.copy2(hero_src, assets / "hero.jpg")
        manifest["hero"] = "assets/hero.jpg"

    (pack_out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def pack_section_css(manifest: dict[str, str], tier: str) -> str:
    """Extra CSS overrides when pack backgrounds exist."""
    t = tier if tier in _TIER_SLOTS else "basic"
    lines: list[str] = []
    if manifest.get("hero"):
        # hero.jpg already referenced in base tier CSS
        pass
    if t in ("business", "premium") and manifest.get("services"):
        url = manifest["services"]
        lines.append(
            f'    body[data-tier="{t}"] #services {{'
            f' background-image: linear-gradient(180deg,rgba(248,250,252,.92),rgba(248,250,252,.96)),'
            f' url("{url}"); background-size: cover; background-position: center; }}'
        )
    if t in ("business", "premium") and manifest.get("cta"):
        url = manifest["cta"]
        lines.append(
            f'    body[data-tier="{t}"] .mid-cta {{'
            f' background-image: linear-gradient(120deg,rgba(15,23,42,.78),rgba(15,23,42,.55)),'
            f' url("{url}"); background-size: cover; background-position: center; color: #fff; }}'
        )
    if t == "business" and manifest.get("background_1"):
        url = manifest["background_1"]
        lines.append(
            f'    body[data-tier="business"] .benefits {{'
            f' background-image: linear-gradient(180deg,rgba(248,250,252,.94),rgba(255,255,255,.98)),'
            f' url("{url}"); background-size: cover; }}'
        )
    if t == "premium" and manifest.get("showcase"):
        url = manifest["showcase"]
        lines.append(
            f'    body[data-tier="premium"] #showcase {{'
            f' background-image: linear-gradient(180deg,rgba(15,23,42,.55),rgba(15,23,42,.75)),'
            f' url("{url}"); background-size: cover; color: #fff; }}'
        )
    if t == "premium" and manifest.get("calculator"):
        url = manifest["calculator"]
        lines.append(
            f'    body[data-tier="premium"] #calculator {{'
            f' background-image: linear-gradient(180deg,rgba(248,250,252,.9),rgba(248,250,252,.95)),'
            f' url("{url}"); background-size: cover; }}'
        )
    if t == "premium" and manifest.get("footer"):
        url = manifest["footer"]
        lines.append(
            f'    body[data-tier="premium"] footer {{'
            f' background-image: linear-gradient(180deg,rgba(15,23,42,.88),rgba(15,23,42,.95)),'
            f' url("{url}"); background-size: cover; background-position: center; }}'
        )
    if t == "premium" and manifest.get("banner"):
        url = manifest["banner"]
        lines.append(
            f'    body[data-tier="premium"] .trust-strip {{'
            f' background-image: linear-gradient(90deg,rgba(15,23,42,.7),rgba(15,23,42,.5)),'
            f' url("{url}"); background-size: cover; }}'
        )
    if t == "premium" and manifest.get("gallery"):
        url = manifest["gallery"]
        lines.append(
            f'    body[data-tier="premium"] #testimonials {{'
            f' background-image: linear-gradient(180deg,rgba(248,250,252,.92),rgba(255,255,255,.97)),'
            f' url("{url}"); background-size: cover; }}'
        )
    if t == "premium" and manifest.get("hero_2"):
        # Second hero used as about section atmosphere
        url = manifest["hero_2"]
        lines.append(
            f'    body[data-tier="premium"] .about {{'
            f' background-image: linear-gradient(180deg,rgba(255,255,255,.88),rgba(255,255,255,.94)),'
            f' url("{url}"); background-size: cover; }}'
        )
    return "\n".join(lines)


def seed_pack_from_preview(niche_id: str) -> int:
    """Fill missing pack slots from niche preview.jpg (bootstrap before gen)."""
    key = (niche_id or "generic").strip().lower()
    preview = _SHOWCASES / key / "preview.jpg"
    if not preview.is_file():
        preview = _SHOWCASES / "generic" / "preview.jpg"
    if not preview.is_file():
        return 0
    written = 0
    for tier, slots in _TIER_SLOTS.items():
        for slot in slots:
            dest = slot_path(key, tier, slot)
            if dest.is_file():
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(preview, dest)
            written += 1
    return written
