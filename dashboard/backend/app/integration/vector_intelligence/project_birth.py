"""Natural project birth — project emerges from conversation, not from mode switch."""

from __future__ import annotations

from app.integration.vector_intelligence.pipeline import VectorTurnAnalysis


def project_birth_hint(analysis: VectorTurnAnalysis) -> str | None:
    """LLM hint when Vector should offer saving discussion as a project."""
    if not analysis.project_birth_ready or analysis.action != "suggest_save_project":
        return None
    return (
        "Мы уже достаточно обсудили идею. "
        "Предложите сохранить всё как проект — одним естественным предложением в конце ответа. "
        "Формулировка в духе: «Предлагаю сохранить это как проект, чтобы ничего не потерялось — согласны?» "
        "Не создавайте проект автоматически и не переключайте интерфейс."
    )
