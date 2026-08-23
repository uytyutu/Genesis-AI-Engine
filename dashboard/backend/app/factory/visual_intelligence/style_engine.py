"""Style Engine — niche → palette, type, composition, hero, cards, motion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Surface = Literal["website", "store", "platform"]

# Website sections vs Store sections — same engine, different component sets
WEBSITE_COMPONENTS = (
    "hero",
    "services",
    "about",
    "team",
    "trust",
    "gallery",
    "contact",
    "footer",
)
STORE_COMPONENTS = (
    "hero",
    "catalog",
    "product_cards",
    "filters",
    "pdp",
    "cart",
    "checkout",
    "account",
    "footer",
)
PLATFORM_COMPONENTS = (
    "hero",
    "packages",
    "modules",
    "trust",
    "preview",
    "cta",
    "footer",
)


@dataclass(frozen=True)
class StyleProfile:
    """Resolved niche visual language — not a single template."""

    niche_id: str
    mood: str
    palette_note: str
    typography_note: str
    composition: str
    card_style: str
    hero_style: str
    background_style: str
    animation_bias: str
    motion_default: str  # basic | business | premium
    density: str  # airy | balanced | dense
    extras: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "niche_id": self.niche_id,
            "mood": self.mood,
            "palette_note": self.palette_note,
            "typography_note": self.typography_note,
            "composition": self.composition,
            "card_style": self.card_style,
            "hero_style": self.hero_style,
            "background_style": self.background_style,
            "animation_bias": self.animation_bias,
            "motion_default": self.motion_default,
            "density": self.density,
            "extras": dict(self.extras),
        }


# User-facing niche examples + full Design Engine niche coverage
_STYLES: dict[str, StyleProfile] = {
    "law": StyleProfile(
        niche_id="law",
        mood="strict · minimal · corporate",
        palette_note="Ink navy, cool gray, restrained gold accent",
        typography_note="Serif display + clean sans body — trust & authority",
        composition="narrow measure, generous whitespace, hairline rules",
        card_style="bordered · low shadow · formal",
        hero_style="centered statement · minimal media",
        background_style="soft paper / cool gradient",
        animation_bias="subtle fade only",
        motion_default="basic",
        density="airy",
    ),
    "restaurant": StyleProfile(
        niche_id="restaurant",
        mood="warm · atmospheric · photographic",
        palette_note="Warm terracotta, cream, deep brown",
        typography_note="Expressive display + readable body",
        composition="large photography, editorial margins",
        card_style="image-led · soft radius",
        hero_style="full-bleed atmosphere photo",
        background_style="warm grain / ambient dark overlays",
        animation_bias="slow reveal · parallax light",
        motion_default="business",
        density="balanced",
    ),
    "beauty": StyleProfile(
        niche_id="beauty",
        mood="light · elegant · soft motion",
        palette_note="Blush, ivory, soft rose gold",
        typography_note="Elegant serif display + airy sans",
        composition="centered calm blocks, soft cards",
        card_style="glass-soft · large radius",
        hero_style="soft portrait · pastel wash",
        background_style="light gradients · soft orbs",
        animation_bias="smooth fade · gentle hover",
        motion_default="business",
        density="airy",
    ),
    "auto": StyleProfile(
        niche_id="auto",
        mood="dark · technical · precise",
        palette_note="Charcoal, steel blue, signal accent",
        typography_note="Condensed display + technical sans",
        composition="asymmetric tech grid, specs first",
        card_style="sharp · industrial shadow",
        hero_style="dark tech banner · product focus",
        background_style="dark mesh / subtle grid",
        animation_bias="crisp transitions · hover lift",
        motion_default="business",
        density="dense",
    ),
    "dental": StyleProfile(
        niche_id="dental",
        mood="clean · light · trust",
        palette_note="Clinical white-blue, soft teal accent",
        typography_note="Friendly sans · clear hierarchy",
        composition="clean columns, trust badges visible",
        card_style="white surface · soft shadow",
        hero_style="bright trust hero · calm CTA",
        background_style="clean light · soft blue wash",
        animation_bias="gentle fade · micro hover",
        motion_default="basic",
        density="balanced",
    ),
    "psychology": StyleProfile(
        niche_id="psychology",
        mood="calm · spacious · trusting",
        palette_note="Soft sage, warm sand, airy ivory — never loud",
        typography_note="Gentle serif display · readable sans body",
        composition="portrait hero · wide margins · one idea per section",
        card_style="soft cream surface · quiet shadow",
        hero_style="large portrait · calm CTA · no spectacle",
        background_style="light sage wash · breathing room",
        animation_bias="soft fade · slow section transitions",
        motion_default="basic",
        density="airy",
    ),
    "fashion": StyleProfile(
        niche_id="fashion",
        mood="editorial · large banners",
        palette_note="Monochrome + seasonal accent",
        typography_note="Editorial display · refined tracking",
        composition="full-bleed banners · sparse copy",
        card_style="edge-to-edge media · minimal chrome",
        hero_style="editorial full-bleed",
        background_style="gallery white / runway dark",
        animation_bias="slow cinematic reveal",
        motion_default="premium",
        density="airy",
    ),
    "computer": StyleProfile(
        niche_id="computer",
        mood="modern · tech · animated accents",
        palette_note="Deep slate, electric accent, glass",
        typography_note="Modern geometric sans",
        composition="modular cards · tech rhythm",
        card_style="glass · subtle border glow (CSS only)",
        hero_style="tech statement · product silhouette",
        background_style="dark tech gradient · mesh",
        animation_bias="reveal · glass · section transitions",
        motion_default="premium",
        density="balanced",
    ),
    "handwerk": StyleProfile(
        niche_id="handwerk",
        mood="craft · grounded · honest",
        palette_note="Timber, slate, warm off-white",
        typography_note="Sturdy sans · clear prices",
        composition="practical grids · workshop photos",
        card_style="solid · craft shadow",
        hero_style="workshop atmosphere",
        background_style="warm neutral · subtle texture",
        animation_bias="simple fade · honest hover",
        motion_default="basic",
        density="balanced",
    ),
    "realestate": StyleProfile(
        niche_id="realestate",
        mood="premium space · calm luxury",
        palette_note="Stone, sage, warm white",
        typography_note="Refined serif + sans",
        composition="large property imagery · airy",
        card_style="gallery card · soft elevation",
        hero_style="property full-bleed",
        background_style="light stone wash",
        animation_bias="parallax light · reveal",
        motion_default="business",
        density="airy",
    ),
    "generic": StyleProfile(
        niche_id="generic",
        mood="balanced · professional · versatile",
        palette_note="Neutral brandable primary",
        typography_note="Clear sans hierarchy",
        composition="standard agency sections",
        card_style="soft elevation",
        hero_style="balanced statement + media",
        background_style="subtle gradient",
        animation_bias="fade · hover",
        motion_default="business",
        density="balanced",
    ),
}

# Aliases → canonical niche_id
_ALIASES = {
    "lawyer": "law",
    "legal": "law",
    "anwalt": "law",
    "jurist": "law",
    "gastro": "restaurant",
    "cafe": "restaurant",
    "salon": "beauty",
    "spa": "beauty",
    "cosmetics": "beauty",
    "autoservice": "auto",
    "car": "auto",
    "garage": "auto",
    "dentist": "dental",
    "zahnarzt": "dental",
    "psychologist": "psychology",
    "psychologe": "psychology",
    "psychotherapeut": "psychology",
    "therapie": "psychology",
    "therapy": "psychology",
    "counseling": "psychology",
    "beratung_psy": "psychology",
    "clothing": "fashion",
    "apparel": "fashion",
    "it": "computer",
    "tech": "computer",
    "software": "computer",
    "furniture": "realestate",
    "green": "handwerk",
    "energy": "computer",
    "fitness": "beauty",
    "photography": "fashion",
    "accounting": "law",
    "cleaning": "generic",
    "appliance": "computer",
    "auto_ankauf": "auto",
}


def normalize_niche(niche_id: str | None) -> str:
    raw = (niche_id or "generic").strip().lower() or "generic"
    return _ALIASES.get(raw, raw)


def resolve_style(niche_id: str | None) -> StyleProfile:
    nid = normalize_niche(niche_id)
    if nid in _STYLES:
        return _STYLES[nid]
    # Fall back to Design Engine niche if known but no VIE profile yet
    from app.factory.niche_profiles import resolve_niche_profile

    profile = resolve_niche_profile(nid)
    base = _STYLES["generic"]
    return StyleProfile(
        niche_id=profile.niche_id,
        mood=base.mood,
        palette_note=f"Design Engine palette for {profile.niche_id}",
        typography_note=base.typography_note,
        composition=base.composition,
        card_style=base.card_style,
        hero_style=base.hero_style,
        background_style=base.background_style,
        animation_bias=base.animation_bias,
        motion_default=base.motion_default,
        density=base.density,
        extras={"from_design_engine": True},
    )


def components_for_surface(surface: Surface) -> tuple[str, ...]:
    if surface == "store":
        return STORE_COMPONENTS
    if surface == "platform":
        return PLATFORM_COMPONENTS
    return WEBSITE_COMPONENTS
