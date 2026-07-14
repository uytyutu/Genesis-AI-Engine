"""
Semantic brief enrichers — return meaning (inference), never user-facing text.

Replaces _success_reply / _millionaire_reply / _business_reply template functions.
"""

from __future__ import annotations

import re
from typing import Any

from dataclasses import replace

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.layers.goal_analysis import GoalBrief, RealGoal, ThreadContext
from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief


def _journey_ctx(phase: str, situation: str, *, gap: str = "", next_step: str = "") -> str:
    """Situational context for Journey — not role or communication style."""
    parts = [f"этап Journey: {phase}", f"ситуация: {situation}"]
    if gap:
        parts.append(f"пробел для проекта: {gap}")
    if next_step:
        parts.append(f"следующий шаг: {next_step}")
    return "; ".join(parts)


def enrich_thinking_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    state: ConversationState,
    last_user: str,
    messages: list[dict[str, str]],
    memory_inferences: dict[str, Any] | None,
) -> ThinkingBrief:
    """Apply inference enrichers — conclusions, not tags."""
    low = last_user.lower()
    rg = goal.real_goal

    if rg == "future_vision":
        return _millionaire_brief(base, goal, state, memory_inferences)
    if rg == "doubt":
        return _success_brief(base, goal, state, last_user)
    if rg == "life_context":
        return _life_context_brief(base, goal, state, last_user)
    if rg == "business_intent":
        return _business_brief(base, goal, state, messages)
    if rg == "correction":
        return _correction_brief(base, goal, messages)
    if _is_uncertain_domain(low):
        return _uncertainty_brief(base, goal, last_user)
    if rg == "curiosity" and re.match(r"^почему\??$|^зачем\??$", low.strip()):
        return _explain_brief(base, goal, state)
    if rg == "curiosity":
        return _curiosity_brief(base, goal, last_user)
    if rg == "emotional_need":
        return _emotional_brief(base, goal, last_user)
    if rg == "small_talk":
        return _small_talk_brief(base, goal, last_user)
    if rg == "factual_question":
        return _factual_brief(base, goal, last_user)
    if re.search(r"сколько\s+мне\s+лет|какой\s+(?:у\s+меня\s+)?возраст|сколько\s+мне\s+сейчас", low):
        return _age_recall_brief(base, state, memory_inferences)
    if memory_inferences:
        return _apply_memory_inferences(base, memory_inferences)
    return base


def _millionaire_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    state: ConversationState,
    memory: dict[str, Any] | None,
) -> ThinkingBrief:
    risks = ("нереалистичные ожидания быстрого богатства", "путать символ с целью")
    ctx = _journey_ctx(
        "Открытый диалог",
        "личный вопрос о деньгах и будущем",
        next_step="честный ответ без каталога продуктов",
    )

    return ThinkingBrief(
        **{
            **base.__dict__,
            "conversation_goal": "изменить жизнь через финансы",
            "real_goal": "финансовая свобода и возможность изменить жизнь",
            "implicit_need": "ясность без пустых обещаний",
            "emotional_state": "надежда",
            "confidence": 0.84,
            "recommended_action": "advise",
            "why": (
                "Слово «миллионер» часто означает не цифру на счёте, "
                "а желание свободы и контроля над своей жизнью."
            ),
            "risks": risks,
            "best_response_strategy": ctx,
        }
    )


def _success_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    state: ConversationState,
    last_user: str,
) -> ThinkingBrief:
    anxious = bool(re.search(r"страш|боюсь", last_user, re.I)) or goal.emotion == "anxious"
    return ThinkingBrief(
        **{
            **base.__dict__,
            "conversation_goal": "понять свои шансы",
            "real_goal": "получить поддержку и честное мнение",
            "implicit_need": "услышать честную оценку без пустых обещаний",
            "emotional_state": "сомнение" if not anxious else "тревога",
            "confidence": 0.82,
            "recommended_action": "comfort" if anxious else "answer",
            "why": (
                "Вопрос «стану ли успешным» — не про бизнес-план, "
                "а про страх не оправдать ожидания."
            ),
            "risks": ("пустые обещания", "уход в продажу сайтов"),
            "best_response_strategy": _journey_ctx(
                "Открытый диалог",
                "сомнение в успехе",
                next_step="поддержка без гарантий и без каталога",
            ),
        }
    )


