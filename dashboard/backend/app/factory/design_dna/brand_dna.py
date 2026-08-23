"""Brand DNA — art-director chain from Creative Identity.

Not Luxury/Minimal/Editorial labels as the brand.
Chain: Brand Story → Core Emotion → Core Promise → Visual Metaphor →
Creative Theme → Scene/Motion/Type/Color/Interaction languages.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

from app.factory.design_dna.creative_identity import (
    CreativeIdentity,
    invent_creative_identity,
)
from app.factory.design_dna.design_observatory import NicheObservatoryBrief, observe_niche


@dataclass(frozen=True)
class BrandDNA:
    """Personality from Creative Identity — not a recycled niche skin."""

    business_name: str
    niche_id: str
    package_id: str
    voice: str
    feeling: str
    why_hero_exists: str
    color_feeling: str
    type_voice: str
    scene_arc: str
    avoid: tuple[str, ...]
    fingerprint: str
    # Art-director chain
    brand_story: str = ""
    core_emotion: str = ""
    core_promise: str = ""
    visual_metaphor: str = ""
    creative_theme: str = ""
    creative_theme_id: str = ""
    scene_language: str = ""
    motion_language: str = ""
    interaction_style: str = ""
    photo_world: str = ""
    founder_name: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def brand_dna_from_identity(identity: CreativeIdentity) -> BrandDNA:
    h = identity.human or {}
    return BrandDNA(
        business_name=str(h.get("founder_name") or identity.title),
        niche_id=identity.niche_revealed,
        package_id=identity.package_id,
        voice=identity.typography_voice,
        feeling=identity.core_emotion,
        why_hero_exists=(
            f"The Hero exists to make '{identity.title}' felt in 3 seconds: {identity.idea}"
        ),
        color_feeling=identity.color_emotion,
        type_voice=identity.typography_voice,
        scene_arc=identity.scene_language,
        avoid=tuple(identity.forbidden),
        fingerprint=identity.fingerprint,
        brand_story=identity.brand_story,
        core_emotion=identity.core_emotion,
        core_promise=identity.core_promise,
        visual_metaphor=identity.visual_metaphor,
        creative_theme=identity.creative_theme,
        creative_theme_id=identity.theme_id,
        scene_language=identity.scene_language,
        motion_language=identity.motion_language,
        interaction_style=identity.interaction_style,
        photo_world=identity.photo_world,
        founder_name=str(h.get("founder_name") or ""),
    )


def invent_brand_dna(
    *,
    business_name: str,
    niche_id: str,
    package_id: str = "business",
    diversity_salt: str = "",
    observatory: NicheObservatoryBrief | None = None,
    surface: str = "site",
    approach_id: str = "",
) -> BrandDNA:
    """Invent Creative Identity first — niche is revealed after the human."""
    _ = observatory or observe_niche(niche_id)  # still available for later stages
    identity = invent_creative_identity(
        business_name=business_name,
        niche_id=niche_id,
        package_id=package_id,
        surface=surface,
        diversity_salt=diversity_salt,
        approach_id=approach_id,
    )
    dna = brand_dna_from_identity(identity)
    # Keep business_name as company name for factory compatibility
    name = (business_name or "Business").strip() or "Business"
    fp = hashlib.sha256(
        f"{name}|{dna.creative_theme_id}|{package_id}|{diversity_salt}".encode()
    ).hexdigest()[:24]
    return BrandDNA(
        business_name=name,
        niche_id=dna.niche_id,
        package_id=dna.package_id,
        voice=dna.voice,
        feeling=dna.feeling,
        why_hero_exists=dna.why_hero_exists,
        color_feeling=dna.color_feeling,
        type_voice=dna.type_voice,
        scene_arc=dna.scene_arc,
        avoid=dna.avoid,
        fingerprint=fp,
        brand_story=dna.brand_story,
        core_emotion=dna.core_emotion,
        core_promise=dna.core_promise,
        visual_metaphor=dna.visual_metaphor,
        creative_theme=dna.creative_theme,
        creative_theme_id=dna.creative_theme_id,
        scene_language=dna.scene_language,
        motion_language=dna.motion_language,
        interaction_style=dna.interaction_style,
        photo_world=dna.photo_world,
        founder_name=dna.founder_name,
    )
