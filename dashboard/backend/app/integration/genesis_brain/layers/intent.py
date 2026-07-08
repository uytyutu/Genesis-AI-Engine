"""
Genesis Intent Layer — understand what the user means before generating a reply.

Pipeline: fuzzy normalize → intent → context from history → role → goals.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.fuzzy_nlp import contains_any, normalize_for_intent

IntentKind = str  # greeting | small_talk | emotion | science | business | website | bot | studio | writing | general


@dataclass(frozen=True)
class IntentBrief:
    raw_message: str
    normalized: str
    intent: IntentKind
    role: str
    goals: tuple[str, ...] = ()
    context_topic: str | None = None
    business: ConversationState | None = None
    confidence: str = "medium"  # low | medium | high
    turn_index: int = 0

    def to_prompt_hint(self) -> str:
        goals = ", ".join(self.goals) if self.goals else "понять и помочь"
        ctx = f" Контекст диалога: {self.context_topic}." if self.context_topic else ""
        return (
            f"Намерение: {self.intent}. Роль: {self.role}. Цели пользователя: {goals}.{ctx} "
            f"Отвечайте на смысл, не исправляйте опечатки. Максимум один уточняющий вопрос."
        )


class GenesisIntentLayer:
    """Pre-response intent analysis — internal only."""

    def analyze(
        self,
        messages: list[dict[str, str]],
        memory: dict[str, Any] | None = None,
    ) -> IntentBrief:
        raw = self._last_user_raw(messages)
        normalized = normalize_for_intent(raw)
        turn_index = sum(1 for m in messages if m.get("role") == "user")
        biz = ConversationState.from_messages(messages)
        context_topic = self._context_topic(messages, biz)

        intent, role, goals, confidence = self._classify(normalized, biz, context_topic, turn_index)

        return IntentBrief(
            raw_message=raw,
            normalized=normalized,
            intent=intent,
            role=role,
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
    ) -> tuple[IntentKind, str, tuple[str, ...], str]:
        if contains_any(n, "стой", "останов", "хватит", "прекрати", "стоп"):
            return "control", "companion", ("пауза в разговоре",), "high"

        if contains_any(n, "давай поговорим", "поговорим", "просто поговорить", "поболтаем"):
            return "small_talk", "companion", ("поболтать",), "high"

        if contains_any(n, "привет", "здравствуй", "hello", "hi", "добрый", "доброе"):
            return "greeting", "companion", ("установить контакт",), "high"

        if contains_any(n, "как дела", "как ты", "как вы", "что нового"):
            return "small_talk", "companion", ("поболтать",), "high"

        if contains_any(n, "грустн", "тяжело", "плохо", "одинок", "устал", "боюсь", "страшно"):
            return "emotion", "empath", ("поддержка", "выслушать"), "high"

        if re.search(
            r"как\s+думаешь|как\s+считаешь|получится\s+ли|"
            r"я\s+стану|миллионер|разбогат",
            n,
        ):
            return "personal_reflection", "mentor", ("размышление о себе",), "high"

        if contains_any(n, "шутк", "анекдот", "посмея", "смешн"):
            return "humor", "companion", ("развлечь",), "medium"

        if contains_any(n, "квантов", "физик", "космос", "чёрн", "наук", "объясни"):
            return "science", "teacher", ("объяснить", "обучить"), "high"

        if contains_any(n, "письм", "email", "резюме", "текст для"):
            return "writing", "writer", ("помочь с текстом",), "high"

        if contains_any(n, "studio", "подписк", "платформ") or biz.wants_studio:
            return "studio", "consultant", ("выбрать тариф Studio", "понять выгоду подписки"), "high"

        if contains_any(n, "telegram", "чатбот", "бот", "whatsapp"):
            return "bot", "digital", ("автоматизировать общение",), "high"

        if contains_any(n, "сайт", "лендинг", "интернет-магазин", "магазин"):
            return "website", "digital", ("создать сайт",), "high"

        if (
            contains_any(n, "бизнес", "придумай", "идея", "открыть", "ниша", "проект", "дело")
            or contains_any(n, "бизнесс", "идея бизнес")
            or (biz.goal == "open_business" and context_topic == "business")
            or context_topic == "business"
        ):
            goals: list[str] = ["найти или развить бизнес-идею"]
            if biz.budget_amount:
                goals.append(f"бюджет ~{biz.budget_display()}")
            if biz.country:
                goals.append(f"страна: {biz.country}")
            return "business", "consultant", tuple(goals), "high"

        if contains_any(n, "продвижен", "реклам", "маркетинг", "клиент"):
            return "marketing", "marketing", ("привлечь клиентов",), "medium"

        if contains_any(n, "приложен", "app", "мобильн"):
            return "app", "digital", ("создать приложение",), "medium"

        if context_topic and turn_index > 1:
            return context_topic, "consultant", ("продолжить тему",), "medium"

        return "general", "universal", ("понять задачу", "помочь"), "low"

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
