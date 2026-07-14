"""
Genesis Reasoning Layer — Journey phase + recommendation strategy from intent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.integration.genesis_brain.layers.intent import GenesisIntentLayer, IntentBrief
from app.integration.vector_intelligence.types import JOURNEY_PHASE_LABELS


@dataclass(frozen=True)
class ReasoningBrief:
    topic: str
    journey_phase: str
    should_recommend: bool
    confidence: str  # low | medium | high
    intent: IntentBrief | None = None

    def to_prompt_hint(self) -> str:
        phase = JOURNEY_PHASE_LABELS.get(self.journey_phase, self.journey_phase)
        parts = [
            f"Тема: {self.topic}. Этап Journey: {phase}. "
            f"Сначала движение к результату, потом максимум один вопрос. "
            f"Уверенность: {self.confidence}."
        ]
        if self.intent:
            parts.append(self.intent.to_prompt_hint())
        return " ".join(parts)


class GenesisReasoningLayer:
    """Pre-response analysis — not shown to user."""

    def __init__(self) -> None:
        self._intent = GenesisIntentLayer()

    def analyze(
        self,
        messages: list[dict[str, str]],
        memory: dict[str, Any] | None = None,
    ) -> ReasoningBrief:
        intent = self._intent.analyze(messages, memory)
        should_rec = intent.journey_phase != "open_dialog"
        return ReasoningBrief(
            topic=intent.intent,
            journey_phase=intent.journey_phase,
            should_recommend=should_rec,
            confidence=intent.confidence,
            intent=intent,
        )
