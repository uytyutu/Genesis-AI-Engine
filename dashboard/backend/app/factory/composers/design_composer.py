"""Design Composer — niche personality tokens (not Virtus Core aurora)."""

from __future__ import annotations

from app.factory.composers.context import QuestionnaireContext
from app.factory.industry_scenarios import resolve_scenario
from app.factory.niche_profiles import resolve_niche_profile


def compose_design_meta(ctx: QuestionnaireContext) -> dict:
    """Return design personality hints for meta / CSS — niche identity only."""
    profile = resolve_niche_profile(ctx.niche)
    scenario = resolve_scenario(ctx.niche)
    style = profile.style if profile else None
    return {
        "composer": "design",
        "niche": ctx.niche,
        "emotional_tone": scenario.emotional_tone if scenario else "neutral",
        "journey": scenario.journey if scenario else "service",
        "primary": getattr(style, "primary", None),
        "font_display": getattr(style, "font_display", None),
        "radius": getattr(style, "radius", None),
        "btn_radius": getattr(style, "btn_radius", None),
        # Explicit: client sites must not use Virtus Core storefront aurora.
        "forbid_platform_aurora": True,
    }
