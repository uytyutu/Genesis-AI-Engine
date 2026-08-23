"""R3 — Composer Engine: one facade over Path A composition bricks.

Does not invent new site features. Orchestrates existing modules:

  Layout Profile Resolver
  → Hero Composer
  → Component Composer
  → Trust Composer
  → Media Intelligence
  → Localization (via Market Profile SSOT)
  → Page Composition (landing_builder)

Factory and ZIP Builder talk to this engine — not to each brick.

R3.4.1.2: market language / currency / CTA / locale come from
resolve(market_code) → MarketProfile — not from Composer-local if/else.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from app.factory.analyzer import AnalysisResult
from app.factory.catalog_manager import CatalogView
from app.factory.landing_builder import build_landing_html
from app.factory.layout_variants import (
    LayoutProfile,
    profile_as_dict,
    resolve_component_for_layout,
    resolve_hero_for_layout,
    resolve_layout_profile,
)
from app.factory.market_profile import MarketProfile, resolve as resolve_market_profile
from app.factory.package_features import PackageFeatures
from app.factory.trust_composer import (
    collect_trust_evidence,
    select_trust_template,
)

ENGINE_ID = "composer_v1"


@dataclass(frozen=True)
class CompositionPlan:
    """Resolved composition decisions — bricks to call, not HTML yet."""

    engine_id: str
    layout_profile: LayoutProfile
    hero_layout: str
    component_profile: str
    trust_template: str
    market_code: str
    niche_id: str
    package_id: str
    business_name: str
    # R3.4.1.2 — market chrome from Market Profile (SSOT)
    language: str = ""
    currency: str = ""
    locale: str = ""
    default_cta: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "layout_profile": profile_as_dict(self.layout_profile),
            "hero_layout": self.hero_layout,
            "component_profile": self.component_profile,
            "trust_template": self.trust_template,
            "market_code": self.market_code,
            "niche_id": self.niche_id,
            "package_id": self.package_id,
            "business_name": self.business_name,
            "language": self.language,
            "currency": self.currency,
            "locale": self.locale,
            "default_cta": self.default_cta,
        }

    def gate_meta(self) -> dict[str, Any]:
        return {
            "market_code": self.market_code,
            "hero_layout": self.hero_layout,
            "component_profile": self.component_profile,
            "layout_profile": self.layout_profile.id,
            "package_delivery": {"package_id": self.package_id},
            "language": self.language,
            "currency": self.currency,
            "locale": self.locale,
        }


@dataclass
class CompositionResult:
    html: str
    plan: CompositionPlan
    media_plan: dict[str, Any] = field(default_factory=dict)
    media_css: str = ""
    media_background: bool = False
    gallery: list[str] = field(default_factory=list)
    hero_ok: bool = True
    hero_from_client: bool = False
    content_gate: dict[str, Any] = field(default_factory=dict)
    analysis: AnalysisResult | None = None
    market_profile: dict[str, Any] = field(default_factory=dict)
    design_dna: dict[str, Any] = field(default_factory=dict)


def _profile_chrome(profile: MarketProfile) -> dict[str, str]:
    return {
        "language": profile.language,
        "currency": profile.currency,
        "locale": profile.locale,
        "default_cta": profile.default_cta,
    }


def resolve_composition_plan(
    *,
    business_name: str,
    package_id: str,
    market_code: str,
    niche_id: str,
    commitments: tuple[str, ...] | list[str] = (),
    portfolio_paths: list[str] | None = None,
    client_trust: dict | None = None,
    has_maps: bool = False,
    has_process: bool = False,
    diversity_salt: str = "",
) -> CompositionPlan:
    """Client × Package × Market × Niche → deterministic composition plan."""
    profile = resolve_market_profile(market_code)
    market = profile.market_code
    chrome = _profile_chrome(profile)
    layout = resolve_layout_profile(
        business_name=business_name,
        package_id=package_id,
        market_code=market,
        niche_id=niche_id,
        diversity_salt=diversity_salt,
    )
    hero = resolve_hero_for_layout(
        layout,
        niche_id=niche_id,
        business_name=business_name,
        package_id=package_id,
        diversity_salt=diversity_salt,
    )
    component = resolve_component_for_layout(
        layout,
        hero_layout=hero,
        business_name=business_name,
        package_id=package_id,
        niche_id=niche_id,
        diversity_salt=diversity_salt,
    )
    evidence = collect_trust_evidence(
        client_trust=client_trust,
        commitments=commitments,
        portfolio_paths=portfolio_paths or [],
        has_maps=has_maps,
        has_process=has_process,
    )
    trust = select_trust_template(
        niche_id=niche_id,
        market_code=market,
        business_name=business_name,
        package_id=package_id,
        evidence=evidence,
    )
    return CompositionPlan(
        engine_id=ENGINE_ID,
        layout_profile=layout,
        hero_layout=hero,
        component_profile=component,
        trust_template=trust,
        market_code=market,
        niche_id=niche_id,
        package_id=package_id,
        business_name=business_name,
        language=chrome["language"],
        currency=chrome["currency"],
        locale=chrome["locale"],
        default_cta=chrome["default_cta"],
    )


def prepare_media(
    product_dir: Path,
    *,
    niche_id: str,
    market_code: str,
    package_id: str,
    business_name: str,
    hero_from_client: bool = False,
    gallery_rels: list[str] | None = None,
) -> Any:
    """Media Intelligence brick — returns MediaPlan."""
    from app.factory.media_intelligence import finalize_product_media

    market = resolve_market_profile(market_code).market_code
    return finalize_product_media(
        product_dir,
        niche_id=niche_id,
        market_code=market,
        package_id=package_id,
        business_name=business_name,
        hero_from_client=hero_from_client,
        gallery_rels=gallery_rels,
    )


def compose_landing(
    analysis: AnalysisResult,
    *,
    features: PackageFeatures,
    market_code: str,
    whatsapp: str = "",
    city: str = "",
    street: str = "",
    motion_level: str | None = None,
    catalog: CatalogView | None = None,
    hero_pack_manifest: dict | None = None,
    client_logo: bool = False,
    client_logo_src: str = "assets/logo.png",
    client_gallery: list[str] | None = None,
    brand_style: str | None = None,
    client_trust: dict | None = None,
    product_dir: Path | None = None,
    hero_from_client: bool = False,
    modern: bool = False,
    blue_boost: bool = False,
    calculator: bool = False,
    include_testimonials: bool = False,
    large_headline: bool = False,
    diversity_salt: str = "",
    studio_plan: object | None = None,
    approach: str = "",
    contacts: dict | None = None,
) -> CompositionResult:
    """Full Path A compose: Content Gate → Media → Page Composition via plan."""
    from app.factory.content_gate import run_content_gate

    # R3.4.1.2 — Market Profile SSOT (language / currency / CTA / locale)
    profile = resolve_market_profile(market_code)
    market = profile.market_code

    # R3.3 — sanitize niche copy before any HTML (swap defaults, no LLM)
    _, analysis = run_content_gate(
        analysis=analysis,
        market_code=market,
        auto_repair=True,
    )
    assert analysis is not None

    # Niche CTA wins; market profile default_cta is chrome fallback only.
    from app.factory.hero_integrity import ensure_analysis_hero, resolve_delivery_cta

    analysis = ensure_analysis_hero(analysis)
    analysis = replace(
        analysis,
        cta_label=resolve_delivery_cta(
            niche=analysis.niche,
            analysis_cta=analysis.cta_label,
            market_default_cta=profile.default_cta,
        ),
    )

    gallery = list(client_gallery or [])
    media_plan_obj = None
    media_css = ""
    media_background = False
    hero_ok = True
    hero_client = bool(hero_from_client)

    if product_dir is not None:
        media_plan_obj = prepare_media(
            product_dir,
            niche_id=analysis.niche,
            market_code=market,
            package_id=features.package_id,
            business_name=analysis.business_name,
            hero_from_client=hero_from_client,
            gallery_rels=gallery,
        )
        gallery = list(media_plan_obj.gallery)
        media_css = media_plan_obj.css
        media_background = bool(media_plan_obj.background_src)
        hero_ok = bool(media_plan_obj.hero_ok)
        hero_client = bool(media_plan_obj.hero_from_client)

    plan = resolve_composition_plan(
        business_name=analysis.business_name,
        package_id=features.package_id,
        market_code=market,
        niche_id=analysis.niche,
        commitments=analysis.trust_points,
        portfolio_paths=gallery,
        client_trust=client_trust,
        has_maps=bool(features.maps),
        has_process=bool(features.process),
        diversity_salt=diversity_salt,
    )

    # Digital Creative Studio — design the brand BEFORE any marketing HTML
    from app.factory.design_dna.art_director import run_digital_creative_studio
    from app.factory.design_dna.concept_gate import (
        REALITY_BENCHMARK_NOTE,
        gate_report,
        should_export_marketing_html,
    )
    from app.factory.design_dna.quality_floor import validate_quality_floor_html
    from app.factory.design_dna.visual_benchmark import quality_floor_for

    studio = run_digital_creative_studio(
        business_name=analysis.business_name,
        niche_id=analysis.niche,
        package_id=features.package_id,
        diversity_salt=diversity_salt,
        product_dir=Path(product_dir) if product_dir is not None else None,
        surface="site",
    )
    dna = studio.dna
    if product_dir is not None and studio.generation_status == "FAIL_TEMPLATE":
        try:
            import json as _json

            (Path(product_dir) / "design_dna_gate.json").write_text(
                _json.dumps(
                    {
                        "generation_status": "FAIL_TEMPLATE",
                        "action": "REBUILD",
                        "reason": studio.note,
                        "philosophy": studio.philosophy,
                        "quality_floor": quality_floor_for(features.package_id),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass

    # Reality Benchmark FAIL: freeze marketing HTML — Creative Identity Owner Preview
    if product_dir is not None and not should_export_marketing_html(
        studio_generation_status=studio.generation_status
    ):
        from app.factory.design_dna.creative_identity import (
            invent_creative_identity,
            write_creative_identity,
            write_identity_preview_as_index,
        )

        identity = studio.creative_identity or invent_creative_identity(
            business_name=analysis.business_name,
            niche_id=analysis.niche,
            package_id=features.package_id,
            surface="site",
            diversity_salt=diversity_salt,
            allow_html_export=False,
            html_blocked_reason=REALITY_BENCHMARK_NOTE,
        )
        write_creative_identity(Path(product_dir), identity)
        html = write_identity_preview_as_index(Path(product_dir), identity).read_text(
            encoding="utf-8"
        )
        try:
            import json as _json

            (Path(product_dir) / "html_export_gate.json").write_text(
                _json.dumps(gate_report(html_allowed=False), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass
        return CompositionResult(
            html=html,
            plan=plan,
            media_plan=media_plan_obj.as_dict() if media_plan_obj else {},
            media_css=media_css,
            media_background=media_background,
            gallery=gallery,
            hero_ok=hero_ok,
            hero_from_client=hero_client,
            content_gate={"status": "CREATIVE_IDENTITY_ONLY", "note": REALITY_BENCHMARK_NOTE},
            analysis=analysis,
            market_profile=profile.as_dict(),
            design_dna=dna.as_dict() if dna is not None else {},
        )

    if dna is None:
        from app.factory.design_dna import resolve_design_dna
        from app.factory.design_dna.rhythm import DEFAULT_SECTION_KEYS

        dna = resolve_design_dna(
            business_name=analysis.business_name,
            niche_id=analysis.niche,
            package_id=features.package_id,
            section_keys=DEFAULT_SECTION_KEYS,
            diversity_salt=diversity_salt,
        )

    # Apply chosen composition: layout order + hero (impression over structure)
    if studio.layout_profile is not None:
        new_comp = resolve_component_for_layout(
            studio.layout_profile,
            hero_layout=studio.hero_layout or dna.hero_layout,
            business_name=analysis.business_name,
            package_id=features.package_id,
            niche_id=analysis.niche,
            diversity_salt=diversity_salt,
        )
        plan = replace(
            plan,
            layout_profile=studio.layout_profile,
            hero_layout=studio.hero_layout or dna.hero_layout,
            component_profile=new_comp,
        )
    elif dna.hero_layout and dna.hero_layout != plan.hero_layout:
        new_comp = resolve_component_for_layout(
            plan.layout_profile,
            hero_layout=dna.hero_layout,
            business_name=analysis.business_name,
            package_id=features.package_id,
            niche_id=analysis.niche,
            diversity_salt=diversity_salt,
        )
        plan = replace(plan, hero_layout=dna.hero_layout, component_profile=new_comp)

    if product_dir is not None:
        try:
            import json as _json

            (Path(product_dir) / "visual_benchmark.json").write_text(
                _json.dumps(
                    {
                        "quality_floor": quality_floor_for(features.package_id),
                        "optimize_for": "first_visual_effect",
                        "benchmark_brief": studio.benchmark_brief,
                        "studio_id": studio.studio_id,
                        "owner_review": studio.owner_review,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass

    # Starter also gets soft motion — unfinished static pages fail the shame test
    effective_motion = motion_level
    if features.package_id == "basic" and dna.motion == "soft":
        effective_motion = "css"

    html = build_landing_html(
        analysis,
        features=features,
        whatsapp=whatsapp,
        city=city,
        street=street,
        modern=modern,
        blue_boost=blue_boost,
        calculator=calculator,
        include_testimonials=include_testimonials,
        large_headline=large_headline,
        motion_level=effective_motion,
        market_code=plan.market_code,
        market_profile=profile,
        catalog=catalog,
        hero_pack_manifest=hero_pack_manifest,
        client_logo=client_logo,
        client_logo_src=client_logo_src,
        client_gallery=gallery,
        hero_photo=hero_ok,
        hero_video=(
            "assets/hero.mp4"
            if product_dir is not None
            and (Path(product_dir) / "assets" / "hero.mp4").is_file()
            else ""
        ),
        brand_style=brand_style,
        client_trust=client_trust,
        media_css=media_css,
        media_background=media_background,
        composition_plan=plan,
        studio_plan=studio_plan,
        design_dna=dna,
        product_dir=Path(product_dir) if product_dir is not None else None,
        approach=approach,
        contacts=contacts,
    )

    floor_fails = validate_quality_floor_html(html, dna)
    if floor_fails and product_dir is not None:
        try:
            (product_dir / "design_dna_gate.json").write_text(
                __import__("json").dumps(
                    {"failures": floor_fails, "dna": dna.as_dict()},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass

    cg_result, _ = run_content_gate(
        analysis=analysis,
        html=html,
        market_code=plan.market_code,
        auto_repair=False,
    )

    return CompositionResult(
        html=html,
        plan=plan,
        media_plan=media_plan_obj.as_dict() if media_plan_obj else {},
        media_css=media_css,
        media_background=media_background,
        gallery=gallery,
        hero_ok=hero_ok,
        hero_from_client=hero_client,
        content_gate=cg_result.as_dict(),
        analysis=analysis,
        market_profile=profile.as_dict(),
        design_dna=dna.as_dict(),
    )
