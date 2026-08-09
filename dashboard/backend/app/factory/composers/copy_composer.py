"""Copy Composer — about / benefits from questionnaire; neutral if thin data."""

from __future__ import annotations

from dataclasses import replace

from app.factory.analyzer import AnalysisResult
from app.factory.composers.context import QuestionnaireContext


def compose_copy(analysis: AnalysisResult, ctx: QuestionnaireContext) -> AnalysisResult:
    name = ctx.business_name or analysis.business_name
    services = list(analysis.services or [])
    about = (analysis.about_text or "").strip()
    # Keep niche/preset about when it already has substance — never replace with a stub.
    thin = len(about) < 60 or "Erreichbar für Anfragen" in about
    if thin:
        if ctx.city and name:
            focus = f" — Fokus: {', '.join(services[:3])}." if services else "."
            about = f"{name} in {ctx.city}{focus}"
            if analysis.about_text and len((analysis.about_text or "").strip()) >= 40:
                # Prefer richer preset + soft city anchor
                base = (analysis.about_text or "").strip()
                if ctx.city and ctx.city not in base:
                    about = f"{base} Standort: {ctx.city}."
                else:
                    about = base
        elif about:
            pass
        elif services and name:
            about = (
                f"{name} begleitet Sie mit {', '.join(services[:3])} — "
                "klar im Ablauf, erreichbar und auf Ihre Situation abgestimmt."
            )
        else:
            about = f"{name} — klare Leistungen und schnelle Rückmeldung."

    benefits = list(analysis.benefits or ())
    if len(ctx.advantages) >= 2:
        benefits = list(ctx.advantages[:4])
    elif ctx.city and benefits:
        # Soft localization without inventing USPs
        benefits = list(benefits)
        if not any(ctx.city.lower() in b.lower() for b in benefits):
            benefits[0] = f"Vor Ort in {ctx.city}" if benefits else f"Lokal in {ctx.city}"

    return replace(analysis, about_text=about[:520], benefits=tuple(benefits[:4]))