def _life_context_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    state: ConversationState,
    last_user: str,
) -> ThinkingBrief:
    age = state.user_age
    thread = goal.thread
    real = "контекст о себе"
    ctx = _journey_ctx("Открытый диалог", "человек делится фактом о себе")
    why = "Человек делится фактом о себе, ожидая, что его не проигнорируют."

    if age and (thread.mentioned_doubt or thread.mentioned_success):
        real = "возраст в контексте сомнения об успехе"
        why = (
            f"Возраст {age} в контексте сомнения об успехе — "
            "часто сигнал «успею ли я»."
        )
        ctx = _journey_ctx(
            "Открытый диалог",
            f"возраст {age} лет на фоне сомнения",
            next_step="связать с ранее обсуждённым",
        )
    elif age and thread.mentioned_wealth:
        real = "контекст к разговору о будущем"
        ctx = _journey_ctx(
            "Открытый диалог",
            f"возраст {age} лет на фоне финансовой цели",
        )

    return ThinkingBrief(
        **{
            **base.__dict__,
            "real_goal": real,
            "why": why,
            "best_response_strategy": ctx,
            "confidence": 0.78,
            "recommended_action": "answer",
        }
    )


def _business_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    state: ConversationState,
    messages: list[dict[str, str]],
) -> ThinkingBrief:
    optional = goal.optional_question
    missing = state.missing_critical(messages)

    if state.ready_for_business_advice():
        ctx = _journey_ctx(
            "1. Принятие ответственности",
            "достаточно фактов для плана",
            next_step="предложить направления к результату",
        )
        action = "advise"
        optional = None
    elif state.life_goal == "family_time":
        ctx = _journey_ctx(
            "2. Понимание цели",
            "семья важнее 24/7 присутствия",
            next_step="lean-модели в плане",
        )
        action = "advise"
        optional = None
    elif not state.has_country() and not state.has_budget():
        ctx = _journey_ctx(
            "1. Принятие ответственности",
            "ранний бизнес-интент",
            next_step="предложить направления без анкеты",
        )
        action = "advise"
        optional = None
    elif state.has_budget() and state.uncertain_niche:
        ctx = _journey_ctx(
            "2. Понимание цели",
            "бюджет известен, формат неясен",
            gap="формат результата",
            next_step="один вопрос только если без него нельзя двигаться",
        )
        action = "ask_one_question" if goal.optional_question else "advise"
    elif missing:
        ctx = _journey_ctx(
            "2. Понимание цели",
            "не хватает факта для brief",
            gap=missing[0],
            next_step="один вопрос по пробелу",
        )
        action = "ask_one_question"
    else:
        ctx = _journey_ctx(
            "1. Принятие ответственности",
            "бизнес-задача принята",
            next_step="движение к brief",
        )
        action = "advise"

    return ThinkingBrief(
        **{
            **base.__dict__,
            "conversation_goal": "найти реальный путь к своему делу",
            "real_goal": "практическая опора, не мотивационная речь",
            "recommended_action": action,
            "confidence": 0.76,
            "best_response_strategy": ctx,
            "optional_question": optional,
        }
    )


