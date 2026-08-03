"""Copy Composer — about / benefits from questionnaire; neutral if thin data."""

from __future__ import annotations

from dataclasses import replace

from app.factory.analyzer import AnalysisResult
from app.factory.composers.context import QuestionnaireContext


def compose_copy(analysis: AnalysisResult, ctx: QuestionnaireContext) -> AnalysisResult:
    name = ctx.business_name or analysis.business_name
    services = list(analysis.services or [])
    about = (analysis.about_text or "").strip()
    # Do not invent biography — keep niche about, inject city/services only from data.
    if ctx.city and name and name not in about:
        about = (
            f"{name} in {ctx.city}"
            + (f" — Fokus: {', '.join(services[:3])}." if services else ".")
        )
    elif services and name:
        about = f"{name} — {', '.join(services[:3])}. Erreichbar für Anfragen und Termine."
    elif not about:
        about = f"{name} — klare Leistungen und schnelle Rückmeldung."

    benefits = list(analysis.benefits or ())
    if len(ctx.advantages) >= 2:
        benefits = list(ctx.advantages[:4])
    elif ctx.city and benefits:
        # Soft localization without inventing USPs
        benefits = list(benefits)
        if not any(ctx.city.lower() in b.lower() for b in benefits):
            benefits[0] = f"Vor Ort in {ctx.city}" if benefits else f"Lokal in {ctx.city}"

    return replace(analysis, about_text=about[:400], benefits=tuple(benefits[:4]))
