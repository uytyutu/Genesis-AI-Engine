"""
Emotional Intelligence Layer — mood-aware responses before business logic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Mood(str, Enum):
    NEUTRAL = "neutral"
    JOY = "joy"
    PROMOTION = "promotion"
    TIRED = "tired"
    HEAVY = "heavy"
    ANGRY = "angry"
    GRATEFUL = "grateful"
    CURIOUS = "curious"
    MISINFORMED = "misinformed"


@dataclass(frozen=True)
class EmotionalBrief:
    mood: Mood
    intensity: str  # low | medium | high
    lead_with_empathy: bool


class EmotionalIntelligenceLayer:
    """Detect user mood and craft the emotional opening of a reply."""

    _JOY = re.compile(
        r"повышен|выиграл|радост|счастлив|отличн\w+\s+новост|получил\w*\s+работ",
        re.I,
    )
    _TIRED = re.compile(r"устал|выгорел|нет\s+сил|измотан|не\s+выспал", re.I)
    _HEAVY = re.compile(
        r"тяжело|плохо|грустн|депресс|не\s+справля|одинок|мне\s+больно|непросто",
        re.I,
    )
    _ANGRY = re.compile(r"бесит|злюсь|раздраж|ужасн|кошмар|ненавиж", re.I)
    _GRATEFUL = re.compile(r"спасибо|благодар|помогли|выручил", re.I)
    _FLAT_EARTH = re.compile(r"земл\w*\s+плоск|плоск\w*\s+земл", re.I)

    def analyze(self, user_message: str) -> EmotionalBrief:
        text = (user_message or "").strip()
        if self._FLAT_EARTH.search(text):
            return EmotionalBrief(Mood.MISINFORMED, "medium", lead_with_empathy=False)
        if self._HEAVY.search(text):
            return EmotionalBrief(Mood.HEAVY, "high", lead_with_empathy=True)
        if self._ANGRY.search(text):
            return EmotionalBrief(Mood.ANGRY, "high", lead_with_empathy=True)
        if self._TIRED.search(text):
            return EmotionalBrief(Mood.TIRED, "medium", lead_with_empathy=True)
        if self._JOY.search(text) or "повышение" in text.lower():
            return EmotionalBrief(Mood.PROMOTION, "high", lead_with_empathy=False)
        if self._GRATEFUL.search(text):
            return EmotionalBrief(Mood.GRATEFUL, "medium", lead_with_empathy=False)
        if "?" in text and len(text) > 20:
            return EmotionalBrief(Mood.CURIOUS, "low", lead_with_empathy=False)
        return EmotionalBrief(Mood.NEUTRAL, "low", lead_with_empathy=False)

    def emotional_opening(self, brief: EmotionalBrief, name: str | None = None) -> str | None:
        """Opening lines when mood should override generic draft."""
        n = f"{name}, " if name else ""

        if brief.mood == Mood.PROMOTION:
            return (
                f"{n}Поздравляю!\n\n"
                "Это замечательная новость.\n\n"
                "Такие моменты действительно приятно отмечать.\n\n"
                "Желаю, чтобы это стало началом ещё больших достижений."
            )

        if brief.mood == Mood.HEAVY:
            return (
                "Мне жаль, что сейчас Вам непросто.\n\n"
                "Давайте попробуем разобраться вместе."
            )

        if brief.mood == Mood.TIRED:
            return (
                f"{n}Понимаю — бывает, когда сил совсем мало.\n\n"
                "Не буду грузить лишним. Если хотите — можем разобрать одну простую задачу "
                "или просто наметить план на потом."
            )

        if brief.mood == Mood.ANGRY:
            return (
                "Слышу Вас. Похоже, ситуация действительно выбила из колеи.\n\n"
                "Давайте спокойно разберём, что можно сделать прямо сейчас."
            )

        if brief.mood == Mood.MISINFORMED:
            return (
                "На сегодняшний день научные данные показывают, что Земля имеет форму, "
                "близкую к сфере.\n\n"
                "Если интересно, могу показать, какие наблюдения и эксперименты к этому привели."
            )

        if brief.mood == Mood.GRATEFUL:
            return (
                "Рад, что смог помочь.\n\n"
                "Если понадобится ещё что-то — я здесь."
            )

        return None

    def to_prompt_hint(self, brief: EmotionalBrief) -> str:
        return f"Настроение пользователя: {brief.mood.value}. Эмпатия первой: {brief.lead_with_empathy}."
