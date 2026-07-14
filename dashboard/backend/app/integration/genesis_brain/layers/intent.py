"""
Genesis Intent Layer — what the user needs for progress, before generating a reply.

Pipeline: fuzzy normalize → topic intent → Journey phase → context from history → goals.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.fuzzy_nlp import contains_any, normalize_for_intent
from app.integration.vector_intelligence.pipeline import analyze_turn
from app.integration.vector_intelligence.types import JOURNEY_PHASE_LABELS, JourneyPhase

IntentKind = str  # greeting | small_talk | emotion | science | business | website | bot | studio | writing | general


@dataclass(frozen=True)
class IntentBrief:
    raw_message: str
    normalized: str
    intent: IntentKind
    journey_phase: JourneyPhase
    goals: tuple[str, ...] = ()
    context_topic: str | None = None
    business: ConversationState | None = None
    confidence: str = "medium"  # low | medium | high
    turn_index: int = 0

    def to_prompt_hint(self) -> str:
        goals = ", ".join(self.goals) if self.goals else "движение к результату"
        ctx = f" Контекст диалога: {self.context_topic}." if self.context_topic else ""
        phase = JOURNEY_PHASE_LABELS.get(self.journey_phase, self.journey_phase)
        return (
            f"Этап Journey: {phase}. Что нужно человеку сейчас: {goals}.{ctx} "
            f"Отвечайте на смысл, не исправляйте опечатки. Максимум один уточняющий вопрос."
        )


class GenesisIntentLayer:
    """Pre-response intent analysis — internal only."""

    def analyze(
        self,
        messages: list[dict[str, str]],
        memory: dict[str, Any] | None = None,
    ) -> IntentBrief:
        _ = memory
        raw = self._last_user_raw(messages)
        normalized = normalize_for_intent(raw)
        turn_index = sum(1 for m in messages if m.get("role") == "user")
        biz = ConversationState.from_messages(messages)
        context_topic = self._context_topic(messages, biz)

        intent, goals, confidence = self._classify(normalized, biz, context_topic, turn_index)
        history = messages[:-1] if len(messages) > 1 else None
        journey_phase = analyze_turn(raw, history=history).journey_phase

        return IntentBrief(
            raw_message=raw,
            normalized=normalized,
            intent=intent,
            journey_phase=journey_phase,
            goals=goals,
            context_topic=context_topic,
            business=biz,
            confidence=confidence,
            turn_index=turn_index,
        )

    def _classify(
        self,
        n: str,
        biz: ConversationState,
        context_topic: str | None,
        turn_index: int,
    ) -> tuple[IntentKind, tuple[str, ...], str]:
        if contains_any(n, "стой", "останов", "хватит", "прекрати", "стоп"):
            return "control", ("уважить границу и паузу",), "high"

        if contains_any(n, "давай поговорим", "поговорим", "просто поговорить", "поболтаем"):
            return "small_talk", ("ответить по сути без продаж",), "high"

        if contains_any(n, "привет", "здравствуй", "hello", "hi", "добрый", "доброе"):
            return "greeting", ("теплый контакт без навязывания задачи",), "high"

        if contains_any(n, "как дела", "как ты", "как вы", "что нового"):
            return "small_talk", ("ответить по сути без продаж",), "high"

        if contains_any(n, "грустн", "тяжело", "плохо", "одинок", "устал", "боюсь", "страшно"):
            return "emotion", ("поддержка и ясность",), "high"

        if re.search(
            r"как\s+думаешь|как\s+считаешь|получится\s+ли|"
            r"я\s+стану|миллионер|разбогат",
            n,
        ):
            return "personal_reflection", ("честный разговор без продаж",), "high"

        if contains_any(n, "шутк", "анекдот", "посмея", "смешн"):
            return "humor", ("лёгкий ответ по теме",), "medium"

        if contains_any(n, "квантов", "физик", "космос", "чёрн", "наук", "объясни"):
            return "science", ("ясное объяснение",), "high"

        if contains_any(n, "письм", "email", "резюме", "текст для"):
            return "writing", ("помочь с текстом",), "high"

        if contains_any(n, "studio", "подписк", "платформ") or biz.wants_studio:
            return "studio", ("честно о Virtus Studio",), "high"

        if contains_any(n, "telegram", "чатбот", "бот", "whatsapp"):
            return "bot", ("принять задачу по боту",), "high"

        if contains_any(n, "сайт", "лендинг", "интернет-магазин", "магазин"):
            return "website", ("принять задачу по сайту",), "high"

        if (
            contains_any(n, "бизнес", "придумай", "идея", "открыть", "ниша", "проект", "дело")
            or contains_any(n, "бизнесс", "идея бизнес")
            or (biz.goal == "open_business" and context_topic == "business")
            or context_topic == "business"
        ):
            goals: list[str] = ["принять задачу и прояснить цель"]
            if biz.budget_amount:
                goals.append(f"бюджет ~{biz.budget_display()}")
            if biz.country:
                goals.append(f"страна: {biz.country}")
            return "business", tuple(goals), "high"

        if contains_any(n, "продвижен", "реклам", "маркетинг", "клиент"):
            return "marketing", ("следующий шаг к видимости",), "medium"

        if contains_any(n, "приложен", "app", "мобильн"):
            return "app", ("принять задачу по приложению",), "medium"

        if context_topic and turn_index > 1:
            return context_topic, ("продолжить тему к результату",), "medium"

        return "general", ("понять задачу и взять в работу",), "low"

    @staticmethod
    def _context_topic(messages: list[dict[str, str]], biz: ConversationState) -> str | None:
        if biz.goal == "open_business" or biz.business_type or biz.uncertain_niche:
            return "business"
        for m in reversed(messages[:-1] if messages else []):
            if m.get("role") != "user":
                continue
            n = normalize_for_intent(m.get("content") or "")
            if contains_any(n, "бизнес", "придумай", "идея", "открыть"):
                return "business"
            if contains_any(n, "сайт", "лендинг"):
                return "website"
            if contains_any(n, "studio"):
                return "studio"
            if contains_any(n, "грустн", "тяжело"):
                return "emotion"
        return None

    @staticmethod
    def _last_user_raw(messages: list[dict[str, str]]) -> str:
        for m in reversed(messages):
            if m.get("role") == "user":
                return (m.get("content") or "").strip()
        return ""
