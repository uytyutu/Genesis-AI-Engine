"""Industry Design DNA — niche families must not share one template pool.

Phase 3: Automotive DE is the first acceptance niche; other families stay distinct.
"""

from __future__ import annotations

import hashlib
from typing import Iterable

# Niche id → industry family (stable contract for Design Spec)
NICHE_TO_FAMILY: dict[str, str] = {
    "auto": "automotive",
    "autohaus": "automotive",
    "car_dealership": "automotive",
    "auto_detailing": "automotive",
    "auto_ankauf": "automotive",
    "restaurant": "hospitality",
    "dental": "dental",
    "orthodontics": "dental",
    "law": "legal",
    "beauty": "beauty",
    "realestate": "realestate",
    "psychology": "psychology",
    "family_psychology": "psychology",
    "handwerk": "craft",
    "dachreinigung": "craft",
    "zaunbau": "craft",
    "gartenpflege": "craft",
    "cleaning": "craft",
    "computer": "technology",
    "it_support": "technology",
}

# Style pools per family × package — disjoint where possible
_FAMILY_POOLS: dict[str, dict[str, tuple[str, ...]]] = {
    "automotive": {
        "basic": ("modern_clinical", "organic_premium"),
        "business": ("modern_clinical", "editorial", "organic_premium"),
        "premium": ("luxury_studio", "editorial", "modern_clinical"),
    },
    "hospitality": {
        "basic": ("boutique_warm", "organic_premium"),
        "business": ("boutique_warm", "luxury_studio", "editorial"),
        "premium": ("luxury_studio", "boutique_warm", "editorial"),
    },
    "dental": {
        "basic": ("modern_clinical", "scandinavian_calm"),
        "business": ("modern_clinical", "scandinavian_calm", "organic_premium"),
        "premium": ("modern_clinical", "luxury_studio", "scandinavian_calm"),
    },
    "legal": {
        "basic": ("editorial", "modern_clinical"),
        "business": ("editorial", "luxury_studio", "modern_clinical"),
        "premium": ("luxury_studio", "editorial", "modern_clinical"),
    },
    "beauty": {
        "basic": ("boutique_warm", "organic_premium"),
        "business": ("luxury_studio", "boutique_warm", "organic_premium"),
        "premium": ("luxury_studio", "boutique_warm", "editorial"),
    },
    "realestate": {
        "basic": ("editorial", "modern_clinical"),
        "business": ("luxury_studio", "editorial", "modern_clinical"),
        "premium": ("luxury_studio", "editorial", "modern_clinical"),
    },
}

_RENDERER_STRATEGY: dict[str, str] = {
    "automotive": "craftsman",
    "hospitality": "restaurant",
    "dental": "clinic",
    "legal": "legal",
    "beauty": "editorial",
    "realestate": "corporate",
    "psychology": "clinic",
    "craft": "craftsman",
    "technology": "technology",
}


def industry_family_for_niche(niche_id: str) -> str:
    niche = (niche_id or "generic").strip().lower() or "generic"
    return NICHE_TO_FAMILY.get(niche, "generic")


def style_pool_for_family(family: str, package_id: str) -> tuple[str, ...] | None:
    fam = (family or "generic").strip().lower()
    pid = (package_id or "basic").strip().lower()
    if pid not in ("basic", "business", "premium"):
        pid = "business"
    pools = _FAMILY_POOLS.get(fam)
    if not pools:
        return None
    return pools.get(pid) or pools.get("basic")


def renderer_strategy_for_family(family: str) -> str:
    return _RENDERER_STRATEGY.get((family or "").strip().lower(), "classic")


def _pick(pool: Iterable[str], seed: str) -> str:
    items = tuple(pool)
    if not items:
        return "modern_clinical"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return items[int(digest[:8], 16) % len(items)]


