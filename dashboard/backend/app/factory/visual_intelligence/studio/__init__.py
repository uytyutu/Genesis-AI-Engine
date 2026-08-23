"""Digital Creative Studio — board of directors under AI Creative Director.

Decisions must change HTML/CSS/assets, not only meta.
Business outcome directors: Conversion, Trust, Performance, Accessibility, Localization.
Master KPI: Commercial Readiness Score ≥ 90 → Commercial Ready.
"""

from __future__ import annotations

from app.factory.visual_intelligence.studio.board import (
    STUDIO_ENGINE_ID,
    StudioPlan,
    convene_board,
)
from app.factory.visual_intelligence.studio.apply_html import apply_studio_to_html
from app.factory.visual_intelligence.studio.experience_replay import (
    build_experience_replay,
    write_experience_replay,
)
from app.factory.visual_intelligence.studio.ceo_blind_test import run_ceo_blind_test
from app.factory.visual_intelligence.studio.commercial_readiness import (
    COMMERCIAL_READY_THRESHOLD,
    score_commercial_readiness,
)

__all__ = [
    "COMMERCIAL_READY_THRESHOLD",
    "STUDIO_ENGINE_ID",
    "StudioPlan",
    "apply_studio_to_html",
    "build_experience_replay",
    "convene_board",
    "run_ceo_blind_test",
    "score_commercial_readiness",
    "write_experience_replay",
]
