"""Visual Intelligence Engine — Gen1 premium visual system.

One engine → many niche styles. Website Factory, AI Store, and Virtus Core
share Style / Asset / Motion / Quality Gate. Client ZIPs stay CSS-first
(no Lottie/Three); Premium platform surface may use richer motion tokens.

AI Creative Director + Design Memory + Store Director sit above craft engines
and decide the experience for niche + budget.
"""

from __future__ import annotations

from app.factory.visual_intelligence.engine import (
    VISUAL_ENGINE_ID,
    VisualPlan,
    resolve_visual_plan,
    visual_intelligence_ready,
)
from app.factory.visual_intelligence.quality_gate import (
    VISUAL_QUALITY_THRESHOLD,
    VisualQualityResult,
    assert_visual_quality,
    run_visual_quality_gate,
)
from app.factory.visual_intelligence.asset_manager import AssetManager, AssetPick
from app.factory.visual_intelligence.motion_engine import (
    MotionTier,
    emit_motion_css,
    resolve_motion_tier,
)
from app.factory.visual_intelligence.style_engine import StyleProfile, resolve_style
from app.factory.visual_intelligence.ai_design_director import (
    PREMIUM_FEELING_THRESHOLD,
    audit_design_director_gallery,
    score_html,
)
from app.factory.visual_intelligence.ai_creative_director import decide_experience
from app.factory.visual_intelligence.design_memory import (
    check_similarity,
    record_composition,
)
from app.factory.visual_intelligence.store_director import decide_store_experience
from app.factory.visual_intelligence.studio import (
    apply_studio_to_html,
    convene_board,
    run_ceo_blind_test,
    score_commercial_readiness,
)

__all__ = [
    "VISUAL_ENGINE_ID",
    "VISUAL_QUALITY_THRESHOLD",
    "PREMIUM_FEELING_THRESHOLD",
    "AssetManager",
    "AssetPick",
    "MotionTier",
    "StyleProfile",
    "VisualPlan",
    "VisualQualityResult",
    "apply_studio_to_html",
    "assert_visual_quality",
    "audit_design_director_gallery",
    "check_similarity",
    "convene_board",
    "decide_experience",
    "decide_store_experience",
    "emit_motion_css",
    "record_composition",
    "resolve_motion_tier",
    "resolve_style",
    "resolve_visual_plan",
    "run_ceo_blind_test",
    "run_visual_quality_gate",
    "score_commercial_readiness",
    "score_html",
    "visual_intelligence_ready",
]
