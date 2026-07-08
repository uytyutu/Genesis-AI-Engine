"""
Executive Brain v2 — reasoning engine: how best to help the human.

Not a category router. Uses Goal Analysis before choosing action.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.layers.conversation_type import (
    ConversationKind,
    classify_conversation_type,
    is_business_mode,
    _business_thread_active,
)
from app.integration.genesis_brain.layers.emotional_intelligence import EmotionalBrief
from app.integration.genesis_brain.layers.goal_analysis import (
    GoalAnalysisLayer,
    GoalBrief,
    HelpfulAction,
)
from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief

ExecutiveAction = Literal[
    "answer",
    "advise",
    "comfort",
    "challenge",
    "teach",
    "explore",
    "wait",
    "ask_one_question",
]


@dataclass(frozen=True)
class ExecutiveDecision:
    """Decision only — no user-facing text."""

    action: ExecutiveAction = "answer"
    optional_question: str | None = None
    confidence: float = 0.0


ResponseMode = Literal[
    "propose",   # offer options, no mandatory question
    "advise",    # help now with known facts
    "clarify",   # one high-value question only
    "close",     # natural conversation end
    "pivot",     # user rejected / changed mind
    "correct",   # user says we were wrong
    "explain",   # user asks why
    "continue",  # default — pass to normal pipeline
]


@dataclass(frozen=True)
class ExecutiveBrief:
    """Internal decision — never shown to user."""

    mode: ResponseMode = "continue"
    conversation_type: ConversationKind = "general_question"
    helpful_action: HelpfulAction = "answer"
    goal: GoalBrief | None = None
    true_want: str = ""
    main_goal: str = ""
    reasoning_chain: str = ""
    can_help_without_questions: bool = False
    optional_question: str | None = None
    contradictions: tuple[str, ...] = ()
    changed_since_last: tuple[str, ...] = ()

    def to_prompt_hint(self) -> str:
        parts = [
            f"Executive v2: mode={self.mode}, action={self.helpful_action}, talk={self.conversation_type}.",
            f"Истинная потребность: {self.true_want or 'уточняется'}.",
            f"Главная цель: {self.main_goal or 'не названа'}.",
        ]
        if self.reasoning_chain:
            parts.append(f"Рассуждение: {self.reasoning_chain}")
        if self.goal:
            parts.append(self.goal.to_prompt_hint())
        if self.can_help_without_questions:
            parts.append("Помогай сейчас — без обязательных вопросов.")
        if self.optional_question:
            parts.append(f"Если нужен один вопрос: {self.optional_question}")
        if self.contradictions:
            parts.append("Противоречия: " + "; ".join(self.contradictions))
        return " ".join(parts)


class GenesisExecutiveBrain:
    """Director — how to help, not which module to call."""

    def __init__(self) -> None:
        self._goal_layer = GoalAnalysisLayer()

    def decide_from_thinking(
        self,
        thinking: ThinkingBrief,
        *,
        state: ConversationState,
        messages: list[dict[str, str]],
        last_user: str,
    ) -> ExecutiveDecision:
        """v3 — decision from Thinking Brief only, no text analysis."""
        action: ExecutiveAction = thinking.recommended_action  # type: ignore[assignment]
        valid = {
            "answer",
            "advise",
            "comfort",
            "challenge",
            "teach",
            "explore",
            "wait",
            "ask_one_question",
        }
        if action not in valid:
            action = "answer"

        low = last_user.strip().lower()
        if re.match(
            r"^(спасибо|благодарю|пока|до\s+свидания|всё|все|на\s+сегодня\s+всё)\b",
            low,
        ) and len(low) < 60:
            action = "wait"

        if re.match(r"^нет\.?$", low) and len(low) < 10:
            if thinking.recommended_action != "answer":
                action = "explore"

        if re.search(r"передумал|переехал|теперь\s+живу|не\s+кофейн|не\s+хочу", low):
            action = "explore"

        optional = thinking.optional_question
        if action == "ask_one_question" and not optional:
            action = "advise"

        return ExecutiveDecision(
            action=action,
            optional_question=optional,
            confidence=thinking.confidence,
        )

    def decide(
        self,
        *,
        state: ConversationState,
        last_user: str,
        messages: list[dict[str, str]],
        turn_index: int,
        emotional: EmotionalBrief | None = None,
    ) -> ExecutiveBrief:
        low = last_user.strip().lower()
        prev = self._previous_state(messages, state)
        talk = classify_conversation_type(last_user, messages, state)
        goal = self._goal_layer.analyze(last_user, messages, state, emotional)

        changed = self._detect_changes(prev, state)
        contradictions = self._detect_contradictions(prev, state, low)

        true_want = goal.implicit_need or self._true_want(state, talk)
        main_goal = state.life_goal or state.motivation or goal.surface_topic

        base = dict(
            conversation_type=talk,
            goal=goal,
            true_want=true_want,
            main_goal=main_goal or "",
            helpful_action=goal.helpful_action,
            reasoning_chain=goal.reasoning_chain,
            can_help_without_questions=goal.helpful_action != "one_question",
            optional_question=goal.optional_question,
            changed_since_last=changed,
            contradictions=contradictions,
        )

        if self._is_closing(low):
            return ExecutiveBrief(**{**base, "mode": "close", "helpful_action": "close"})

        if goal.real_goal == "correction":
            return ExecutiveBrief(**{**base, "mode": "correct", "helpful_action": "answer"})

        if re.search(r"ты\s+ошиб|ошибся|не\s+прав|неправильно", low):
            return ExecutiveBrief(**{**base, "mode": "correct", "helpful_action": "answer"})

        if re.match(r"^почему\??$|^зачем\??$", low) or low.startswith("почему "):
            if (
                state.ready_for_business_advice()
                or _business_thread_active(messages)
                or (state.has_country() and state.has_budget())
            ):
                talk = "business_consulting"
            return ExecutiveBrief(
                **{
                    **base,
                    "mode": "explain",
                    "conversation_type": talk,
                    "helpful_action": "answer",
                }
            )

        if re.match(r"^(нет|не\s+хочу|не\s+надо|не\s+буду)\b", low) and len(low) < 80:
            return ExecutiveBrief(**{**base, "mode": "pivot"})

        if re.search(r"передумал|переехал|теперь\s+живу|переехала", low):
            return ExecutiveBrief(**{**base, "mode": "pivot"})

        # Non-business: help via goal analysis, never product pipeline
        if not is_business_mode(talk) or goal.real_goal in (
            "doubt",
            "future_vision",
            "life_context",
            "emotional_need",
            "correction",
            "small_talk",
            "curiosity",
            "unknown",
        ):
            mode: ResponseMode = "continue"
            if goal.helpful_action == "one_question":
                mode = "clarify"
            return ExecutiveBrief(**{**base, "mode": mode})

        if talk == "business_consulting" or state.goal in ("open_business", "ai_company"):
            if state.ready_for_business_advice():
                return ExecutiveBrief(**{**base, "mode": "advise", "helpful_action": "advise"})

            if state.goal == "ai_company":
                return ExecutiveBrief(**{**base, "mode": "advise", "helpful_action": "advise"})

            if (
                state.goal == "open_business"
                and not state.has_country()
                and not state.has_budget()
                and not state.uncertain_niche
            ):
                return ExecutiveBrief(**{**base, "mode": "propose", "helpful_action": "advise"})

            missing = state.missing_critical(messages)
            if missing and not state.question_already_asked(missing[0], messages):
                q = self._one_question(missing[0], state)
                return ExecutiveBrief(
                    **{
                        **base,
                        "mode": "clarify",
                        "helpful_action": "one_question",
                        "optional_question": q,
                    }
                )

            return ExecutiveBrief(**{**base, "mode": "propose", "helpful_action": "advise"})

        return ExecutiveBrief(**{**base, "mode": "continue"})

    @staticmethod
    def _is_closing(low: str) -> bool:
        if len(low) > 60:
            return False
        return bool(
            re.match(
                r"^(спасибо|благодарю|пока|до\s+свидания|всё|все|на\s+сегодня\s+всё)\b",
                low,
            )
        )

    @staticmethod
    def _true_want(state: ConversationState, talk: ConversationKind = "general_question") -> str:
        if talk == "personal_reflection":
            return "понять себя и свои шансы"
        if talk in ("casual_conversation", "philosophy", "emotional_support"):
            return "поговорить и быть услышанным"
        if state.goal == "ai_company":
            return "построить AI-компанию"
        if state.goal == "open_business":
            if state.business_type == "coffee":
                return "открыть кофейню"
            if state.business_type == "car_wash":
                return "открыть автомойку"
            if state.avoids_people or state.prefers_online:
                return "бизнес с минимумом личного контакта"
            return "открыть прибыльный бизнес"
        if state.life_goal == "financial_independence":
            return "финансовая независимость"
        if state.life_goal == "family_time":
            return "больше времени с семьёй"
        return ""

    @staticmethod
    def _one_question(gap: str, state: ConversationState) -> str:
        if gap == "country":
            return "В какой стране планируете?"
        if gap == "budget":
            return "Какой бюджет на старт?"
        return "Что для Вас важнее — офлайн или онлайн?"

    @staticmethod
    def _previous_state(
        messages: list[dict[str, str]], current: ConversationState
    ) -> ConversationState | None:
        if len(messages) < 2:
            return None
        prior = ConversationState.from_messages(messages[:-1])
        if prior.to_dict() == ConversationState().to_dict():
            return None
        return prior

    @staticmethod
    def _detect_changes(
        prev: ConversationState | None, curr: ConversationState
    ) -> tuple[str, ...]:
        if not prev:
            return ()
        out: list[str] = []
        if prev.country and curr.country and prev.country != curr.country:
            out.append(f"страна: {prev.country} → {curr.country}")
        if prev.city and curr.city and prev.city != curr.city:
            out.append(f"город: {prev.city} → {curr.city}")
        if prev.business_type and curr.business_type and prev.business_type != curr.business_type:
            out.append(f"ниша: {prev.business_type} → {curr.business_type}")
        if prev.budget_amount and curr.budget_amount and prev.budget_amount != curr.budget_amount:
            out.append("бюджет изменился")
        return tuple(out)

    @staticmethod
    def _detect_contradictions(
        prev: ConversationState | None,
        curr: ConversationState,
        low: str,
    ) -> tuple[str, ...]:
        out: list[str] = []
        if prev and prev.business_type and "не хочу" in low:
            out.append(f"отказ от {prev.business_type}")
        if "не кофейн" in low or ("не" in low and "кофе" in low):
            out.append("отказ от кофейни")
        return tuple(out)


def executive_reply(
    brief: ExecutiveBrief,
    state: ConversationState,
    last_user: str,
    *,
    visitor_id: str,
    turn_index: int,
    messages: list[dict[str, str]] | None = None,
) -> str | None:
    """Generate response when Executive Brain overrides generic pipeline."""
    from app.integration.genesis_brain.human_replies import human_reply
    from app.integration.genesis_brain.layers.conversation_state import pick_opening
    from app.integration.genesis_brain.layers.conversation_type import is_business_mode
    from app.integration.genesis_brain.reasoned_reply import (
        _advice_when_ready,
        reasoned_business_reply,
    )

    open_ = pick_opening(visitor_id, turn_index)
    talk = brief.conversation_type

    if brief.mode == "close":
        return (
            "Рад был помочь.\n\n"
            "Если позже захотите вернуться к этой теме — "
            "продолжим именно с того места, на котором остановились."
        )

    if brief.mode == "correct" or talk == "meta_correction":
        if talk == "meta_correction":
            return human_reply(
                "meta_correction",
                last_user,
                state=state,
                visitor_id=visitor_id,
                turn_index=turn_index,
                messages=messages,
            )
        return (
            f"{open_} Спасибо, что поправили — пересмотрю рекомендацию.\n\n"
            "Расскажите, что именно не сходится — я подстрою совет под вашу ситуацию."
        )

    if brief.mode == "explain":
        if state.country == "Россия" and state.budget_amount and state.budget_amount <= 50000:
            return (
                "Потому что при бюджете около **10–50 тыс. ₽** в Москве аренда и оборудование "
                "для полноценной кофейни обычно превышают эту сумму уже в первый месяц.\n\n"
                "Я предложил форматы, которые реально укладываются в такой старт."
            )
        return (
            f"{open_} Коротко: я опираюсь на то, что уже знаю — "
            f"{state.country or 'регион'}, бюджет {state.budget_display() or 'не указан'}.\n\n"
            "Если логика не сходится — поправьте меня, и я пересчитаю."
        )

    if not is_business_mode(talk):
        if brief.goal:
            from app.integration.genesis_brain.reasoned_human import reasoned_human_reply

            return reasoned_human_reply(
                brief.goal,
                brief,
                raw=last_user,
                state=state,
                visitor_id=visitor_id,
                turn_index=turn_index,
                messages=messages,
            )
        human = human_reply(
            talk, last_user, state=state, visitor_id=visitor_id, turn_index=turn_index, messages=messages
        )
        if human:
            return human

    if brief.mode == "pivot":
        if brief.changed_since_last:
            change = brief.changed_since_last[0]
            return (
                f"{open_} Записал изменение: {change}.\n\n"
                + (_advice_when_ready(state, "") if state.ready_for_business_advice() else _propose_three(state, open_))
            )
        if state.avoids_people or state.prefers_online:
            return _propose_online(state, open_)
        return (
            f"{open_} Понял — меняем направление.\n\n"
            + _propose_three(state, open_)
        )

    if brief.mode == "propose":
        return _propose_three(state, open_)

    if brief.mode == "advise":
        routed = reasoned_business_reply(
            state,
            last_user,
            visitor_id=visitor_id,
            turn_index=turn_index,
            messages=messages,
        )
        if routed:
            return routed
        if state.goal == "ai_company" or state.business_type == "car_wash":
            from app.integration.genesis_brain.reasoned_reply import _advice_specialized

            return _advice_specialized(state, open_)
        if state.ready_for_business_advice():
            return _advice_when_ready(state, open_)

    if brief.mode == "clarify" and brief.optional_question:
        ack = ""
        if state.budget_display():
            ack = f"Бюджет **{state.budget_display()}** — принял. "
        elif state.country:
            ack = f"{state.country} — учту. "
        return f"{open_} {ack}{brief.optional_question}"

    if is_business_mode(talk):
        return reasoned_business_reply(
            state,
            last_user,
            visitor_id=visitor_id,
            turn_index=turn_index,
            messages=messages,
        )

    return None


def _propose_three(state: ConversationState, open_: str) -> str:
    """Three options first — questions optional, not mandatory."""
    motiv = ""
    if state.life_goal == "financial_independence":
        motiv = " С учётом цели — финансовая независимость."
    elif state.life_goal == "family_time":
        motiv = " С учётом желания больше времени с семьёй — lean-модели."
    elif state.avoids_people:
        motiv = " Без постоянного общения с клиентами лично."

    loc = ""
    if state.country:
        loc = f" для {state.country}"
        if state.city:
            loc = f" для {state.city}, {state.country}"

    if state.prefers_online or state.avoids_people:
        return _propose_online(state, open_)

    return (
        f"{open_} Я бы предложил три направления{loc}, которые часто хорошо стартуют.{motiv}\n\n"
        "**1. Локальный сервис с записью** — салон, ремонт, мастер на дом. Стабильный спрос.\n\n"
        "**2. Coffee to go / небольшое кафе** — если нравится офлайн и продукт.\n\n"
        "**3. Онлайн-услуга или digital** — консультации, SMM, микро-SaaS. Ниже порог входа.\n\n"
        "Если захотите — потом уточним детали под ваш бюджет и город."
    )


def _propose_online(state: ConversationState, open_: str) -> str:
    return (
        f"{open_} Раз Вам ближе онлайн или минимум личного контакта — три варианта:\n\n"
        "**1. AI-сервис или автоматизация** — боты, микро-SaaS, Virtus Factory.\n\n"
        "**2. Контент + обучение** — курсы, подписка, экспертиза.\n\n"
        "**3. Удалённая услуга** — дизайн, код, маркетинг под ключ.\n\n"
        "Детали подстроим, когда будете готовы."
    )
