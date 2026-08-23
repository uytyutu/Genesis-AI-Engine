"""Design Observatory — external quality compass for Virtus Core 2026+.

Before generation, study best-in-niche *principles* (never copy pixels):
first screen, rhythm, depth, typography, micro-interactions, trust, CTA craft.
Then invent an original Brand DNA + Creative Direction.

This is not a scraper. Curated observatory notes evolve with web design —
so the platform ages forward, not backward.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ObservatoryLens:
    """One principle lens the studio studies before inventing."""

    id: str
    question: str
    principles: tuple[str, ...]
    anti_patterns: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NicheObservatoryBrief:
    """Curated niche study — principles only, never a site clone brief."""

    niche_id: str
    era: str  # e.g. 2026+
    study_sources: tuple[str, ...]  # categories of excellence, not URLs to copy
    first_screen: tuple[str, ...]
    page_rhythm: tuple[str, ...]
    composition_depth: tuple[str, ...]
    typography: tuple[str, ...]
    micro_interactions: tuple[str, ...]
    trust: tuple[str, ...]
    cta_craft: tuple[str, ...]
    brand_feel: tuple[str, ...]
    invent: str  # what Factory must invent (original)
    never: tuple[str, ...] = ()
    lenses: tuple[ObservatoryLens, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["lenses"] = [x.as_dict() if hasattr(x, "as_dict") else x for x in self.lenses]
        return d

    def creative_brief(self) -> str:
        lines = [
            f"Design Observatory · {self.niche_id} · {self.era}",
            "Rule: analyze principles — invent original — never copy pixels.",
            "First screen: " + "; ".join(self.first_screen[:4]),
            "Rhythm: " + "; ".join(self.page_rhythm[:3]),
            "Depth: " + "; ".join(self.composition_depth[:3]),
            "Type: " + "; ".join(self.typography[:3]),
            "Motion: " + "; ".join(self.micro_interactions[:3]),
            "Trust: " + "; ".join(self.trust[:3]),
            "CTA: " + "; ".join(self.cta_craft[:3]),
            f"Invent: {self.invent}",
        ]
        if self.never:
            lines.append("Never: " + "; ".join(self.never[:5]))
        return "\n".join(lines)


_CORE_LENSES: tuple[ObservatoryLens, ...] = (
    ObservatoryLens(
        id="first_screen",
        question="Why does the first screen exist?",
        principles=(
            "One emotional job in 3 seconds",
            "Visual center owns the fold",
            "Brand voice before feature list",
        ),
        anti_patterns=("Hero as feature dump", "equal card grid first", "logo wall as hero"),
    ),
    ObservatoryLens(
        id="rhythm",
        question="How does the page breathe?",
        principles=(
            "Scenes with distinct moods",
            "Alternating density — never identical section padding",
            "Story → emotion → interaction → conversion",
        ),
        anti_patterns=("Hero→Text→Cards→Text→Cards", "uniform white slabs"),
    ),
    ObservatoryLens(
        id="trust",
        question="How is confidence earned?",
        principles=(
            "Proof woven into scenes, not bolted as a strip",
            "Specific over generic claims",
            "Quiet credentials beat badge spam",
        ),
        anti_patterns=("fake counters", "stock handshake photos as trust"),
    ),
    ObservatoryLens(
        id="cta",
        question="How does desire become action?",
        principles=(
            "CTA matches emotional temperature of the scene",
            "Secondary path without visual noise",
            "One primary ask per scene",
        ),
        anti_patterns=("identical pill buttons everywhere", "three equal CTAs"),
    ),
)


_OBSERVATORY: dict[str, NicheObservatoryBrief] = {
    "psychology": NicheObservatoryBrief(
        niche_id="psychology",
        era="2026+",
        study_sources=(
            "European private therapy practices",
            "Nordic wellness editorials",
            "Quiet luxury hospitality brands",
            "Premium mental-health SaaS landing craft",
        ),
        first_screen=(
            "Full-bleed calm photography or cinematic still",
            "Serif display voice — hush, not clinic",
            "One clear next step (Erstgespräch) without urgency theater",
            "Negative space that feels intentional, not empty",
        ),
        page_rhythm=(
            "Story before service grid",
            "Trust as intimacy, not badge strip first",
            "Gallery / atmosphere mid-page as emotional reset",
            "Late conversion after understanding",
        ),
        composition_depth=(
            "Layered atmosphere (air, soft mesh) in niche sage/sand — not purple clone",
            "Glass only where it earns emotion",
            "Asymmetry over equal cards",
        ),
        typography=(
            "Display serif for brand voice",
            "Humanist sans for body calm",
            "Generous line-height; short measure on hero",
        ),
        micro_interactions=(
            "Soft reveal on scroll",
            "Hover that breathes — no neon bounce",
            "Sticky nav that gains weight, not noise",
        ),
        trust=(
            "Schweigepflicht / confidentiality as craft, not legal dump",
            "Process as reassurance scenes",
            "Real location / hours without template chrome",
        ),
        cta_craft=(
            "Erstgespräch as invitation",
            "Secondary WhatsApp only if it fits calm brand",
            "No countdown or scarcity theater",
        ),
        brand_feel=("calm", "expensive quiet", "natural", "confident", "alive"),
        invent=(
            "Original Brand DNA for THIS practice: unique emotion, type voice, "
            "scene sequence, and why the Hero exists — never a recycled prior site."
        ),
        never=(
            "Salon glam stock",
            "Clinic fluorescent white",
            "Constructor card ladder",
            "Identical Business/Premium clones",
            "Purple Virtus App Store atmosphere",
        ),
        lenses=_CORE_LENSES,
    ),
    "law": NicheObservatoryBrief(
        niche_id="law",
        era="2026+",
        study_sources=(
            "Boutique European law firms",
            "Editorial corporate brand sites",
            "Quiet prestige consulting",
        ),
        first_screen=(
            "Authority without marble cliché",
            "Precise headline — one mandate",
            "Dark or ink editorial, not stock gavel",
        ),
        page_rhythm=(
            "Credentials early as craft",
            "Practice areas as narrative, not icon grid dump",
            "Contact as confident close",
        ),
        composition_depth=("Editorial columns", "Hairline rules used sparingly", "Photo as evidence"),
        typography=("Classical serif + precise sans", "Tight but readable scale"),
        micro_interactions=("Understated underline / ink shifts", "No playful bounce"),
        trust=("Named expertise", "Process clarity", "Impressum as professionalism"),
        cta_craft=("Erstberatung — calm, not salesy"),
        brand_feel=("prestige", "clarity", "confidence"),
        invent="Original firm personality — not a gray template with a logo.",
        never=("Stock handshake hero", "Fake award counters"),
        lenses=_CORE_LENSES,
    ),
    "restaurant": NicheObservatoryBrief(
        niche_id="restaurant",
        era="2026+",
        study_sources=(
            "Independent fine-casual brands",
            "Editorial food magazines",
            "Hospitality brand sites",
        ),
        first_screen=(
            "Appetite image owns the fold",
            "Reservation CTA as invitation",
            "Atmosphere before menu dump",
        ),
        page_rhythm=("Gallery hunger → story → menu → book"),
        composition_depth=("Full-bleed food/lifestyle", "Warm surfaces", "Sparse type"),
        typography=("Character display + soft sans"),
        micro_interactions=("Parallax soft", "Menu hover taste"),
        trust=("Real kitchen / team photos", "Hours & map clear"),
        cta_craft=("Reserve — one primary"),
        brand_feel=("warmth", "appetite", "alive"),
        invent="A restaurant brand scene sequence — not a delivery-app clone.",
        never=("Generic pizza stock for every cuisine"),
        lenses=_CORE_LENSES,
    ),
}


_GENERIC = NicheObservatoryBrief(
    niche_id="generic",
    era="2026+",
    study_sources=(
        "European digital studio portfolios",
        "Premium SaaS brand sites",
        "Luxury ecommerce craft",
    ),
    first_screen=(
        "Emotional job in 3 seconds",
        "Brand voice before feature list",
        "One visual center",
    ),
    page_rhythm=("Scene → Story → Emotion → Interaction → Experience → Conversion",),
    composition_depth=("Living atmosphere", "Asymmetry", "Depth layers"),
    typography=("Voice-matched display + readable body"),
    micro_interactions=("Purposeful motion — never decoration spam"),
    trust=("Specific proof woven into scenes"),
    cta_craft=("One primary ask per scene"),
    brand_feel=("modern", "confident", "alive"),
    invent="Original Brand DNA — forget previous Factory outputs.",
    never=("Constructor ladder", "White empty slabs", "Identical niche clones"),
    lenses=_CORE_LENSES,
)


def observe_niche(niche_id: str | None) -> NicheObservatoryBrief:
    """Return observatory brief for niche. Always invent original — never copy."""
    key = (niche_id or "generic").strip().lower() or "generic"
    return _OBSERVATORY.get(key) or replace_niche(_GENERIC, key)


def replace_niche(brief: NicheObservatoryBrief, niche_id: str) -> NicheObservatoryBrief:
    return NicheObservatoryBrief(
        niche_id=niche_id,
        era=brief.era,
        study_sources=brief.study_sources,
        first_screen=brief.first_screen,
        page_rhythm=brief.page_rhythm,
        composition_depth=brief.composition_depth,
        typography=brief.typography,
        micro_interactions=brief.micro_interactions,
        trust=brief.trust,
        cta_craft=brief.cta_craft,
        brand_feel=brief.brand_feel,
        invent=f"Original Brand DNA for {niche_id} — invent, never recycle prior sites.",
        never=brief.never,
        lenses=brief.lenses,
    )


def observatory_creative_brief(niche_id: str | None) -> str:
    return observe_niche(niche_id).creative_brief()
