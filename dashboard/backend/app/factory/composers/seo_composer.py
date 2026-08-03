"""SEO Composer — title/description from questionnaire facts only."""

from __future__ import annotations

from app.factory.analyzer import AnalysisResult
from app.factory.composers.context import QuestionnaireContext


def compose_seo(analysis: AnalysisResult, ctx: QuestionnaireContext) -> dict[str, str]:
    name = ctx.business_name or analysis.business_name
    city = ctx.city
    service = (analysis.services or ctx.services or ("Leistungen",))[0]
    title = f"{name} — {service}" + (f" | {city}" if city else "")
    desc = (analysis.subtitle or analysis.about_text or title)[:160]
    return {"composer": "seo", "title": title[:70], "description": desc}
