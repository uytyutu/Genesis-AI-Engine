"""
Response Variation Engine — same intent, different words every time.
"""

from __future__ import annotations

import hashlib
import random
from typing import Any

from app.integration.public_truth_catalog import studio_unavailable_message

_POOLS: dict[str, list[str]] = {
    "greeting": [
        "Привет! 👋 Чем займёмся — просто поболтаем, идея или проект?",
        "Рад, что вы здесь. О чём думаете?",
        "Здравствуйте! С чего начнём?",
    ],
    "small_talk": [
        "Всё хорошо, спасибо! 😊 А у вас как дела?",
        "Отлично, на связи. Чем могу помочь сегодня?",
        "Нормально, спасибо что спросили. А вы как?",
        "Всё отлично. Что сегодня будем создавать или обсуждать?",
    ],
    "emotion": [
        "Понимаю, бывает непросто.\n\nХотите выговориться — я рядом. Или переключимся на что-то конкретное, если так легче?",
        "Слышу Вас. Такие чувства нормальны.\n\nЧто сейчас больше всего давит?",
        "Мне жаль, что Вам тяжело.\n\nМогу просто выслушать или помочь с делом — как Вам удобнее?",
    ],
    "science": [
        "Интересная тема.\n\nС чего начнём — простое объяснение или чуть глубже в детали?",
        "Люблю такие вопросы.\n\nРасскажу доступно — скажите, насколько подробно нужно.",
    ],
    "business": [
        "Отлично — давайте подберём направление, которое реально может приносить прибыль.\n\n"
        "В какой стране планируете и какой бюджет на старт?",
        "Хорошая цель.\n\n"
        "Чтобы не гадать: страна, бюджет и хотите ли сами управлять каждый день?",
        "Понял — бизнес.\n\n"
        "Три быстрых ориентира: где открываетесь, сколько готовы вложить, онлайн или офлайн?",
    ],
    "website": [
        "Сайт — правильный шаг.\n\n"
        "Расскажите коротко: чем занимаетесь и для кого сайт?",
        "Сделаем.\n\n"
        "Что важнее на старте — запись клиентов, продажи или просто визитка?",
    ],
    "studio": [
        studio_unavailable_message() + "\n\nРасскажите, какой сайт или бизнес вам нужен — подберём пакет.",
    ],
    "general": [
        "Слушаю. О чём хотите поговорить?",
        "Хорошо. Расскажите — я здесь.",
        "Понял. Продолжайте мысль — я с Вами.",
    ],
    "personal_reflection": [
        "Успех редко приходит одним прыжком — чаще это последовательные шаги и упрямство.\n\n"
        "Если коротко: шансы есть, когда цель ясна и Вы готовы долго учиться.",
        "Интересный вопрос о себе.\n\n"
        "Я бы смотрел не на одну «волшебную» ставку, а на то, что Вы готовы делать регулярно.",
    ],
}


class ResponseVariationEngine:
    """Hash-seeded pools — different answer each visit/day/request."""

    def pick(self, intent: str, visitor_id: str, message: str) -> str:
        pool = _POOLS.get(intent) or _POOLS["general"]
        seed = f"{visitor_id}:{intent}:{message}:{random.random()}"
        idx = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(pool)
        return pool[idx]

    def vary(self, text: str, intent: str, visitor_id: str, salt: str = "") -> str:
        """Light rewrite — swap opening line from pool if template detected."""
        alt = self.pick(intent, visitor_id, salt)
        if len(text) > 80:
            # Keep body, replace weak opener
            lines = text.split("\n", 1)
            if len(lines) > 1:
                return alt.split("\n", 1)[0] + "\n\n" + lines[1]
        return alt
