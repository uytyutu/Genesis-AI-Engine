"""Brand Composer — business identity from questionnaire (no invented brand story)."""

from __future__ import annotations

from dataclasses import replace

from app.factory.analyzer import AnalysisResult
from app.factory.composers.context import QuestionnaireContext


def compose_brand(analysis: AnalysisResult, ctx: QuestionnaireContext) -> AnalysisResult:
    name = ctx.business_name or analysis.business_name
    # Hours / contact stay from analyzer unless order overwrote via apply_order_contacts.
    return replace(analysis, business_name=name)
