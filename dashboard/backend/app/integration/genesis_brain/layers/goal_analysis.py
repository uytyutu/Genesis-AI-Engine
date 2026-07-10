"""
Goal Analysis v1 — what the human actually wants, not which pipeline to run.

Analyzes meaning + thread context before Executive Brain decides how to help.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from app.integration.genesis_brain.fuzzy_nlp import normalize_for_intent
from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.layers.emotional_intelligence import EmotionalBrief

RealGoal = Literal[
    "doubt",              # «получится ли», «как думаешь»
    "future_vision",      # «хочу стать миллионером»
    "life_context",       # «мне 27» — факт, не вопрос
    "emotional_need",     # тяжело, страшно, одиноко
    "seeking_validation", # нужно услышать «да, получится»
    "seeking_advice",     # что делать, как начать
    "correction",         # «не тот вопрос»
    "curiosity",          # как работает, что такое
    "business_intent",    # открыть бизнес, сайт
    "small_talk",         # привет, как дела
    "thread_follow_up",   # уточнение к прошлой реплике ассистента
    "factual_question",   # конкретный вопрос
    "unknown",
]

HelpfulAction = Literal[
    "comfort",
    "answer",
    "advise",
    "challenge",
    "acknowledge",   # принять контекст и связать с темой
    "one_question",
    "close",
]

EmotionTone = Literal[
    "hopeful",
    "anxious",
    "heavy",
    "neutral",
    "excited",
    "frustrated",
    "grateful",
]


@dataclass(frozen=True)
class ThreadContext:
    """What the dialogue was about before this turn."""

    mentioned_doubt: bool = False
    mentioned_wealth: bool = False
    mentioned_success: bool = False
    mentioned_age: bool = False
    mentioned_business: bool = False
    prior_topics: tuple[str, ...] = ()

    def dominant_theme(self) -> str | None:
        if self.mentioned_wealth or self.mentioned_success:
            return "future"
        if self.mentioned_doubt:
            return "doubt"
        if self.mentioned_business:
            return "business"
        return None


@dataclass(frozen=True)
class GoalBrief:
    """Internal — user's real goal and how to help."""

    real_goal: RealGoal
    helpful_action: HelpfulAction
    emotion: EmotionTone
    implicit_need: str
    reasoning_chain: str
    thread: ThreadContext
    surface_topic: str = ""
    should_ask_question: bool = False
    optional_question: str | None = None
    known_facts: tuple[str, ...] = ()

    def to_prompt_hint(self) -> str:
        return (
            f"Goal: {self.real_goal}. Действие: {self.helpful_action}. "
            f"Эмоция: {self.emotion}. Потребность: {self.implicit_need}. "
            f"Рассуждение: {self.reasoning_chain}"
        )


