"""Layout Composer — scenario layout bias into layout pool preference."""

from __future__ import annotations

from app.factory.composers.context import QuestionnaireContext
from app.factory.industry_scenarios import resolve_scenario
from app.factory.layout_variants import NICHE_LAYOUT_POOL, get_layout_profile, resolve_layout_profile


def preferred_layout_ids(ctx: QuestionnaireContext) -> tuple[str, ...]:
    sc = resolve_scenario(ctx.niche)
    if sc and sc.layout_bias:
        return sc.layout_bias
    return NICHE_LAYOUT_POOL.get(ctx.niche) or NICHE_LAYOUT_POOL["generic"]


def compose_layout_profile(ctx: QuestionnaireContext):
    """Deterministic layout using scenario bias when available."""
    sc = resolve_scenario(ctx.niche)
    if sc and sc.layout_bias:
        # Prefer first scenario layout for strong niche personality.
        return get_layout_profile(sc.layout_bias[0])
    return resolve_layout_profile(
        business_name=ctx.business_name,
        package_id=ctx.package_id,
        market_code=ctx.market_code,
        niche_id=ctx.niche,
    )
