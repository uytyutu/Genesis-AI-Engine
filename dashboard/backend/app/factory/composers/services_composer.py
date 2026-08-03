"""Services Composer — questionnaire services win; no invented offerings."""

from __future__ import annotations

from dataclasses import replace

from app.factory.analyzer import AnalysisResult
from app.factory.composers.context import QuestionnaireContext, merge_services


def compose_services(analysis: AnalysisResult, ctx: QuestionnaireContext) -> AnalysisResult:
    services = merge_services(analysis.services or [], ctx.services)
    if not services:
        return analysis
    prev = list(analysis.service_descriptions or ())
    descs: list[str] = []
    for i, title in enumerate(services):
        if i < len(prev) and str(prev[i]).strip():
            descs.append(str(prev[i]).strip())
        elif ctx.city:
            descs.append(f"{title} — in {ctx.city} und Umgebung.")
        else:
            descs.append(f"{title} — Details auf Anfrage.")
    return replace(
        analysis,
        services=services,
        service_descriptions=tuple(descs),
    )
