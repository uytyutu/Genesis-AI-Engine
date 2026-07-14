"""Re-export — use industry_intelligence (Professional Decision Backlog)."""

from app.integration.vector_intelligence.industry_intelligence import (
    IndustryProfession,
    build_decision_leadership_response,
    build_profession_surprise,
    list_professions,
    match_industry_profession,
    match_profession_insight,
    profession_style_followup,
)

__all__ = [
    "IndustryProfession",
    "build_decision_leadership_response",
    "build_profession_surprise",
    "list_professions",
    "match_industry_profession",
    "match_profession_insight",
    "profession_style_followup",
]