class GoalAnalysisLayer:
    """Understand human goal from meaning + memory + thread — not keywords alone."""

    def analyze(
        self,
        last_user: str,
        messages: list[dict[str, str]],
        state: ConversationState,
        emotional: EmotionalBrief | None = None,
    ) -> GoalBrief:
        raw = (last_user or "").strip()
        n = normalize_for_intent(raw)
        low = raw.lower()
        thread = self._thread_context(messages, state)
        emotion = self._emotion_tone(emotional, low)
        facts = self._known_facts(state)

        real_goal = self._real_goal(raw, n, low, thread, state, messages)
        implicit = self._implicit_need(real_goal, thread, emotion, state)
        action, question = self._helpful_action(real_goal, thread, state, low)
        reasoning = self._reasoning_chain(
            real_goal, action, implicit, thread, state, raw
        )

        return GoalBrief(
            real_goal=real_goal,
            helpful_action=action,
            emotion=emotion,
            implicit_need=implicit,
            reasoning_chain=reasoning,
            thread=thread,
            surface_topic=self._surface_topic(n, low),
            should_ask_question=question is not None,
            optional_question=question,
            known_facts=facts,
        )

    def _real_goal(
        self,
        raw: str,
        n: str,
        low: str,
        thread: ThreadContext,
        state: ConversationState,
        messages: list[dict[str, str]],
    ) -> RealGoal:
        if re.search(
            r"не\s+тот\s+вопрос|не\s+этот\s+вопрос|я\s+задавал|задавал\s+не|"
            r"неверно\s+понял|не\s+то\s+ответ|"
            r"ты\s+ошиб|ошибся|не\s+прав|неправильно|"
            r"не\s+так|не\s+понял|не\s+поняла",
            low,
        ):
            return "correction"

        if re.match(r"^нет\.?$", low.strip()) and len(raw) < 12:
            return "correction"

        if re.match(r"^(спасибо|благодарю|пока|до\s+свидания)\b", low) and len(low) < 60:
            return "small_talk"

        if re.search(
            r"как\s+думаешь|как\s+считаешь|получится\s+ли|смогу\s+ли|"
            r"я\s+стану|стану\s+ли|у\s+меня\s+получ",
            raw,
            re.I,
        ):
            return "doubt"

        if re.search(r"миллионер|миллион|разбогат|богатств|стать\s+богат", low):
            return "future_vision"

        if self._is_life_context(raw, low):
            return "life_context"

        if re.search(r"мне\s+плохо|тяжело|грустн|одинок|устал|боюсь|страшно|тревож", low):
            return "emotional_need"

        if re.search(
            r"открыть|бизнес|бизнесс|сайт|хочу\s+сайт|придумай\s+иде|"
            r"бюджет\s+\d|€|евро|\d+\s*к\s*(?:руб|rub|₽)|"
            r"у меня\s+(?:есть\s+)?|интернет-магазин|кофейн|автомойк|магазин",
            low,
        ):
            return "business_intent"
        if thread.mentioned_business and re.search(r"бюджет|€|евро|руб|₽", low):
            return "business_intent"

        if re.search(r"^(привет|здравствуй|hello|hi|как\s+дела)\b", low):
            return "small_talk"

        if self._is_thread_follow_up(raw, low, messages):
            return "thread_follow_up"

        if re.search(r"что\s+такое|как\s+работает|объясни|почиму|почему", low):
            return "curiosity"

        if "?" in raw or re.search(r"^(как|зачем|где|когда|сколько)\b", low):
            return "factual_question"

        if thread.dominant_theme() == "doubt" and len(low) < 40:
            return "doubt"

        return "unknown"

    @staticmethod
    def _prior_assistant_text(messages: list[dict[str, str]]) -> str:
        skipped_current_user = False
        for msg in reversed(messages):
            role = msg.get("role")
            if role == "user" and not skipped_current_user:
                skipped_current_user = True
                continue
            if skipped_current_user and role == "assistant":
                return (msg.get("content") or "").strip()
        return ""

    def _is_thread_follow_up(
        self,
        raw: str,
        low: str,
        messages: list[dict[str, str]],
    ) -> bool:
        """User clarifies or questions the assistant's previous reply — not a new topic."""
        prior = self._prior_assistant_text(messages)
        if not prior:
            return False
        if re.search(
            r"^(?:в\s+смысле|почему\s+ты|чему\s+ты|зачем\s+ты|что\s+значит|"
            r"что\s+имел\s+в\s+виду|как\s+это\s+понимать|ты\s+чего|"
            r"можно\s+попроще|не\s+понял|не\s+поняла)\b",
            low,
        ):
            return True
        if len(low) < 90 and "?" in raw and re.search(
            r"\b(?:ты|тебя|твой|твоя|это|так|смысл|имел|рад|связ)\b",
            low,
        ):
            return True
        return False

    @staticmethod
    def _is_life_context(raw: str, low: str) -> bool:
        if re.search(r"мне\s+\d{1,2}\s*(?:лет|года|год)?\b", low):
            return True
        if re.search(r"мне\s+(?:уже\s+)?(?:двадцать|тридцать|сорок)", low):
            return True
        if re.match(r"^\d{1,2}\s*(?:лет|года)\.?$", low.strip()):
            return True
        if len(low) < 50 and not "?" in raw:
            if re.search(r"работаю\s+|учусь\s+|живу\s+в\s+|переехал", low):
                return True
        return False

    def _thread_context(
        self,
        messages: list[dict[str, str]],
        state: ConversationState,
    ) -> ThreadContext:
        users = [m.get("content") or "" for m in messages if m.get("role") == "user"]
        prior = users[:-1] if len(users) > 1 else []
        topics: list[str] = []

        mentioned_doubt = mentioned_wealth = mentioned_success = mentioned_age = False
        mentioned_business = bool(state.goal)

        for text in users:
            t = text.lower()
            if re.search(r"как\s+думаешь|получится|успеш|смогу\s+ли", t, re.I):
                mentioned_doubt = True
                topics.append("doubt")
            if re.search(r"миллион|разбогат|богат", t):
                mentioned_wealth = True
                topics.append("wealth")
            if re.search(r"успеш", t):
                mentioned_success = True
            if re.search(r"мне\s+\d{1,2}|мне\s+(?:двадцать|тридцать)", t):
                mentioned_age = True
                topics.append("age")
            if re.search(r"бизнес|сайт|открыть", t):
                mentioned_business = True
                topics.append("business")

        if state.user_age:
            mentioned_age = True

        return ThreadContext(
            mentioned_doubt=mentioned_doubt,
            mentioned_wealth=mentioned_wealth,
            mentioned_success=mentioned_success,
            mentioned_age=mentioned_age,
            mentioned_business=mentioned_business,
            prior_topics=tuple(dict.fromkeys(topics)),
        )

    @staticmethod
    def _emotion_tone(emotional: EmotionalBrief | None, low: str) -> EmotionTone:
        if emotional:
            m = emotional.mood.value
            if m in ("heavy", "tired", "angry"):
                return "heavy"
            if m == "promotion":
                return "excited"
            if m == "grateful":
                return "grateful"
        if re.search(r"боюсь|страшно|тревож|сомнева", low):
            return "anxious"
        if re.search(r"надеюсь|мечта|хочу\s+стать", low):
            return "hopeful"
        if re.search(r"злюсь|бесит|раздраж", low):
            return "frustrated"
        return "neutral"

    @staticmethod
    def _implicit_need(
        real_goal: RealGoal,
        thread: ThreadContext,
        emotion: EmotionTone,
        state: ConversationState,
    ) -> str:
        if real_goal == "doubt":
            return "услышать честную оценку шансов без пустых обещаний"
        if real_goal == "future_vision":
            return "понять, реалистичен ли путь и с чего начать внутренне"
        if real_goal == "life_context":
            if thread.mentioned_doubt or thread.mentioned_wealth:
                return "чтобы контекст связали с темой разговора, а не проигнорировали"
            return "быть услышанным — факт о себе"
        if real_goal == "emotional_need":
            return "поддержка или конкретная помощь — по ситуации"
        if real_goal == "correction":
            return "признать ошибку в предыдущем ответе и исправить, не спрашивая «уточните»"
        if real_goal == "business_intent":
            return "практический путь, не анкета ради анкеты"
        if emotion == "anxious":
            return "успокоение и ясность"
        return "полезный ответ без лишних вопросов"

    def _helpful_action(
        self,
        real_goal: RealGoal,
        thread: ThreadContext,
        state: ConversationState,
        low: str,
    ) -> tuple[HelpfulAction, str | None]:
        if real_goal == "correction":
            return "answer", None
        if real_goal == "life_context":
            return "acknowledge", None
        if real_goal == "doubt":
            return "comfort" if "страш" in low or "боюсь" in low else "answer", None
        if real_goal == "future_vision":
            return "advise", None
        if real_goal == "emotional_need":
            return "comfort", None
        if real_goal == "business_intent":
            if state.ready_for_business_advice():
                return "advise", None
            if state.ready_for_proposal():
                return "advise", None
            if state.has_budget() or state.has_country():
                return "acknowledge", None
            missing = state.missing_critical()
            if missing and real_goal == "business_intent":
                return "one_question", self._gap_question(missing[0], state)
            return "advise", None
        if real_goal == "small_talk":
            return "answer", None
        if real_goal == "curiosity":
            return "answer", None
        return "answer", None

    @staticmethod
    def _gap_question(gap: str, state: ConversationState) -> str:
        if gap == "country":
            return "В какой стране планируете?"
        if gap == "budget":
            return "Какой бюджет на старт?"
        return "Что для Вас важнее — офлайн или онлайн?"

    @staticmethod
    def _known_facts(state: ConversationState) -> tuple[str, ...]:
        out: list[str] = []
        if state.user_name:
            out.append(f"имя: {state.user_name}")
        if state.user_age:
            out.append(f"возраст: {state.user_age}")
        if state.country:
            out.append(f"страна: {state.country}")
        if state.life_goal:
            out.append(f"жизненная цель: {state.life_goal}")
        if state.goal:
            out.append(f"цель: {state.goal}")
        return tuple(out)

    @staticmethod
    def _surface_topic(n: str, low: str) -> str:
        if "миллион" in low:
            return "богатство"
        if "успеш" in low:
            return "успех"
        if "бизнес" in low or "бизнесс" in low:
            return "бизнес"
        return ""

    def _reasoning_chain(
        self,
        real_goal: RealGoal,
        action: HelpfulAction,
        implicit: str,
        thread: ThreadContext,
        state: ConversationState,
        raw: str,
    ) -> str:
        parts: list[str] = []
        parts.append(f"Пользователь хочет: {implicit}.")

        if real_goal == "doubt":
            parts.append("Это не запрос на бизнес — это сомнение в себе.")
        elif real_goal == "future_vision":
            parts.append("Речь о будущем и амбиции, не о покупке продукта.")
        elif real_goal == "life_context":
            parts.append("Это контекст о человеке, не отдельный вопрос.")
            if thread.mentioned_doubt:
                parts.append("Связать с ранее высказанным сомнением.")
            if thread.mentioned_wealth:
                parts.append("Связать с темой денег/богатства.")

        if state.user_age and real_goal in ("future_vision", "doubt", "life_context"):
            parts.append(f"Возраст {state.user_age} — учесть горизонт времени.")

        parts.append(f"Лучшее действие сейчас: {action}.")
        if action != "one_question":
            parts.append("Не задавать вопрос ради вопроса.")

        return " ".join(parts)
