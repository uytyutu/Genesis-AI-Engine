"""
Genesis Reasoning Layer — role + recommendation strategy from intent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.integration.genesis_brain.layers.intent import GenesisIntentLayer, IntentBrief


@dataclass(frozen=True)
class ReasoningBrief:
    topic: str
    suggested_role: str
    should_recommend: bool
    confidence: str  # low | medium | high
    intent: IntentBrief | None = None

    def to_prompt_hint(self) -> str:
        parts = [
            f"Тема: {self.topic}. Роль: {self.suggested_role}. "
            f"Сначала помощь и рекомендация, потом максимум один вопрос. "
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
        should_rec = intent.intent not in ("greeting", "small_talk", "humor")
        return ReasoningBrief(
            topic=intent.intent,
            suggested_role=intent.role,
            should_recommend=should_rec,
            confidence=intent.confidence,
            intent=intent,
        )
