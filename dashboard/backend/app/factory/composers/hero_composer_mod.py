"""Hero Composer — niche + questionnaire; never universal partner chrome."""

from __future__ import annotations

from dataclasses import replace

from app.factory.analyzer import AnalysisResult
from app.factory.composers.context import QuestionnaireContext

_BANNED_TAILS = (
    "ihr partner vor ort",
    "partner vor ort",
    "wir helfen ihrem unternehmen",
)


def compose_hero(analysis: AnalysisResult, ctx: QuestionnaireContext) -> AnalysisResult:
    name = ctx.business_name or analysis.business_name
    services = list(analysis.services or [])
    headline = (analysis.headline or "").strip()
    hl_low = headline.lower()
    if any(b in hl_low for b in _BANNED_TAILS) or not headline:
        tail = services[0] if services else (ctx.primary_service() or "klare Leistungen")
        headline = f"{name} — {tail}"
    elif name and " — " in headline:
        _, rest = headline.split(" — ", 1)
        rest = rest.strip()
        # Avoid "Name — Name — …" when analyzer already embedded the business name.
        if rest.lower().startswith(name.lower()):
            rest = services[0] if services else (ctx.primary_service() or "klare Leistungen")
        headline = f"{name} — {rest}"

    subtitle = (analysis.subtitle or "").strip()
    if not subtitle or "helfen ihrem" in subtitle.lower():
        parts = [s for s in services[:3] if s]
        if ctx.city and parts:
            subtitle = f"{' · '.join(parts)} — {ctx.city}"
        elif parts:
            subtitle = " · ".join(parts)
        elif ctx.city:
            subtitle = f"Persönlicher Service in {ctx.city}."
        else:
            subtitle = "Klare Leistungen, erreichbare Ansprechpartner."

    return replace(analysis, business_name=name, headline=headline[:120], subtitle=subtitle[:180])
