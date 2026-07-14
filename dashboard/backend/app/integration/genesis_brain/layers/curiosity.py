"""
Curiosity — уточнение только для проекта, когда этап Journey требует факта.

Не задаёт вопросы «ради интересного разговора». Только пробелы, без которых нельзя двигаться.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.integration.genesis_brain.layers.emotional_intelligence import EmotionalBrief, Mood
from app.integration.vector_intelligence.types import JOURNEY_PHASE_LABELS, JourneyPhase

_JOURNEY_CLARIFY_PHASES = frozenset(
    {
        "understand_goal",
        "requirements",
        "materials",
    }
)

_GAP_QUESTIONS: dict[str, str] = {
    "country": "В какой стране планируете работу над проектом?",
    "budget": "Какой бюджет заложен на этот этап?",
    "niche": "Какой формат результата ближе — офлайн-точка или онлайн?",
}


@dataclass(frozen=True)
class CuriosityHint:
    append: str | None = None


class CuriosityLayer:
    """One optional clarification — only when Journey phase needs a missing project fact."""

    _SKIP_MOODS = frozenset({Mood.HEAVY, Mood.ANGRY, Mood.TIRED, Mood.GRATEFUL, Mood.MISINFORMED})

    def suggest(
        self,
        *,
        user_message: str,
        emotional: EmotionalBrief,
        turn_index: int,
        visitor_id: str,
        has_business_topic: bool,
        conversation_type: str = "general_question",
        journey_phase: JourneyPhase = "open_dialog",
        missing_facts: tuple[str, ...] = (),
    ) -> CuriosityHint:
        _ = user_message, visitor_id, turn_index, has_business_topic, conversation_type

        if journey_phase not in _JOURNEY_CLARIFY_PHASES:
            return CuriosityHint()

        if emotional.mood in self._SKIP_MOODS:
            return CuriosityHint()

        if not missing_facts:
            return CuriosityHint()

        gap = missing_facts[0]
        if gap == "страна":
            gap = "country"
        if gap == "бюджет":
            gap = "budget"
        if gap in ("формат (офлайн/онлайн)", "формат"):
            gap = "niche"

        question = _GAP_QUESTIONS.get(gap)
        if not question:
            return CuriosityHint()

        phase = JOURNEY_PHASE_LABELS.get(journey_phase, journey_phase)
        return CuriosityHint(
            append=f"\n\n[{phase}] Нужен один факт для движения: {question}"
        )

    @staticmethod
    def has_business_topic(text: str) -> bool:
        return bool(
            re.search(
                r"сайт|кафе|салон|магазин|бот|studio|бизнес|заказ|лендинг",
                text,
                re.I,
            )
        )
