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
    strategy = (
        "честно объяснить, что деньги — следствие ценности, не лотерея; "
        "не продавать продукты Genesis"
    )
    if goal.thread.mentioned_doubt:
        strategy += "; связать с ранее высказанным сомнением"
    if state.user_age and state.user_age <= 30:
        strategy += f"; учесть горизонт времени ({state.user_age} лет — ещё много итераций)"

    depth = (memory or {}).get("preferred_depth", "")
    if depth == "deep":
        strategy += "; ответ глубже, без воды"

    return ThinkingBrief(
        **{
            **base.__dict__,
            "conversation_goal": "изменить жизнь через финансы",
            "real_goal": "финансовая свобода и возможность изменить жизнь",
            "implicit_need": "наставник, который не обещает чудес",
            "emotional_state": "надежда",
            "confidence": 0.84,
            "recommended_action": "advise",
            "why": (
                "Слово «миллионер» часто означает не цифру на счёте, "
                "а желание свободы и контроля над своей жизнью."
            ),
            "risks": risks,
            "best_response_strategy": strategy,
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
            "best_response_strategy": (
                "поддержать без гарантий; говорить о системе и итерациях, не о «таланте»; "
                "не предлагать Factory/Studio"
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
    real = "контекст о себе — быть услышанным"
    strategy = "принять факт и связать с темой разговора"
    why = "Человек делится фактом о себе, ожидая, что его не проигнорируют."

    if age and (thread.mentioned_doubt or thread.mentioned_success):
        real = "человек переживает, что время уходит"
        why = (
            f"Возраст {age} в контексте сомнения об успехе — "
            "часто сигнал «успею ли я»."
        )
        strategy = (
            f"принять {age} лет; связать с ранее обсуждённым сомнением; "
            "не отвечать только «принял возраст»"
        )
    elif age and thread.mentioned_wealth:
        real = "добавляет контекст к разговору о будущем"
        strategy = f"связать {age} лет с горизонтом для финансовых целей"

    return ThinkingBrief(
        **{
            **base.__dict__,
            "real_goal": real,
            "why": why,
            "best_response_strategy": strategy,
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
    strategy = (
        "Product Mind: консультант — стек решений под нишу; "
        "два пути (под ключ / Studio); честно если подписка не нужна; "
        "не отправлять в разделы сайта"
    )
    optional = goal.optional_question
    if state.ready_for_business_advice():
        strategy = "дать конкретные направления с учётом страны и бюджета"
        action = "advise"
        optional = None
    elif state.life_goal == "family_time":
        strategy = "lean-модели с временем для семьи; упомянуть семью"
        action = "advise"
        optional = None
    elif not state.has_country() and not state.has_budget():
        strategy = "предложить три направления; не спрашивать страну первым делом"
        action = "advise"
        optional = None
    elif state.has_budget() and state.uncertain_niche:
        strategy = "подтвердить бюджет; один вопрос про формат"
        action = "ask_one_question" if goal.optional_question else "advise"
    elif state.missing_critical(messages):
        strategy = "один высокоценный вопрос, не допрос"
        action = "ask_one_question"
    else:
        action = "advise"

    return ThinkingBrief(
        **{
            **base.__dict__,
            "conversation_goal": "найти реальный путь к своему делу",
            "real_goal": "практическая опора, не мотивационная речь",
            "recommended_action": action,
            "confidence": 0.76,
            "best_response_strategy": strategy,
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
        strategy = (
            f"коротко признать ошибку; вернуться к вопросу: «{prior[:140]}»"
            if prior
            else "коротко признать ошибку; попросить переформулировать одним предложением"
        )
    elif prior and re.search(r"успеш|миллион|получ|стану", prior, re.I):
        why = "Ответили на бизнес/продукт вместо личного вопроса о будущем."
        strategy = "признать ошибку; вернуться к personal thread; не продавать"
    else:
        strategy = (
            "коротко признать ошибку; исправить ответ; 2–4 предложения; "
            "не «уточните» и не шаблон"
        )

    return ThinkingBrief(
        **{
            **base.__dict__,
            "real_goal": "быть понятым по существу",
            "implicit_need": "извиниться и ответить на исходный вопрос",
            "recommended_action": "answer",
            "confidence": 0.88,
            "why": why,
            "best_response_strategy": strategy,
        }
    )


def _explain_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    state: ConversationState,
) -> ThinkingBrief:
    strategy = "объяснить логику с опорой на известные факты"
    if (
        state.country == "Россия"
        and state.budget_amount
        and state.budget_amount <= 50000
        and state.budget_currency == "RUB"
    ):
        strategy = (
            "объяснить, почему кофейня не влезает в бюджет (аренда, оборудование); "
            "использовать слово «потому»"
        )

    return ThinkingBrief(
        **{
            **base.__dict__,
            "real_goal": "понять логику предыдущего совета",
            "implicit_need": "прозрачность, не оправдания",
            "recommended_action": "teach",
            "confidence": 0.85,
            "best_response_strategy": strategy,
        }
    )


def _curiosity_brief(
    base: ThinkingBrief,
    goal: GoalBrief,
    last_user: str,
) -> ThinkingBrief:
    low = last_user.lower()
    strategy = "объяснить доступно, без воды"
    conv = "понять как работает"
    if "factory" in low or "фабрик" in low:
        conv = "понять продукт Factory"
        strategy = "объяснить Factory; упомянуть Studio как альтернативу"
    elif "studio" in low:
        conv = "понять Virtus Studio"
        strategy = "объяснить Studio и подписку"
    return replace(
        base,
        conversation_goal=conv,
        real_goal="получить ясное объяснение",
        recommended_action="teach",
        best_response_strategy=strategy,
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
            "best_response_strategy": "сначала эмпатия; не торопиться с решениями",
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
    strategy = (
        "не притворяться всезнайкой; сказать «не могу утверждать наверняка» или "
        "«есть несколько точек зрения»; быть честным и полезным"
    )
    if is_medical:
        strategy += "; не ставить диагноз; рекомендовать врача при серьёзных симптомах"
    return ThinkingBrief(
        **{
            **base.__dict__,
            "real_goal": "получить честный ответ без выдуманной уверенности",
            "implicit_need": "правда, а не авторитет",
            "confidence": 0.42,
            "recommended_action": "advise",
            "risks": ("ложная уверенность", "вредный совет"),
            "best_response_strategy": strategy,
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
                "real_goal": "проверка памяти собеседника",
                "known_facts": base.known_facts + (f"возраст: {age}",),
                "confidence": 0.95,
                "recommended_action": "answer",
                "best_response_strategy": f"ответить прямо: Вам {age} лет; не спрашивать снова",
            }
        )
    return ThinkingBrief(
        **{
            **base.__dict__,
            "real_goal": "уточнить возраст",
            "confidence": 0.5,
            "recommended_action": "ask_one_question",
            "optional_question": "Вы ещё не говорили — сколько Вам лет?",
            "best_response_strategy": "честно сказать, что возраст не записан; один вопрос",
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
            "conversation_goal": "живой разговор",
            "real_goal": "человеческий контакт",
            "implicit_need": "услышать живого собеседника, не бота",
            "confidence": 0.85,
            "recommended_action": "answer",
            "best_response_strategy": (
                "1–2 коротких предложения + один вопрос о человеке; "
                "без «Добрый день, рад видеть»; не переводить на услуги"
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
            "best_response_strategy": (
                "сначала суть простыми словами; пример или аналогия; "
                "не «расскажите подробнее» без попытки ответить"
            ),
        }
    )


def _apply_memory_inferences(
    base: ThinkingBrief,
    memory: dict[str, Any],
) -> ThinkingBrief:
    style = memory.get("communication_style")
    if style == "brief":
        strategy = base.best_response_strategy + "; короткий ответ"
    elif style == "deep":
        strategy = base.best_response_strategy + "; больше глубины"
    else:
        strategy = base.best_response_strategy
    return ThinkingBrief(**{**base.__dict__, "best_response_strategy": strategy})


def _prior_user(messages: list[dict[str, str]]) -> str:
    users = [m.get("content") or "" for m in messages if m.get("role") == "user"]
    if len(users) >= 2:
        return users[-2]
    return users[0] if users else ""