def industry_hero_profile(family: str, package_id: str = "business") -> dict[str, str]:
    """Stable hero/CTA contract for Design Spec comparison across families."""
    fam = (family or "generic").strip().lower()
    pid = (package_id or "business").strip().lower()
    if fam == "automotive":
        return {
            "hero_mode": "cinematic",
            "hero_focus": "service",
            "cta_primary": "Termin vereinbaren",
            "photography": "automotive_workshop",
            "experience_axis": "craftsman",
        }
    if fam == "hospitality":
        return {
            "hero_mode": "immersive",
            "hero_focus": "experience",
            "cta_primary": "Tisch reservieren",
            "photography": "food_interior",
            "experience_axis": "immersive",
        }
    if fam == "dental":
        return {
            "hero_mode": "clinical",
            "hero_focus": "trust",
            "cta_primary": "Termin vereinbaren",
            "photography": "clinic",
            "experience_axis": "clinic",
        }
    return {
        "hero_mode": "classic",
        "hero_focus": "overview",
        "cta_primary": "Kontakt",
        "photography": "general",
        "experience_axis": pid,
    }


def apply_industry_meta_adjustments(
    *,
    niche_id: str,
    package_id: str,
    meta: dict[str, str],
    business_name: str,
    diversity_salt: str = "",
) -> dict[str, str]:
    """Post-pick hero/layout tweaks so families feel different at first glance."""
    niche = (niche_id or "").strip().lower()
    pid = (package_id or "basic").strip().lower()
    family = industry_family_for_niche(niche)
    name = (business_name or "Business").strip()
    salt = (diversity_salt or "").strip()

    if family == "automotive":
        meta["composition"] = "signal"
        if pid == "premium":
            meta["hero_layout"] = "D"
            meta["hero_concept"] = "cinematic_glass"
            meta["glass"] = "high"
            meta["emotion"] = "confidence"
            meta["accent_hex"] = "#1d4ed8"
            meta["surface_hex"] = "#f8fafc"
            meta["ink_hex"] = "#0f172a"
        elif pid == "business":
            meta["hero_layout"] = "F"
            meta["hero_concept"] = "trust_panel"
            meta["glass"] = "medium"
            meta["emotion"] = "trust"
            meta["accent_hex"] = "#2563eb"
        else:
            meta["hero_layout"] = "C"
            meta["hero_concept"] = "trust_panel"
            meta["glass"] = "low"
            meta["accent_hex"] = "#1e40af"
    elif family == "hospitality":
        meta["composition"] = "immersive"
        meta["emotion"] = "warmth"
        meta["surface_hex"] = "#1c1917"
        meta["ink_hex"] = "#fafaf9"
        meta["accent_hex"] = "#c2410c"
        if pid == "premium":
            meta["hero_layout"] = "D"
            meta["hero_concept"] = "immersive_glass"
            meta["glass"] = "high"
        elif pid == "business":
            meta["hero_layout"] = _pick(("B", "D"), f"{name}|rest|hero|{salt}")
            meta["hero_concept"] = "immersive_plate"
            meta["glass"] = "medium"
        else:
            meta["hero_layout"] = "B"
            meta["hero_concept"] = "warm_intro"
            meta["glass"] = "low"
    elif family == "dental":
        meta["composition"] = "clean"
        meta["hero_concept"] = "trust_panel"
        meta["hero_layout"] = "C" if pid == "basic" else _pick(("A", "C"), f"{name}|dental|hero|{salt}")
        meta["emotion"] = "trust"
    elif family == "legal":
        meta["composition"] = "magazine"
        meta["hero_concept"] = "magazine_bleed"
        meta["hero_layout"] = "B"
        meta["emotion"] = "prestige"
    elif family == "beauty":
        meta["composition"] = "soft"
        meta["hero_concept"] = "soft_orb_photo"
        meta["hero_layout"] = "E"
        meta["emotion"] = "elegance"
    elif family == "realestate":
        meta["composition"] = "immersive"
        meta["hero_concept"] = "cinematic_glass"
        meta["hero_layout"] = "D"
        meta["emotion"] = "prestige"

    return meta


def industry_dna_directive(
    *,
    niche_id: str,
    package_id: str,
    business_name: str,
    diversity_salt: str = "",
    style_hint: str = "",
) -> dict[str, str]:
    family = industry_family_for_niche(niche_id)
    pool = style_pool_for_family(family, package_id)
    style = (style_hint or "").strip().lower()
    if pool and style and style not in pool:
        style = ""
    if not style and pool:
        style = _pick(pool, f"{business_name}|{family}|{package_id}|directive|{diversity_salt}")
    return {
        "industry_family": family,
        "renderer_strategy": renderer_strategy_for_family(family),
        "style_hint": style or "",
        "style_pool": ",".join(pool or ()),
    }
