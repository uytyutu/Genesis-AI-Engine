"""
Conversation Style Engine — variety in greetings and closings.

Genesis Public never repeats the same welcome twice in a row.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

_GREETING_FIRST = [
    (
        "Добро пожаловать в Genesis.\n\n"
        "Рад видеть Вас.\n\n"
        "Чем могу помочь сегодня?"
    ),
    (
        "Здравствуйте! Вы в Genesis — месте, где идеи становятся продуктами.\n\n"
        "Расскажите, что у Вас на уме."
    ),
    (
        "Приветствую Вас в Genesis.\n\n"
        "Я здесь, чтобы помочь с бизнесом, проектами и любыми вопросами.\n\n"
        "С чего начнём?"
    ),
    (
        "Добрый день! Genesis на связи.\n\n"
        "Чем могу быть полезен сегодня?"
    ),
]

_GREETING_RETURN = [
    (
        "Добро пожаловать обратно.\n\n"
        "Рад новой встрече.\n\n"
        "О чём поговорим сегодня?"
    ),
    (
        "Снова рад Вас видеть.\n\n"
        "Чем займёмся на этот раз?"
    ),
    (
        "Рад снова видеть Вас.\n\n"
        "Чем сегодня могу быть полезен?"
    ),
    (
        "Вы снова здесь — отлично.\n\n"
        "Продолжим с того, что важно, или начнём новую тему?"
    ),
]

_GREETING_NAMED = [
    "Добро пожаловать обратно, {name}.\n\nРад новой встрече.\n\nО чём поговорим сегодня?",
    "{name}, рад снова Вас видеть.\n\nЧем могу помочь сегодня?",
    "Здравствуйте, {name}!\n\nХорошо, что Вы снова здесь.\n\nС чего начнём?",
    "{name}, Genesis на связи.\n\nЧто для Вас сейчас в приоритете?",
]

_MORNING = [
    "Доброе утро! Рад видеть Вас в Genesis.\n\nЧем займёмся сегодня?",
    "Доброе утро.\n\nGenesis на связи — чем могу помочь?",
    "Доброе утро! Вы в Genesis.\n\nС чего начнём день?",
]

_GREETING_FAMILIAR = [
    "Чем займёмся сегодня?",
    "Рад снова видеть Вас.\n\nО чём поговорим?",
    "Genesis на связи.\n\nЧто для Вас сейчас в приоритете?",
    "Хорошо, что Вы снова здесь.\n\nС чего начнём?",
]

_GREETING_LONG_TERM = [
    "Надеюсь, день проходит хорошо.\n\nЧем могу быть полезен?",
    "Рад нашей давней беседе.\n\nО чём поговорим сегодня?",
    "Вы снова здесь — ценю это.\n\nЧем займёмся?",
    "Genesis на связи.\n\nПродолжим или новая тема?",
]

_EVENING = [
    "Добрый вечер! Рад, что заглянули в Genesis.\n\nЧем могу помочь?",
    "Добрый вечер.\n\nGenesis на связи — о чём поговорим?",
    "Добрый вечер.\n\nРад видеть Вас — с чего начнём?",
]


@dataclass(frozen=True)
class StyleContext:
    visit_count: int = 0
    name: str | None = None
    visitor_id: str = "anonymous"
    hour: int = 12


class ConversationStyleEngine:
    """Picks natural, non-repeating phrasing from constitution pools."""

    def pick_greeting(self, ctx: StyleContext) -> str:
        seed = f"{ctx.visitor_id}:{ctx.visit_count}:{datetime.now(timezone.utc).date().isoformat()}"
        idx = int(hashlib.sha256(seed.encode()).hexdigest(), 16)

        if ctx.name and ctx.visit_count > 0:
            pool = _GREETING_NAMED
            text = pool[idx % len(pool)].format(name=ctx.name)
            return text

        if ctx.hour >= 18:
            return _EVENING[idx % len(_EVENING)]
        if ctx.hour < 11 and ctx.visit_count == 0:
            return _MORNING[idx % len(_MORNING)]

        if ctx.visit_count >= 30:
            return _GREETING_LONG_TERM[idx % len(_GREETING_LONG_TERM)]
        if ctx.visit_count >= 8:
            return _GREETING_FAMILIAR[idx % len(_GREETING_FAMILIAR)]
        if ctx.visit_count <= 1:
            return _GREETING_FIRST[idx % len(_GREETING_FIRST)]
        return _GREETING_RETURN[idx % len(_GREETING_RETURN)]

    def build_context(self, memory: dict[str, Any] | None, visitor_id: str) -> StyleContext:
        mem = memory or {}
        hour = datetime.now(timezone.utc).hour
        return StyleContext(
            visit_count=int(mem.get("visit_count") or 0),
            name=mem.get("name"),
            visitor_id=visitor_id,
            hour=hour,
        )

    def is_greeting_message(self, text: str) -> bool:
        t = text.strip().lower()
        if len(t) > 60:
            return False
        starters = (
            "привет",
            "здравствуй",
            "добрый",
            "доброе",
            "hello",
            "hi",
            "hey",
            "доброго",
        )
        return any(t.startswith(s) for s in starters)
