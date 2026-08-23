"""Digital Creative Studio — Virtus Core 2026+.

Think like a studio team. Design the digital face of a business.
Brand DNA → Direction board → Creative Review → HTML (final export only).
Design Observatory studies niche principles — never copies pixels.
Never auto-PASS. Scenes, not section stacks.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from app.factory.design_dna.agency_os import (
    DIGITAL_SIGNATURE,
    MANIFEST_ID,
    build_agency_review,
)
from app.factory.design_dna.brand_dna import BrandDNA, brand_dna_from_identity, invent_brand_dna
from app.factory.design_dna.brand_book import (
    BrandBook,
    apply_brand_book_to_dna,
    brand_book_css_vars,
    resolve_brand_book,
)
from app.factory.design_dna.atmosphere_pack import (
    AtmospherePack,
    build_atmosphere_pack,
)
from app.factory.design_dna.concept_gate import (
    REALITY_BENCHMARK_NOTE,
    REALITY_BENCHMARK_STATUS,
    should_export_marketing_html,
)
from app.factory.design_dna.creative_identity import (
    CreativeIdentity,
    invent_creative_identity,
    write_creative_identity,
)
from app.factory.design_dna.composition_library import (
    CompositionConcept,
    compositions_for_niche,
    is_predictable_funnel,
    rhythm_signature,
)
from app.factory.design_dna.design_approaches import (
    DesignApproach,
    choose_studio_approach,
)
from app.factory.design_dna.design_observatory import (
    NicheObservatoryBrief,
    observe_niche,
)
from app.factory.design_dna.dna import DesignDNA
from app.factory.design_dna.experience_memory import (
    ExperienceRecord,
    bias_from_memory,
    prior_best_overall,
    remember_experience,
)
from app.factory.design_dna.resolve import resolve_design_dna
from app.factory.design_dna.studio_acceptance import OWNER_PASS_PHRASE
from app.factory.design_dna.studio_law import (
    ERA_NAME,
    ERA_PRODUCT_NAME,
    LAW_1,
    LAW_2,
    enforce_law_1,
)
from app.factory.design_dna.taste_engine import TasteVerdict, evaluate_taste
from app.factory.design_dna.visual_benchmark import (
    quality_floor_for,
    require_visual_benchmark,
)
from app.factory.layout_variants import LayoutProfile, get_layout_profile
from app.factory.design_dna.rhythm import DEFAULT_SECTION_KEYS


STUDIO_ID = "digital_creative_studio_v4_studio_era"
VARIANT_COUNT_PREMIUM = 10
VARIANT_COUNT_BUSINESS = 6

# Direction board — Creative Identity first; HTML is last export only
PIPELINE_STAGES: tuple[str, ...] = (
    "human_first",
    "brand_story",
    "core_emotion",
    "core_promise",
    "visual_metaphor",
    "creative_theme",
    "scene_language",
    "motion_language",
    "typography_voice",
    "color_emotion",
    "interaction_style",
    "creative_conflict",
    "owner_preview",
)

# Allowed emotional arc (scenes — not section stacks)
SCENE_ARC: tuple[str, ...] = (
    "scene",
    "story",
    "emotion",
    "interaction",
    "experience",
    "conversion",
)

# Map structural keys → scene roles (impression vocabulary)
_SECTION_TO_SCENE: dict[str, str] = {
    "about": "story",
    "gallery": "emotion",
    "showcase": "scene",
    "services": "experience",
    "reputation": "interaction",
    "benefits": "emotion",
    "trust": "interaction",
    "process": "experience",
    "mid_cta": "conversion",
    "late_cta": "conversion",
    "contact": "conversion",
    "faq": "interaction",
    "reviews": "interaction",
    "maps": "interaction",
    "stats": "interaction",
    "catalog": "experience",
    "info": "story",
}


@dataclass(frozen=True)
class Moodboard:
    niche_id: str
    emotion: str
    keywords: tuple[str, ...]
    avoid: tuple[str, ...]
    hero_feeling: str
    atmosphere: str
    references: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConceptVariant:
    composition: CompositionConcept
    dna: DesignDNA
    layout_profile: LayoutProfile
    hero_layout: str
    score: float
    reasons: tuple[str, ...]
    rejected: bool = False
    reject_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "composition_id": self.composition.id,
            "composition_label": self.composition.label,
            "hero_layout": self.hero_layout,
            "layout_profile": self.layout_profile.id,
            "dna_style": self.dna.style,
            "dna_composition": self.dna.composition,
            "section_order": list(self.layout_profile.section_order),
            "score": round(self.score, 3),
            "reasons": list(self.reasons),
            "rejected": self.rejected,
            "reject_reason": self.reject_reason,
            "rhythm": rhythm_signature(self.layout_profile.section_order),
        }


@dataclass
class StudioDirection:
    """Digital Experience direction — final HTML export only."""

    studio_id: str = STUDIO_ID
    package_id: str = "premium"
    niche_id: str = "generic"
    moodboard: Moodboard | None = None
    business_identity: Any = None
    brand_book: BrandBook | None = None
    atmosphere_pack: AtmospherePack | None = None
    brand_dna: BrandDNA | None = None
    creative_identity: CreativeIdentity | None = None
    observatory: NicheObservatoryBrief | None = None
    studio_approach: DesignApproach | None = None
    observatory_brief: str = ""
    benchmark_brief: str = ""
    quality_floor: str = ""
    variants_considered: list[dict[str, Any]] = field(default_factory=list)
    chosen: ConceptVariant | None = None
    dna: DesignDNA | None = None
    layout_profile: LayoutProfile | None = None
    hero_layout: str = "D"
    scene_sequence: list[str] = field(default_factory=list)
    why_hero_exists: str = ""
    taste: TasteVerdict | None = None
    law_1: dict[str, Any] = field(default_factory=dict)
    memory_bias: dict[str, Any] = field(default_factory=dict)
    owner_review: str = "PENDING_OWNER"
    owner_required: str = OWNER_PASS_PHRASE
    optimize_for: str = "designer_decisions_and_taste"
    note: str = (
        f"{ERA_NAME}: {ERA_PRODUCT_NAME}. Template-like = REBUILD. "
        "Agent may not PASS. Owner sell-readiness only."
    )
    generation_status: str = "OK_TO_BUILD"
    pipeline: tuple[str, ...] = PIPELINE_STAGES
    philosophy: str = "virtus_core_studio_era_digital_experience_generation"
    creative_review: str = "PENDING"
    kpi_question: str = (
        "Without Virtus Core logo — would a stranger believe a modern "
        "European digital studio built this?"
    )
    era: str = ERA_NAME
    product_noun: str = ERA_PRODUCT_NAME
    immutable_law_1: str = LAW_1
    immutable_law_2: str = LAW_2
    manifest_id: str = MANIFEST_ID
    digital_signature_aim: str = DIGITAL_SIGNATURE.aim
    agency_review: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "studio_id": self.studio_id,
            "era": self.era,
            "product_noun": self.product_noun,
            "manifest_id": self.manifest_id,
            "digital_signature_aim": self.digital_signature_aim,
            "philosophy": self.philosophy,
            "immutable_law_1": self.immutable_law_1,
            "immutable_law_2": self.immutable_law_2,
            "pipeline": list(self.pipeline),
            "scene_arc": list(SCENE_ARC),
            "package_id": self.package_id,
            "niche_id": self.niche_id,
            "studio_approach": self.studio_approach.as_dict() if self.studio_approach else None,
            "moodboard": self.moodboard.as_dict() if self.moodboard else None,
            "business_identity": self.business_identity.as_dict()
            if self.business_identity is not None
            and hasattr(self.business_identity, "as_dict")
            else None,
            "brand_book": self.brand_book.as_dict() if self.brand_book else None,
            "atmosphere_pack": self.atmosphere_pack.as_dict()
            if self.atmosphere_pack
            else None,
            "brand_dna": self.brand_dna.as_dict() if self.brand_dna else None,
            "creative_identity": self.creative_identity.as_dict()
            if self.creative_identity
            else None,
            "observatory": self.observatory.as_dict() if self.observatory else None,
            "observatory_brief": self.observatory_brief,
            "benchmark_brief": self.benchmark_brief,
            "quality_floor": self.quality_floor,
            "why_hero_exists": self.why_hero_exists,
            "scene_sequence": list(self.scene_sequence),
            "taste": self.taste.as_dict() if self.taste else None,
            "law_1": dict(self.law_1),
            "memory_bias": dict(self.memory_bias),
            "agency_review": dict(self.agency_review),
            "variants_considered": self.variants_considered,
            "chosen": self.chosen.as_dict() if self.chosen else None,
            "dna": self.dna.as_dict() if self.dna else None,
            "layout_profile_id": self.layout_profile.id if self.layout_profile else None,
            "section_order": list(self.layout_profile.section_order)
            if self.layout_profile
            else [],
            "hero_layout": self.hero_layout,
            "generation_status": self.generation_status,
            "creative_review": self.creative_review,
            "kpi_question": self.kpi_question,
            "owner_review": self.owner_review,
            "owner_required": self.owner_required,
            "optimize_for": self.optimize_for,
            "note": self.note,
        }


_MOOD_BY_NICHE: dict[str, Moodboard] = {
    "psychology": Moodboard(
        niche_id="psychology",
        emotion="calm sanctuary",
        keywords=(
            "quiet luxury",
            "nature path",
            "editorial stillness",
            "glass soft light",
            "breathing space",
        ),
        avoid=(
            "salon glam",
            "clinic fluorescent",
            "equal card grid first",
            "purple mesh clone",
            "Hero→cards→text ladder",
        ),
        hero_feeling="3-second hush — expensive quiet, not a template",
        atmosphere="living sage/sand air — Virtus depth, niche color",
        references=(
            "European private therapy studios",
            "Nordic wellness editorial sites",
        ),
    ),
}


def build_moodboard(niche_id: str | None, *, business_name: str = "") -> Moodboard:
    niche = (niche_id or "generic").strip().lower()
    if niche in _MOOD_BY_NICHE:
        return _MOOD_BY_NICHE[niche]
    return Moodboard(
        niche_id=niche,
        emotion="contemporary craft",
        keywords=("depth", "rhythm", "hero presence", "niche truth"),
        avoid=("template ladder", "flat white", "metric PASS theater"),
        hero_feeling="first three seconds must sell the craft",
        atmosphere="living canvas, niche palette",
        references=("Best contemporary niche studios",),
    )


def _profile_with_order(seed_id: str, concept: CompositionConcept) -> LayoutProfile:
    from app.factory.design_dna.reputation_pack import inject_reputation_into_order

    base = get_layout_profile(concept.layout_seed or seed_id or "L6")
    return replace(
        base,
        id=f"{base.id}-{concept.id}",
        label=f"{base.label} · {concept.label}",
        section_order=inject_reputation_into_order(concept.section_order),
        preferred_component=concept.component,
        hero_variants=concept.hero_layouts,
    )


def _score_variant(
    *,
    concept: CompositionConcept,
    dna: DesignDNA,
    niche: str,
    package_id: str,
    bench_keywords: tuple[str, ...],
) -> tuple[float, tuple[str, ...], bool, str]:
    reasons: list[str] = []
    score = 40.0
    order = concept.section_order

    if is_predictable_funnel(order):
        return 5.0, ("too predictable — classic section ladder",), True, "predictable_funnel"

    if concept.anti_predictable:
        score += 12
        reasons.append("anti-predictable composition")
    else:
        score -= 8
        reasons.append("closer to funnel — demoted for Premium")

    if niche in concept.niche_affinity:
        score += 18
        reasons.append(f"niche affinity:{niche}")

    if package_id == "premium":
        if concept.hero_layouts[0] in ("B", "D", "F"):
            score += 10
            reasons.append("cinematic hero preference")
        if dna.composition in ("immersive", "magazine", "organic"):
            score += 6
            reasons.append(f"dna composition:{dna.composition}")

    # Benchmark keyword overlap (soft)
    blob = f"{concept.label} {concept.mood} {concept.notes} {dna.style}".lower()
    hits = sum(1 for k in bench_keywords if k.lower() in blob)
    score += hits * 3
    if hits:
        reasons.append(f"benchmark hits:{hits}")

    # Prefer early story/gallery/about over services for psychology Premium
    if niche == "psychology" and package_id == "premium":
        early = order[:3]
        if any(k in early for k in ("about", "gallery", "showcase", "process", "trust")):
            score += 10
            reasons.append("story-before-offer early fold")
        if early[:1] == ("services",) or early[:2] == ("info", "stats"):
            score -= 15
            reasons.append("offer/stats too early")

    return score, tuple(reasons), False, ""


def _pick_hero(concept: CompositionConcept, *, package_id: str, niche: str, seed: str) -> str:
    pool = concept.hero_layouts
    if package_id == "premium" and niche == "psychology":
        # Prefer cinematic glass when concept allows
        for h in ("D", "B", "F"):
            if h in pool:
                return h
    idx = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % len(pool)
    return pool[idx]


def _scene_sequence(section_order: tuple[str, ...] | list[str]) -> list[str]:
    """Map structural keys to scene vocabulary (impression, not HTML)."""
    out: list[str] = ["scene"]  # Hero is always first scene
    for key in section_order:
        role = _SECTION_TO_SCENE.get(key, "experience")
        if not out or out[-1] != role:
            out.append(role)
    return out


def _creative_review(direction: StudioDirection) -> str:
    """Internal Creative Review before HTML. Template-like → FAIL_REBUILD."""
    if direction.generation_status == "FAIL_TEMPLATE":
        return "FAIL_REBUILD"
    if direction.chosen is None or direction.layout_profile is None:
        return "FAIL_REBUILD"
    if is_predictable_funnel(direction.layout_profile.section_order):
        return "FAIL_REBUILD"
    if direction.chosen.rejected:
        return "FAIL_REBUILD"
    # Internal structural OK — never visual PASS (owner only)
    return "PASS_INTERNAL"


def run_digital_creative_studio(
    *,
    business_name: str,
    niche_id: str,
    package_id: str,
    diversity_salt: str = "",
    product_dir: Path | None = None,
    variant_count: int | None = None,
    surface: str = "site",
) -> StudioDirection:
    """Studio team loop: design the brand first. HTML is never the first stage."""
    niche = (niche_id or "generic").strip().lower() or "generic"
    pid = (package_id or "basic").strip().lower() or "basic"
    name = (business_name or "Business").strip() or "Business"
    salt = (diversity_salt or "").strip()
    surf = (surface or "site").strip().lower() or "site"

    direction = StudioDirection(package_id=pid, niche_id=niche)
    direction.agency_review = build_agency_review(
        niche_id=niche,
        package_id=pid,
        business_name=name,
    ).as_dict()

    # 1) Forget prior sites — Design Observatory (principles, never copy)
    obs = observe_niche(niche)
    direction.observatory = obs
    direction.observatory_brief = obs.creative_brief()

    # 0) Business Identity — root digital profile (feeds Brand Book → packs)
    try:
        from app.factory.design_dna.business_identity import resolve_business_identity

        direction.business_identity = resolve_business_identity(
            business_name=name,
            niche_id=niche,
            package_id=pid,
            diversity_salt=salt,
        )
    except Exception:
        direction.business_identity = None

    # 1a) Brand Book FIRST — company personality before themes / DNA / HTML
    book = resolve_brand_book(
        business_name=name,
        niche_id=niche,
        package_id=pid,
        diversity_salt=salt,
    )
    direction.brand_book = book

    # 1b) Creative Identity — constrained by Brand Book voice / metaphor / forbid
    from app.factory.design_dna.creative_identity import (
        CREATIVE_THEMES,
        check_creative_conflict,
    )
    from app.factory.design_dna.design_approaches import DESIGN_APPROACHES
    from dataclasses import replace as dc_replace

    identity = invent_creative_identity(
        business_name=name,
        niche_id=niche,
        package_id=pid,
        surface=surf,
        diversity_salt=salt,
        approach_id="",
        allow_html_export=should_export_marketing_html(),
        html_blocked_reason=REALITY_BENCHMARK_NOTE,
        hero_hint=book.visual_metaphor,
        motion_hint=book.motion_language,
        type_hint=f"{book.typography_display} + {book.typography_body}",
    )
    theme_obj = next((t for t in CREATIVE_THEMES if t.id == identity.theme_id), None)
    approach = choose_studio_approach(niche_id=niche, package_id=pid, diversity_salt=salt)
    if theme_obj is not None and not check_creative_conflict(
        theme_obj, approach_id=approach.id
    ).ok:
        for _aid, cand in DESIGN_APPROACHES.items():
            if check_creative_conflict(theme_obj, approach_id=cand.id).ok:
                approach = cand
                break
    identity = invent_creative_identity(
        business_name=name,
        niche_id=niche,
        package_id=pid,
        surface=surf,
        diversity_salt=salt,
        approach_id=approach.id,
        allow_html_export=should_export_marketing_html(),
        html_blocked_reason=REALITY_BENCHMARK_NOTE,
        hero_hint=book.visual_metaphor,
        motion_hint=book.motion_language,
        type_hint=f"{book.typography_display} + {book.typography_body}",
    )
    direction.studio_approach = approach
    direction.memory_bias = bias_from_memory(niche)
    if not identity.conflict.get("ok", True):
        direction.generation_status = "CREATIVE_CONFLICT"
        direction.note = (
            f"Creative Conflict: {identity.title} — "
            + "; ".join(identity.conflict.get("conflicts") or [])
        )
    direction.creative_identity = identity
    brand = dc_replace(
        brand_dna_from_identity(identity),
        business_name=name,
        core_promise=book.brand_promise or identity.core_promise,
        core_emotion=book.core_emotion or identity.core_emotion,
        visual_metaphor=book.visual_metaphor or identity.visual_metaphor,
        scene_language=" · ".join(book.scene_language) or identity.scene_language,
        motion_language=book.motion_language or identity.motion_language,
        photo_world=" · ".join(book.photography) or identity.photo_world,
        avoid=tuple(dict.fromkeys(list(identity.forbidden) + list(book.forbidden))),
        feeling=book.core_emotion or identity.core_emotion,
        type_voice=f"{book.typography_display} / {book.typography_body}",
        color_feeling=book.visual_style,
    )
    direction.brand_dna = brand
    direction.why_hero_exists = (
        f"Hero exists for '{name}': {book.visual_metaphor} — {book.brand_promise}"
    )

    direction.moodboard = build_moodboard(niche, business_name=name)
    if direction.moodboard is not None:
        direction.moodboard = Moodboard(
            niche_id=direction.moodboard.niche_id,
            emotion=book.core_emotion or identity.core_emotion,
            keywords=direction.moodboard.keywords
            + (book.visual_style.lower(),)
            + tuple(s.lower() for s in book.scene_language[:3]),
            avoid=tuple(
                dict.fromkeys(
                    list(direction.moodboard.avoid)
                    + list(identity.forbidden)
                    + list(book.forbidden)
                )
            ),
            hero_feeling=book.visual_metaphor or identity.idea,
            atmosphere=" · ".join(book.scene_language) or identity.scene_language,
            references=direction.moodboard.references,
        )
    bench = require_visual_benchmark(niche, package_id=pid)
    direction.benchmark_brief = bench.design_brief() if bench else ""
    direction.quality_floor = quality_floor_for(pid)

    if pid == "basic":
        # Starter still gets full Creative Identity — never jump to HTML first
        dna = resolve_design_dna(
            business_name=name,
            niche_id=niche,
            package_id=pid,
            section_keys=DEFAULT_SECTION_KEYS,
            diversity_salt=salt,
        )
        dna = apply_brand_book_to_dna(dna, book)
        direction.dna = dna
        direction.atmosphere_pack = build_atmosphere_pack(book, dna)
        direction.hero_layout = dna.hero_layout
        direction.scene_sequence = _scene_sequence(DEFAULT_SECTION_KEYS)
        direction.creative_review = "PASS_INTERNAL"
        direction.owner_review = "PENDING_OWNER"
        direction.note = (
            f"{REALITY_BENCHMARK_STATUS}: {REALITY_BENCHMARK_NOTE} "
            "Brand Book + Atmosphere Pack direct the experience before marketing HTML."
        )
        _finalize_concept_artifacts(product_dir, direction, surface=surf)
        _write_direction(product_dir, direction)
        return direction

    n = variant_count or (
        VARIANT_COUNT_PREMIUM if pid == "premium" else VARIANT_COUNT_BUSINESS
    )
    pool = compositions_for_niche(niche, premium=(pid == "premium"))
    # Prefer compositions that match chosen studio approach + memory bias
    prefer = set(approach.composition_bias) | set(direction.memory_bias.get("compositions") or [])
    if prefer:
        preferred = [c for c in pool if c.id in prefer]
        rest = [c for c in pool if c.id not in prefer]
        pool = preferred + rest
    # Diversity salt rotates which slice of the library we consider
    offset = int(hashlib.sha256(f"{name}|{salt}|studio".encode()).hexdigest()[:6], 16)
    rotated = pool[offset % len(pool) :] + pool[: offset % len(pool)]
    candidates = rotated[: max(n, 5)]

    bench_kw = tuple(direction.moodboard.keywords) if direction.moodboard else ()
    # Observatory brand-feel keywords boost scoring
    bench_kw = bench_kw + tuple(obs.brand_feel) + tuple(obs.first_screen[:2])
    variants: list[ConceptVariant] = []

    for i, concept in enumerate(candidates):
        dna = resolve_design_dna(
            business_name=name,
            niche_id=niche,
            package_id=pid,
            section_keys=concept.section_order or DEFAULT_SECTION_KEYS,
            diversity_salt=f"{salt}|comp:{concept.id}|{i}",
        )
        # Force DNA composition string to concept id for CSS hooks
        dna = replace(dna, composition=concept.id)
        dna = apply_brand_book_to_dna(dna, book)
        profile = _profile_with_order(concept.layout_seed, concept)
        hero = _pick_hero(
            concept,
            package_id=pid,
            niche=niche,
            seed=f"{name}|{pid}|{concept.id}|hero|{salt}",
        )
        score, reasons, rejected, reject_reason = _score_variant(
            concept=concept,
            dna=dna,
            niche=niche,
            package_id=pid,
            bench_keywords=bench_kw,
        )
        # Score: scene arc early (story/emotion before card dump)
        early_scenes = _scene_sequence(concept.section_order)[:4]
        if "story" in early_scenes or "emotion" in early_scenes:
            score += 6
            reasons = reasons + ("scene_arc_story_emotion_early",)
        variants.append(
            ConceptVariant(
                composition=concept,
                dna=dna,
                layout_profile=profile,
                hero_layout=hero,
                score=score,
                reasons=reasons,
                rejected=rejected,
                reject_reason=reject_reason,
            )
        )

    # Template-like = Generation FAIL. Never silently accept a predictable funnel.
    alive = [v for v in variants if not v.rejected]
    if not alive:
        direction.generation_status = "FAIL_TEMPLATE"
        direction.owner_review = "PENDING_OWNER"
        # Still surface the least-bad candidate for REBUILD diagnostics — not a PASS.
        alive = sorted(variants, key=lambda v: v.score, reverse=True)[:1]
        direction.note = (
            "FAIL_TEMPLATE: all variants predictable or rejected. REBUILD required. "
            "Agent may not PASS."
        )
    alive.sort(key=lambda v: v.score, reverse=True)
    chosen = alive[0]
    if chosen.rejected or is_predictable_funnel(chosen.layout_profile.section_order):
        direction.generation_status = "FAIL_TEMPLATE"
        direction.note = (
            "FAIL_TEMPLATE: chosen rhythm reads as template. REBUILD required."
        )

    # Hero 3-second rule (structural proxy): Premium must use cinematic hero
    if pid == "premium" and chosen.hero_layout not in ("B", "D", "F"):
        for alt in alive[1:]:
            if alt.hero_layout in ("B", "D", "F"):
                chosen = alt
                break
        else:
            chosen = ConceptVariant(
                composition=chosen.composition,
                dna=chosen.dna,
                layout_profile=chosen.layout_profile,
                hero_layout="D",
                score=chosen.score + 2,
                reasons=chosen.reasons + ("hero_3s_force_cinematic",),
            )
    # Business must NOT clone Premium wow — prefer calm layouts when available
    if pid == "business" and niche == "psychology" and chosen.hero_layout in ("B", "D", "F"):
        for alt in alive:
            if alt.hero_layout in ("A", "C", "E"):
                chosen = ConceptVariant(
                    composition=alt.composition,
                    dna=alt.dna,
                    layout_profile=alt.layout_profile,
                    hero_layout=alt.hero_layout,
                    score=alt.score + 3,
                    reasons=alt.reasons + ("tier_ladder_not_premium_clone",),
                )
                break
        else:
            chosen = ConceptVariant(
                composition=chosen.composition,
                dna=chosen.dna,
                layout_profile=chosen.layout_profile,
                hero_layout="C",
                score=chosen.score,
                reasons=chosen.reasons + ("tier_ladder_force_calm",),
            )

    direction.variants_considered = [v.as_dict() for v in variants]
    direction.chosen = chosen
    # Keep DNA hero in sync with chosen (CSS atm_mode keys off dna.hero_layout)
    direction.dna = replace(chosen.dna, hero_layout=chosen.hero_layout, composition=chosen.composition.id)
    if direction.brand_book is not None and direction.dna is not None:
        direction.atmosphere_pack = build_atmosphere_pack(direction.brand_book, direction.dna)
    direction.layout_profile = chosen.layout_profile
    direction.hero_layout = chosen.hero_layout
    direction.scene_sequence = _scene_sequence(chosen.layout_profile.section_order)
    direction.owner_review = "PENDING_OWNER"

    # Creative Review — template-like = immediate REBUILD (never visual PASS)
    direction.creative_review = _creative_review(direction)
    if direction.creative_review == "FAIL_REBUILD":
        direction.generation_status = "FAIL_TEMPLATE"
        direction.note = (
            "Creative Review FAIL_REBUILD: template-like impression. "
            "Rebuild required. Agent may not PASS."
        )

    # AI Taste Engine — holistic judgment (not rigid white-section rules)
    prior = prior_best_overall(niche)
    taste = evaluate_taste(
        composition_id=chosen.composition.id,
        hero_layout=chosen.hero_layout,
        scene_sequence=direction.scene_sequence,
        brand_feeling=brand.feeling,
        why_hero_exists=brand.why_hero_exists,
        studio_approach=approach.id,
        package_id=pid,
        predictable_funnel=is_predictable_funnel(chosen.layout_profile.section_order),
        generation_status=direction.generation_status,
        fingerprint=chosen.dna.fingerprint if chosen.dna else "",
        prior_best_overall=prior,
    )
    direction.taste = taste

    # Law #1 — never worse than previous best / never constructor
    law = enforce_law_1(
        taste_overall=taste.overall,
        prior_best_overall=prior,
        template_like=direction.generation_status == "FAIL_TEMPLATE",
        constructor_like=is_predictable_funnel(chosen.layout_profile.section_order),
        below_studio_bar=taste.verdict in ("FAIL_TASTE", "WEAK") and pid == "premium",
    )
    direction.law_1 = law.as_dict()
    if law.action == "REBUILD" or taste.rebuild:
        direction.generation_status = "REBUILD"
        direction.creative_review = "FAIL_REBUILD"
        direction.note = (
            f"Law #1 / Taste REBUILD: {'; '.join(law.reasons) or '; '.join(taste.reasons)}. "
            "Agent may not PASS."
        )

    # Remember strong internal taste for future bias (not owner PASS)
    if taste.overall >= 70 and direction.generation_status == "OK_TO_BUILD":
        try:
            remember_experience(
                ExperienceRecord(
                    niche_id=niche,
                    package_id=pid,
                    composition_id=chosen.composition.id,
                    hero_layout=chosen.hero_layout,
                    typography_pair=chosen.dna.typography_pair if chosen.dna else "",
                    studio_approach=approach.id,
                    palette_family=chosen.dna.palette_family if chosen.dna else "",
                    why_hero_exists=brand.why_hero_exists,
                    scene_sequence=list(direction.scene_sequence),
                    taste_overall=taste.overall,
                    owner_accepted=False,
                    notes="auto-memory from STRONG/PROMISING taste — not owner PASS",
                )
            )
        except OSError:
            pass

    # Artifacts before HTML — full Design Concept Pack (Owner Preview)
    _finalize_concept_artifacts(product_dir, direction, surface=surf)

    _write_direction(product_dir, direction)
    return direction


def _finalize_concept_artifacts(
    product_dir: Path | None,
    direction: StudioDirection,
    *,
    surface: str = "site",
) -> None:
    """Write Creative Identity + Owner Preview. Marketing HTML is a later export."""
    if product_dir is None:
        return
    try:
        product_dir.mkdir(parents=True, exist_ok=True)
        if direction.observatory is not None:
            (product_dir / "design_observatory.json").write_text(
                json.dumps(direction.observatory.as_dict(), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
        if direction.brand_book is not None:
            (product_dir / "brand_book.json").write_text(
                json.dumps(direction.brand_book.as_dict(), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
            (product_dir / "brand_book.txt").write_text(
                direction.brand_book.as_text() + "\n",
                encoding="utf-8",
            )
        try:
            from app.factory.design_dna.business_identity import (
                resolve_business_identity,
                write_business_identity,
            )

            ident = getattr(direction, "business_identity", None) or resolve_business_identity(
                business_name=direction.brand_book.brand_name
                if direction.brand_book
                else "Business",
                niche_id=direction.niche_id,
                package_id=direction.package_id,
            )
            write_business_identity(product_dir, ident)
        except Exception:
            pass
        if direction.atmosphere_pack is not None:
            (product_dir / "atmosphere_pack.json").write_text(
                json.dumps(direction.atmosphere_pack.as_dict(), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
        try:
            from app.factory.design_dna.reputation_pack import write_reputation_pack

            write_reputation_pack(
                product_dir,
                business_name=direction.brand_book.brand_name
                if direction.brand_book
                else "Business",
                niche_id=direction.niche_id,
                package_id=direction.package_id,
            )
        except Exception:
            pass
        if direction.brand_dna is not None:
            (product_dir / "brand_dna.json").write_text(
                json.dumps(direction.brand_dna.as_dict(), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
        if direction.agency_review:
            (product_dir / "agency_os_review.json").write_text(
                json.dumps(direction.agency_review, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        allow = should_export_marketing_html(
            studio_generation_status=direction.generation_status
        )
        identity = direction.creative_identity
        if identity is None:
            approach_id = direction.studio_approach.id if direction.studio_approach else ""
            identity = invent_creative_identity(
                business_name=direction.brand_dna.business_name
                if direction.brand_dna
                else "Business",
                niche_id=direction.niche_id,
                package_id=direction.package_id,
                surface=surface,
                diversity_salt=f"{direction.niche_id}|{direction.package_id}",
                approach_id=approach_id,
                hero_hint=direction.hero_layout or (
                    direction.brand_dna.visual_metaphor if direction.brand_dna else ""
                ),
                motion_hint=(
                    direction.brand_dna.motion_language if direction.brand_dna else ""
                ),
                type_hint=direction.brand_dna.type_voice if direction.brand_dna else "",
                allow_html_export=allow,
                html_blocked_reason="" if allow else REALITY_BENCHMARK_NOTE,
                founder_hint=direction.brand_dna.founder_name if direction.brand_dna else "",
            )
            direction.creative_identity = identity
        else:
            # Refresh export flags for this write
            identity.html_export_allowed = bool(allow) and bool(
                identity.conflict.get("ok", True)
            )
            identity.html_blocked_reason = (
                ""
                if identity.html_export_allowed
                else (
                    identity.html_blocked_reason
                    or REALITY_BENCHMARK_NOTE
                )
            )
        if not identity.conflict.get("ok", True):
            direction.generation_status = "CREATIVE_CONFLICT"
            direction.note = (
                f"Creative Conflict FAIL for {identity.title}: "
                + "; ".join(identity.conflict.get("conflicts") or [])
            )
        write_creative_identity(product_dir, identity)
        approach_id = direction.studio_approach.id if direction.studio_approach else ""
        sketch = {
            "stage": "creative_identity",
            "naming": "Creative Identity — not Concept",
            "before_html": True,
            "era": ERA_NAME,
            "sprint": "Creative Identity Generation",
            "theme": identity.title,
            "idea": identity.idea,
            "thinking": "human_first_then_niche_then_export",
            "reality_benchmark": REALITY_BENCHMARK_STATUS,
            "html_export_allowed": identity.html_export_allowed,
            "brand_story": identity.brand_story,
            "core_emotion": identity.core_emotion,
            "core_promise": identity.core_promise,
            "visual_metaphor": identity.visual_metaphor,
            "creative_conflict": identity.conflict,
            "studio_approach": approach_id,
            "first_screen_job": direction.why_hero_exists,
            "scene_sequence": direction.scene_sequence,
            "owner_review": "PENDING_OWNER",
            "question": "Who is the human — and what idea can you feel?",
        }
        (product_dir / "concept_sketch.json").write_text(
            json.dumps(sketch, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if direction.observatory is not None:
            refs = {
                "stage": "reference_gallery",
                "source": "design_observatory",
                "niche": direction.niche_id,
                "study_sources": list(direction.observatory.study_sources),
                "rule": "Analyze principles — invent original — never copy pixels",
            }
            (product_dir / "reference_gallery.json").write_text(
                json.dumps(refs, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    except OSError:
        pass


# keep alias used by older imports / store surface
def finalize_store_concept(product_dir: Path | None, direction: StudioDirection) -> None:
    _finalize_concept_artifacts(product_dir, direction, surface="store")


def _write_direction(product_dir: Path | None, direction: StudioDirection) -> None:
    if product_dir is None:
        return
    try:
        (product_dir / "studio_direction.json").write_text(
            json.dumps(direction.as_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if direction.moodboard is not None:
            (product_dir / "moodboard.json").write_text(
                json.dumps(direction.moodboard.as_dict(), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
    except OSError:
        pass