def _correction_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    messages: list[dict[str, str]],
) -> ThinkingBrief:
    prior = _prior_user(messages)
    last = (messages[-1].get("content") or "").strip().lower() if messages else ""
    why = "Пользователь чувствует, что его не поняли — нужно вернуться к настоящему вопросу."
    if re.match(r"^нет\.?$", last) and len(last) < 12:
        why = (
            "Пользователь сказал «нет» — предыдущий ответ не подошёл. "
            "Признать это коротко, не спрашивать «уточните»."
        )
        ctx = _journey_ctx(
            "7. Правки и изменения",
            "предыдущий ответ не подошёл",
            next_step=f"вернуться к: {prior[:80]}" if prior else "попросить переформулировать",
        )
    elif prior and re.search(r"успеш|миллион|получ|стану", prior, re.I):
        why = "Ответили на бизнес/продукт вместо личного вопроса о будущем."
        ctx = _journey_ctx(
            "7. Правки и изменения",
            "сбой темы — личный вопрос",
            next_step="вернуться к исходному вопросу",
        )
    else:
        ctx = _journey_ctx(
            "7. Правки и изменения",
            "пользователь поправил ответ",
            next_step="исправить по существу",
        )

    return ThinkingBrief(
        **{
            **base.__dict__,
            "real_goal": "быть понятым по существу",
            "implicit_need": "извиниться и ответить на исходный вопрос",
            "recommended_action": "answer",
            "confidence": 0.88,
            "why": why,
            "best_response_strategy": ctx,
        }
    )


def _explain_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    state: ConversationState,
) -> ThinkingBrief:
    ctx = _journey_ctx(
        "Открытый диалог",
        "вопрос «почему» к предыдущему совету",
        next_step="объяснить логику на известных фактах",
    )
    if (
        state.country == "Россия"
        and state.budget_amount
        and state.budget_amount <= 50000
        and state.budget_currency == "RUB"
    ):
        ctx = _journey_ctx(
            "2. Понимание цели",
            "бюджет не покрывает полноценную кофейню",
            next_step="объяснить ограничение бюджета",
        )

    return ThinkingBrief(
        **{
            **base.__dict__,
            "real_goal": "понять логику предыдущего совета",
            "implicit_need": "прозрачность, не оправдания",
            "recommended_action": "teach",
            "confidence": 0.85,
            "best_response_strategy": ctx,
        }
    )


def _curiosity_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    last_user: str,
) -> ThinkingBrief:
    low = last_user.lower()
    conv = "вопрос по сути"
    if "factory" in low or "фабрик" in low:
        conv = "вопрос о Factory"
        ctx = _journey_ctx("Открытый диалог", "вопрос о продукте Factory", next_step="факты каталога")
    elif "studio" in low:
        conv = "вопрос о Virtus Studio"
        ctx = _journey_ctx("Открытый диалог", "вопрос о Studio", next_step="факт: в разработке")
    else:
        ctx = _journey_ctx("Открытый диалог", "нужно ясное объяснение", next_step="ответ по сути")
    return replace(
        base,
        conversation_goal=conv,
        real_goal="получить ясное объяснение",
        recommended_action="teach",
        best_response_strategy=ctx,
        confidence=0.8,
    )


def _emotional_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    last_user: str,
) -> ThinkingBrief:
    return ThinkingBrief(
        **{
            **base.__dict__,
            "real_goal": "быть услышанным",
            "implicit_need": "поддержка или конкретная помощь — по ситуации",
            "recommended_action": "comfort",
            "confidence": 0.8,
            "best_response_strategy": _journey_ctx(
                "Открытый диалог",
                "эмоциональная поддержка",
                next_step="короткая поддержка, без навязывания решений",
            ),
        }
    )


def _is_uncertain_domain(text: str) -> bool:
    low = text.lower()
    medical = (
        "диагноз",
        "болит",
        "боль",
        "симптом",
        "лекарств",
        "таблетк",
        "рак",
        "давлен",
        "аллерги",
        "беремен",
        "депресс",
        "простуд",
        "бессон",
        "витамин",
        "голов",
    )
    unanswerable = (
        "точно будет",
        "когда конец света",
        "что будет через 100 лет",
        "предскаж",
        "предсказ",
        "гарантируешь",
        "докажи",
        "однозначно",
        "бог существует",
    )
    return any(m in low for m in medical) or any(u in low for u in unanswerable)


