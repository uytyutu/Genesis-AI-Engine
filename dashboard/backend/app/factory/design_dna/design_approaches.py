"""World design approaches — Design Observatory Studio Era.

Factory chooses a *studio approach* first, then adapts it to the niche.
Not niche-only templates — global design languages.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DesignApproach:
    id: str
    label: str
    pillars: tuple[str, ...]
    composition_bias: tuple[str, ...]
    type_bias: tuple[str, ...]
    color_feeling: str
    motion: str
    niches_affinity: tuple[str, ...]
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


DESIGN_APPROACHES: dict[str, DesignApproach] = {
    "luxury": DesignApproach(
        id="luxury",
        label="Luxury",
        pillars=(
            "minimalism",
            "generous air",
            "large photography",
            "little text",
            "quiet confidence",
        ),
        composition_bias=("luxury_brand", "cinematic", "whisper", "atelier_night", "breath"),
        type_bias=("playfair_manrope", "bodoni_jakarta", "gloock_manrope"),
        color_feeling="restrained ink + warm metal accent",
        motion="slow reveal, soft parallax",
        niches_affinity=("fashion", "beauty", "jewelry", "realestate", "psychology"),
        notes="Premium invites looking",
    ),
    "scandinavian": DesignApproach(
        id="scandinavian",
        label="Scandinavian",
        pillars=(
            "natural materials",
            "calm colors",
            "soft typography",
            "honest space",
            "human warmth",
        ),
        composition_bias=("garden", "sanctuary", "chamber", "nature", "hearth"),
        type_bias=("cormorant_source", "instrument_onest", "newsreader_public"),
        color_feeling="sage, sand, soft wood, daylight",
        motion="gentle fade, no neon bounce",
        niches_affinity=("psychology", "dental", "green", "furniture"),
    ),
    "editorial": DesignApproach(
        id="editorial",
        label="Editorial",
        pillars=(
            "magazine grid",
            "unusual layout",
            "large headlines",
            "story first",
            "typographic drama",
        ),
        composition_bias=("magazine", "editorial", "folio", "narrative", "cascade"),
        type_bias=("newsreader_public", "playfair_manrope", "instrument_onest"),
        color_feeling="ink on paper, selective accent",
        motion="scroll chapters, underline craft",
        niches_affinity=("law", "psychology", "photography", "creative"),
    ),
    "tech_saas": DesignApproach(
        id="tech_saas",
        label="Tech SaaS",
        pillars=(
            "grids",
            "motion",
            "glass",
            "illustrations",
            "product clarity",
        ),
        composition_bias=("bento", "tech_stack", "modern", "signal", "orbit"),
        type_bias=("syne_figtree", "space_grotesk_inter", "bricolage_sora"),
        color_feeling="cool surface + precise accent",
        motion="purposeful micro-interactions",
        niches_affinity=("technology", "saas", "computer", "it"),
    ),
    "boutique": DesignApproach(
        id="boutique",
        label="Boutique",
        pillars=(
            "emotional photography",
            "storytelling",
            "atmosphere",
            "curated offer",
            "intimate brand",
        ),
        composition_bias=("boutique", "spotlight", "runway", "visual_first", "floating"),
        type_bias=("fraunces_dm", "bodoni_jakarta", "gloock_manrope"),
        color_feeling="tactile warm + soft contrast",
        motion="lifestyle hover, gallery breath",
        niches_affinity=("beauty", "fashion", "restaurant", "psychology"),
    ),
    "corporate_clear": DesignApproach(
        id="corporate_clear",
        label="Corporate Clear",
        pillars=(
            "clarity",
            "trust early",
            "precise hierarchy",
            "serious presence",
            "no gimmicks",
        ),
        composition_bias=("vault", "ledger", "corporate", "healthcare", "dialogue"),
        type_bias=("libre_source", "cormorant_source", "space_grotesk_inter"),
        color_feeling="ink, stone, restrained accent",
        motion="understated",
        niches_affinity=("law", "accounting", "dental", "energy"),
    ),
}


def list_approaches() -> list[DesignApproach]:
    return list(DESIGN_APPROACHES.values())


def choose_studio_approach(
    *,
    niche_id: str,
    package_id: str = "business",
    diversity_salt: str = "",
    preferred: str | None = None,
) -> DesignApproach:
    """Pick studio approach first — then niche adapts to it."""
    if preferred and preferred in DESIGN_APPROACHES:
        return DESIGN_APPROACHES[preferred]

    niche = (niche_id or "generic").strip().lower()
    pid = (package_id or "business").strip().lower()
    salt = (diversity_salt or "").strip()

    scored: list[tuple[int, DesignApproach]] = []
    for approach in DESIGN_APPROACHES.values():
        score = 1
        if niche in approach.niches_affinity:
            score += 14
        if pid == "premium" and approach.id in ("luxury", "editorial", "boutique", "scandinavian"):
            score += 8
        if pid == "basic" and approach.id in ("scandinavian", "corporate_clear", "modern"):
            score += 4
        if pid == "business" and approach.id in ("editorial", "corporate_clear", "scandinavian", "boutique"):
            score += 5
        scored.append((score, approach))
    scored.sort(key=lambda x: (-x[0], x[1].id))
    top = [a for s, a in scored if s >= scored[0][0] - 6] or [scored[0][1]]
    idx = int(hashlib.sha256(f"{niche}|{pid}|approach|{salt}".encode()).hexdigest()[:8], 16)
    return top[idx % len(top)]
