"""Deterministic Design DNA resolution — art direction before HTML."""

from __future__ import annotations

import hashlib
from typing import Iterable

from app.factory.design_dna.anti_clone import ensure_unique_fingerprint, fingerprint_dna
from app.factory.design_dna.dna import DesignDNA
from app.factory.design_dna.rhythm import plan_section_rhythm

# Niche → style pools by package (Starter narrower / calmer)
_PSYCHOLOGY_STARTER = ("scandinavian_calm", "modern_clinical", "organic_premium")
_PSYCHOLOGY_BUSINESS = (
    "scandinavian_calm",
    "nature_therapy",
    "modern_clinical",
    "organic_premium",
    "editorial",
)
_PSYCHOLOGY_PREMIUM = (
    "scandinavian_calm",
    "nature_therapy",
    "luxury_studio",
    "editorial",
    "modern_clinical",
    "organic_premium",
)

_DEFAULT_STARTER = ("modern_clinical", "scandinavian_calm", "organic_premium")
_DEFAULT_BUSINESS = ("modern_clinical", "editorial", "organic_premium", "scandinavian_calm")
_DEFAULT_PREMIUM = (
    "luxury_studio",
    "editorial",
    "modern_clinical",
    "organic_premium",
    "scandinavian_calm",
    "nature_therapy",
)

_STYLE_META: dict[str, dict[str, str]] = {
    "scandinavian_calm": {
        "emotion": "calm",
        "palette_family": "sand",
        "typography_pair": "cormorant_source",
        "hero_concept": "soft_split_photo",
        "hero_layout": "A",
        "depth": "medium",
        "glass": "low",
        "composition": "airy",
        "accent_hex": "#5b7c6e",
        "surface_hex": "#f7f4ef",
        "ink_hex": "#2c3330",
    },
    "nature_therapy": {
        "emotion": "nature",
        "palette_family": "forest",
        "typography_pair": "cormorant_source",
        "hero_concept": "nature_fullbleed",
        "hero_layout": "D",
        "depth": "high",
        "glass": "medium",
        "composition": "organic",
        "accent_hex": "#3f5a4f",
        "surface_hex": "#eef4ef",
        "ink_hex": "#1a2e24",
    },
    "luxury_studio": {
        "emotion": "prestige",
        "palette_family": "ink_champagne",
        "typography_pair": "playfair_manrope",
        "hero_concept": "cinematic_glass",
        "hero_layout": "D",
        "depth": "high",
        "glass": "high",
        "composition": "immersive",
        "accent_hex": "#c5a572",
        "surface_hex": "#f4f0ea",
        "ink_hex": "#0c0a09",
    },
    "editorial": {
        "emotion": "clarity",
        "palette_family": "paper_ink",
        "typography_pair": "playfair_manrope",
        "hero_concept": "magazine_bleed",
        "hero_layout": "B",
        "depth": "high",
        "glass": "low",
        "composition": "magazine",
        "accent_hex": "#78716c",
        "surface_hex": "#fafaf9",
        "ink_hex": "#1c1917",
    },
    "modern_clinical": {
        "emotion": "trust",
        "palette_family": "sage_mist",
        "typography_pair": "cormorant_source",
        "hero_concept": "trust_panel",
        "hero_layout": "C",
        "depth": "medium",
        "glass": "medium",
        "composition": "clean",
        "accent_hex": "#5b7c6e",
        "surface_hex": "#f3f6f4",
        "ink_hex": "#243029",
    },
    "organic_premium": {
        "emotion": "warmth",
        "palette_family": "warm_clay",
        "typography_pair": "cormorant_source",
        "hero_concept": "soft_orb_photo",
        "hero_layout": "E",
        "depth": "medium",
        "glass": "medium",
        "composition": "soft",
        "accent_hex": "#a68a6d",
        "surface_hex": "#faf6f1",
        "ink_hex": "#292524",
    },
}


def _pool_for(niche_id: str, package_id: str) -> tuple[str, ...]:
    niche = (niche_id or "generic").strip().lower()
    pid = (package_id or "basic").strip().lower()
    if niche == "psychology":
        if pid == "premium":
            return _PSYCHOLOGY_PREMIUM
        if pid == "business":
            return _PSYCHOLOGY_BUSINESS
        return _PSYCHOLOGY_STARTER
    if pid == "premium":
        return _DEFAULT_PREMIUM
    if pid == "business":
        return _DEFAULT_BUSINESS
    return _DEFAULT_STARTER


def _pick(pool: Iterable[str], seed: str) -> str:
    items = tuple(pool)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return items[int(digest[:8], 16) % len(items)]


def _motion_for(package_id: str, style: str) -> str:
    pid = (package_id or "basic").strip().lower()
    if pid == "basic":
        return "soft"
    if pid == "business":
        return "business"
    if style in ("luxury_studio", "editorial"):
        return "premium"
    return "premium"


