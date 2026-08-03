"""Trust Composer — keep niche trust; add city only when known."""

from __future__ import annotations

from dataclasses import replace

from app.factory.analyzer import AnalysisResult
from app.factory.composers.context import QuestionnaireContext


def compose_trust(analysis: AnalysisResult, ctx: QuestionnaireContext) -> AnalysisResult:
    trust = list(analysis.trust_points or ())
    if ctx.city and trust and not any(ctx.city.lower() in t.lower() for t in trust):
        trust = [ctx.city, *trust][:3]
    return replace(analysis, trust_points=tuple(trust[:3]))
