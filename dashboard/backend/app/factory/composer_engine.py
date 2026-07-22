"""R3 — Composer Engine: one facade over Path A composition bricks.

Does not invent new site features. Orchestrates existing modules:

  Layout Profile Resolver
  → Hero Composer
  → Component Composer
  → Trust Composer
  → Media Intelligence
  → Localization (market design / i18n chrome)
  → Page Composition (landing_builder)

Factory and ZIP Builder talk to this engine — not to each brick.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
from app.factory.market_design import resolve_market_design
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
        }

    def gate_meta(self) -> dict[str, Any]:
        return {
            "market_code": self.market_code,
            "hero_layout": self.hero_layout,
            "component_profile": self.component_profile,
            "layout_profile": self.layout_profile.id,
            "package_delivery": {"package_id": self.package_id},
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
) -> CompositionPlan:
    """Client × Package × Market × Niche → deterministic composition plan."""
    market = resolve_market_design(market_code).market_id
    layout = resolve_layout_profile(
        business_name=business_name,
        package_id=package_id,
        market_code=market,
        niche_id=niche_id,
    )
    hero = resolve_hero_for_layout(
        layout,
        niche_id=niche_id,
        business_name=business_name,
        package_id=package_id,
    )
    component = resolve_component_for_layout(
        layout,
        hero_layout=hero,
        business_name=business_name,
        package_id=package_id,
        niche_id=niche_id,
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

    return finalize_product_media(
        product_dir,
        niche_id=niche_id,
        market_code=market_code,
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
) -> CompositionResult:
    """Full Path A compose: Content Gate → Media → Page Composition via plan."""
    from app.factory.content_gate import run_content_gate

    # R3.3 — sanitize niche copy before any HTML (swap defaults, no LLM)
    _, analysis = run_content_gate(
        analysis=analysis,
        market_code=market_code,
        auto_repair=True,
    )
    assert analysis is not None

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
            market_code=market_code,
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
        market_code=market_code,
        niche_id=analysis.niche,
        commitments=analysis.trust_points,
        portfolio_paths=gallery,
        client_trust=client_trust,
        has_maps=bool(features.maps),
        has_process=bool(features.process),
    )

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
        motion_level=motion_level,
        market_code=plan.market_code,
        catalog=catalog,
        hero_pack_manifest=hero_pack_manifest,
        client_logo=client_logo,
        client_logo_src=client_logo_src,
        client_gallery=gallery,
        hero_photo=hero_ok,
        brand_style=brand_style,
        client_trust=client_trust,
        media_css=media_css,
        media_background=media_background,
    )

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
    )
