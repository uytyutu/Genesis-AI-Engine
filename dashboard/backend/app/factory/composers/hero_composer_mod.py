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


def _headline_has_commercial_signal(
    headline: str, *, niche: str, services: list[str]
) -> bool:
    """Same cues as Commercial Hard Gate hero_matches_niche (strict)."""
    hl = (headline or "").strip()
    if not hl:
        return False
    n = (niche or "generic").strip().lower() or "generic"
    if n == "generic":
        return True
    low = hl.lower()
    if n.replace("_", " ") in low:
        return True
    if any(s.lower() in low for s in services[:2] if s):
        return True
    return " — " in hl


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
    elif name and not _headline_has_commercial_signal(
        headline, niche=str(analysis.niche or ""), services=services
    ):
        # First Impression emotion lines must still carry a commercial cue.
        headline = f"{name} — {headline}"

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
