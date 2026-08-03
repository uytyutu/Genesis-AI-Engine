"""CTA Composer — niche journey CTAs; avoid weak generic labels when niche known."""

from __future__ import annotations

from dataclasses import replace

from app.factory.analyzer import AnalysisResult
from app.factory.composers.context import QuestionnaireContext
from app.factory.hero_integrity import niche_default_cta, resolve_delivery_cta

_WEAK = frozenset(
    {
        "kontakt aufnehmen",
        "contact us",
        "mehr erfahren",
        "learn more",
        "click here",
    }
)


def compose_cta(analysis: AnalysisResult, ctx: QuestionnaireContext) -> AnalysisResult:
    current = (analysis.cta_label or "").strip()
    if current.lower() in _WEAK or not current:
        cta = niche_default_cta(ctx.niche or analysis.niche)
    else:
        cta = resolve_delivery_cta(
            niche=ctx.niche or analysis.niche,
            analysis_cta=current,
        )
    return replace(analysis, cta_label=cta)
