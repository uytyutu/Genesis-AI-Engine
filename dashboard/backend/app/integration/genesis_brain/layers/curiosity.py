"""
Curiosity Layer — gentle initiative when appropriate.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.integration.genesis_brain.layers.emotional_intelligence import EmotionalBrief, Mood

_QUESTION_STARTERS = [
    "Кстати, можно задать один уточняющий вопрос?",
    "Если уместно — один короткий вопрос:",
    "Позвольте уточнить одну деталь:",
]

_IDEA_STARTERS = [
    "У меня появилась идея, которая может улучшить Ваш проект.",
    "Кстати, есть мысль, которая может Вам пригодиться.",
    "Пока мы на этой теме — одна идея:",
]

_FOLLOW_UPS = [
    "Заведение уже работает или только открывается?",
    "Вам ближе готовый сайт под ключ или хотите сами в Studio?",
    "Хотите, чтобы клиенты записывались онлайн?",
    "Какой срок для Вас комфортен?",
    "Это для одного города или сразу нескольких точек?",
]

_DISCOVERY_HINTS = {
    "cafe": (
        "Кстати, позже я смогу помочь с Telegram-ботом, автоматизацией заказов "
        "или мобильным приложением, если это будет полезно."
    ),
    "salon": (
        "Если понадобится — помогу с онлайн-записью, WhatsApp-ботом или рассылкой "
        "для клиентов. Без навязчивости, когда Вы будете готовы."
    ),
    "shop": (
        "Позже можно добавить каталог, оплату онлайн и уведомления о заказах — "
        "скажите, когда захотите углубиться."
    ),
    "bot": (
        "Такой бот можно связать с сайтом, CRM или таблицей заказов — "
        "подскажу, когда дойдём до этого этапа."
    ),
}


def _discovery_topic(text: str) -> str | None:
    t = text.lower()
    if any(w in t for w in ("кофейн", "кафе", "coffee")):
        return "cafe"
    if any(w in t for w in ("салон", "красот", "барбер")):
        return "salon"
    if any(w in t for w in ("магазин", "интернет-магазин")):
        return "shop"
    if any(w in t for w in ("telegram", "телеграм", "бот")):
        return "bot"
    return None


_BUSINESS_IDEAS = [
    "Можно начать с простого лендинга и подключить запись — часто это даёт первых клиентов за пару недель.",
    "Иногда помогает Telegram-бот для записи — дешевле сайта и быстрее запуск.",
    "Если бюджет ограничен — старт с 4 страниц и расширение после первых заказов.",
]


@dataclass(frozen=True)
class CuriosityHint:
    append: str | None = None


class CuriosityLayer:
    """Adds one optional question or idea — not every turn."""

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
    ) -> CuriosityHint:
        if conversation_type not in ("business_consulting", "product_creation"):
            return CuriosityHint()

        if emotional.mood in self._SKIP_MOODS:
            return CuriosityHint()

        if turn_index < 1:
            return CuriosityHint()

        seed = f"{visitor_id}:{turn_index}:{user_message[:40]}"
        roll = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % 100

        # ~35% of turns after the first get initiative
        if roll > 35:
            return CuriosityHint()

        text = user_message.lower()
        topic = _discovery_topic(text)
        if topic and turn_index >= 1 and roll % 3 != 0:
            hint = _DISCOVERY_HINTS.get(topic)
            if hint:
                return CuriosityHint(append=f"\n\n{hint}")

        if has_business_topic or any(w in text for w in ("сайт", "кафе", "салон", "магазин", "бот")):
            if roll % 2 == 0:
                q = _FOLLOW_UPS[roll % len(_FOLLOW_UPS)]
                starter = _QUESTION_STARTERS[roll % len(_QUESTION_STARTERS)]
                return CuriosityHint(append=f"\n\n{starter}\n{q}")
            idea = _BUSINESS_IDEAS[roll % len(_BUSINESS_IDEAS)]
            starter = _IDEA_STARTERS[roll % len(_IDEA_STARTERS)]
            return CuriosityHint(append=f"\n\n{starter}\n{idea}")

        if "?" not in user_message and len(user_message) > 15:
            if has_business_topic or any(w in text for w in ("сайт", "бизнес", "бот")):
                starter = _QUESTION_STARTERS[roll % len(_QUESTION_STARTERS)]
                q = _FOLLOW_UPS[roll % len(_FOLLOW_UPS)]
                return CuriosityHint(append=f"\n\n{starter}\n{q}")

        return CuriosityHint()

    @staticmethod
    def has_business_topic(text: str) -> bool:
        return bool(
            re.search(
                r"сайт|кафе|салон|магазин|бот|studio|бизнес|заказ|лендинг",
                text,
                re.I,
            )
        )