def _uncertainty_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    last_user: str,
) -> ThinkingBrief:
    low = last_user.lower()
    is_medical = any(
        w in low for w in ("диагноз", "болит", "симптом", "лекарств", "таблетк", "рак", "давление")
    )
    ctx = _journey_ctx(
        "Открытый диалог",
        "домен с высокой неопределённостью",
        next_step="честные пределы знания",
    )
    if is_medical:
        ctx = _journey_ctx(
            "Открытый диалог",
            "медицинская тема",
            next_step="не диагноз; при серьёзных симптомах — врач",
        )
    return ThinkingBrief(
        **{
            **base.__dict__,
            "real_goal": "получить честный ответ без выдуманной уверенности",
            "implicit_need": "правда, а не авторитет",
            "confidence": 0.42,
            "recommended_action": "advise",
            "risks": ("ложная уверенность", "вредный совет"),
            "best_response_strategy": ctx,
            "avoid": base.avoid + ("диагноз", "гарантия", "100%"),
        }
    )


def _age_recall_brief(
    base: ThinkingBrief,
    state: ConversationState,
    memory: dict[str, Any] | None,
) -> ThinkingBrief:
    age = state.user_age
    if age:
        return ThinkingBrief(
            **{
                **base.__dict__,
                "conversation_goal": "вспомнить возраст из диалога",
                "real_goal": "вспомнить возраст из диалога",
                "known_facts": base.known_facts + (f"возраст: {age}",),
                "confidence": 0.95,
                "recommended_action": "answer",
                "best_response_strategy": _journey_ctx(
                    "Открытый диалог",
                    f"возраст {age} уже в контексте",
                    next_step="ответить фактом",
                ),
            }
        )
    return ThinkingBrief(
        **{
            **base.__dict__,
            "real_goal": "уточнить возраст",
            "confidence": 0.5,
            "recommended_action": "ask_one_question",
            "optional_question": "Вы ещё не говорили — сколько Вам лет?",
            "best_response_strategy": _journey_ctx(
                "2. Понимание цели",
                "возраст не записан",
                gap="возраст",
                next_step="один вопрос",
            ),
        }
    )


def _small_talk_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    last_user: str,
) -> ThinkingBrief:
    return ThinkingBrief(
        **{
            **base.__dict__,
            "conversation_goal": "свободная реплика",
            "real_goal": "ответ по сути",
            "implicit_need": "краткий ответ без проектов",
            "confidence": 0.85,
            "recommended_action": "answer",
            "best_response_strategy": _journey_ctx(
                "Открытый диалог",
                "свободная реплика",
                next_step="краткий ответ без услуг",
            ),
            "avoid": base.avoid + ("пакет", "тариф", "studio basic", "заказать сайт"),
        }
    )


def _factual_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    last_user: str,
) -> ThinkingBrief:
    return ThinkingBrief(
        **{
            **base.__dict__,
            "conversation_goal": goal.surface_topic or "вопрос по сути",
            "real_goal": "понять и объяснить",
            "implicit_need": "ясный ответ с рассуждением, не шаблон",
            "confidence": 0.78,
            "recommended_action": "advise" if len(last_user) > 40 else "answer",
            "best_response_strategy": _journey_ctx(
                "Открытый диалог",
                goal.surface_topic or "вопрос по сути",
                next_step="суть простыми словами",
            ),
        }
    )


def _apply_memory_inferences(
    base: ThinkingBrief,
    memory: dict[str, Any],
) -> ThinkingBrief:
    style = memory.get("preferred_depth")
    strategy = base.best_response_strategy
    if style == "brief":
        strategy += "; предпочтение: кратко"
    elif style == "deep":
        strategy += "; предпочтение: глубже"
    return ThinkingBrief(**{**base.__dict__, "best_response_strategy": strategy})


def _prior_user(messages: list[dict[str, str]]) -> str:
    users = [m.get("content") or "" for m in messages if m.get("role") == "user"]
    if len(users) >= 2:
        return users[-2]
    return users[0] if users else ""