def resolve_design_dna(
    *,
    business_name: str,
    niche_id: str,
    package_id: str,
    section_keys: tuple[str, ...] | list[str] | None = None,
    diversity_salt: str = "",
    recent_fingerprints: list[str] | None = None,
) -> DesignDNA:
    """Art-direct the product before blocks are assembled."""
    niche = (niche_id or "generic").strip().lower() or "generic"
    pid = (package_id or "basic").strip().lower() or "basic"
    name = (business_name or "Business").strip() or "Business"
    salt = (diversity_salt or "").strip()
    pool = _pool_for(niche, pid)

    # Premium psychology: prefer cinematic layouts when package demands WOW
    style = _pick(pool, f"{name}|{niche}|{pid}|dna-style|{salt}")
    meta = dict(_STYLE_META.get(style) or _STYLE_META["modern_clinical"])

    if pid == "premium" and niche == "psychology" and style not in (
        "luxury_studio",
        "nature_therapy",
        "editorial",
    ):
        # Lift hero toward immersive without forcing one clone
        if meta["hero_layout"] in ("A", "C", "E"):
            meta["hero_layout"] = _pick(("D", "B", "F"), f"{name}|{pid}|hero-lift|{salt}")
            meta["hero_concept"] = "cinematic_glass" if meta["hero_layout"] == "D" else meta["hero_concept"]
            meta["glass"] = "high" if meta["hero_layout"] == "D" else meta["glass"]

    if pid == "basic":
        # Starter: readable light hero — never white text on cream
        if meta["hero_layout"] not in ("A", "C"):
            meta["hero_layout"] = "A"
        meta["depth"] = "medium"
        meta["glass"] = "low" if meta["glass"] == "high" else meta["glass"]

    if niche == "psychology" and pid == "premium":
        # Premium: immersive cinematic only — Business keeps softer layouts for tier ladder
        if meta["hero_layout"] in ("A", "C", "E"):
            meta["hero_layout"] = "D"
            meta["hero_concept"] = "cinematic_glass"
            meta["glass"] = "high"
    elif niche == "psychology" and pid == "business":
        # Business ≠ Premium clone: editorial / split calm, not same D wow
        if meta["hero_layout"] in ("D", "F", "B"):
            meta["hero_layout"] = _pick(("C", "A", "E"), f"{name}|{pid}|biz-hero|{salt}")
            meta["glass"] = "medium"
            meta["hero_concept"] = "trust_panel" if meta["hero_layout"] == "C" else meta["hero_concept"]

    keys = tuple(section_keys or ())
    treatments = plan_section_rhythm(
        section_keys=keys,
        style=style,
        package_id=pid,
        seed=f"{name}|{niche}|{pid}|rhythm|{salt}",
    )

    # Typography Engine — niche ≠ niche; never one global stack
    from app.factory.design_dna.typography_engine import resolve_type_pair

    type_pair = resolve_type_pair(
        niche_id=niche,
        emotion=str(meta.get("emotion") or ""),
        package_id=pid,
        diversity_salt=salt,
    )
    meta["typography_pair"] = type_pair.id

    motion = _motion_for(pid, style)
    base_fp = fingerprint_dna(
        style=style,
        hero_layout=meta["hero_layout"],
        palette=meta["palette_family"],
        treatments=treatments,
        package_id=pid,
        niche_id=niche,
        business_name=name,
    )
    fp = ensure_unique_fingerprint(
        base_fp,
        recent=recent_fingerprints or [],
        reseed=lambda n: fingerprint_dna(
            style=_pick(pool, f"{name}|{niche}|{pid}|dna-style|reroll{n}|{salt}"),
            hero_layout=meta["hero_layout"],
            palette=meta["palette_family"],
            treatments=plan_section_rhythm(
                section_keys=keys,
                style=style,
                package_id=pid,
                seed=f"{name}|{niche}|{pid}|rhythm|reroll{n}|{salt}",
            ),
            package_id=pid,
            niche_id=niche,
            business_name=name,
        ),
    )

    return DesignDNA(
        emotion=meta["emotion"],
        style=style,
        palette_family=meta["palette_family"],
        typography_pair=meta["typography_pair"],
        motion=motion,
        hero_concept=meta["hero_concept"],
        hero_layout=meta["hero_layout"],
        depth=meta["depth"],
        glass=meta["glass"],
        composition=meta["composition"],
        package_id=pid,
        niche_id=niche,
        fingerprint=fp,
        section_treatments=treatments,
        accent_hex=meta["accent_hex"],
        surface_hex=meta["surface_hex"],
        ink_hex=meta["ink_hex"],
    )
