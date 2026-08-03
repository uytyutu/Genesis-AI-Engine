"""Factory composers — modular Path A pipeline (architecture lock).

One lifetime client project; package upgrades unlock features — they do not
spawn a second Factory product identity.

All composers read QuestionnaireContext only (questionnaire + niche + language
+ country + package + platform settings). Inventing company facts is forbidden;
prefer neutral copy when data is missing.

Commercial Rule №1: Hard Gate FAIL beats a high AI Score — the site must be
fit to show a first visitor.
"""

from __future__ import annotations

from typing import Any

from app.factory.analyzer import AnalysisResult
from app.factory.composers.context import QuestionnaireContext, context_from_contacts
from app.factory.composers.brand_composer import compose_brand
from app.factory.composers.copy_composer import compose_copy
from app.factory.composers.cta_composer import compose_cta
from app.factory.composers.hero_composer_mod import compose_hero
from app.factory.composers.services_composer import compose_services
from app.factory.composers.trust_composer import compose_trust
from app.factory.composers.design_composer import compose_design_meta
from app.factory.composers.seo_composer import compose_seo
from app.factory.composers.layout_composer import compose_layout_profile, preferred_layout_ids
from app.factory.composers.quality import (
    CommercialGateResult,
    MAX_REBUILD_ATTEMPTS,
    run_commercial_gate,
)

COMPOSER_IDS = (
    "brand",
    "hero",
    "copy",
    "services",
    "trust",
    "cta",
    "design",
    "seo",
    "layout",
    "quality_gate",
)


def run_composers(
    analysis: AnalysisResult,
    *,
    contacts: dict[str, Any] | None = None,
    package_id: str | None = None,
    html: str | None = None,
    scenario_id: str | None = None,
) -> tuple[AnalysisResult, CommercialGateResult]:
    """Apply modular composers then Hard Gate + AI Score."""
    ctx = context_from_contacts(
        contacts or {},
        package_id=package_id,
        niche=analysis.niche,
        business_name=analysis.business_name,
    )
    working = analysis
    working = compose_brand(working, ctx)
    working = compose_services(working, ctx)
    working = compose_hero(working, ctx)
    working = compose_copy(working, ctx)
    working = compose_trust(working, ctx)
    working = compose_cta(working, ctx)
    design_meta = compose_design_meta(ctx)
    seo_meta = compose_seo(working, ctx)
    layout_profile = compose_layout_profile(ctx)
    gate = run_commercial_gate(
        analysis=working,
        ctx=ctx,
        html=html,
        scenario_id=scenario_id or working.niche,
    )
    gate.extras = {
        "design": design_meta,
        "seo": seo_meta,
        "layout_id": getattr(layout_profile, "id", None),
        "layout_pool": list(preferred_layout_ids(ctx)),
        "max_rebuild_attempts": MAX_REBUILD_ATTEMPTS,
        "one_lifetime_project": True,
    }
    return working, gate


__all__ = [
    "COMPOSER_IDS",
    "QuestionnaireContext",
    "CommercialGateResult",
    "context_from_contacts",
    "run_composers",
    "run_commercial_gate",
]
