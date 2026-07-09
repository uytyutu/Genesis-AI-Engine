"""
Reasoned human responses — generated from Goal Analysis + Executive reasoning.

Not category templates. Content follows implicit need and thread context.
"""

from __future__ import annotations

import hashlib
import re

from app.integration.genesis_brain.layers.conversation_state import ConversationState, pick_opening
from app.integration.genesis_brain.layers.executive_brain import ExecutiveBrief
from app.integration.genesis_brain.layers.goal_analysis import GoalBrief, HelpfulAction, RealGoal
from app.integration.genesis_brain.public_brand import BRAND_NAME


def reasoned_human_reply(
    goal: GoalBrief,
    executive: ExecutiveBrief,
    *,
    raw: str,
    state: ConversationState,
    visitor_id: str,
    turn_index: int,
    messages: list[dict[str, str]] | None = None,
) -> str:
    """Compose response from reasoning — not from conversation_type bucket."""
    open_ = pick_opening(visitor_id, turn_index)
    action = executive.helpful_action or goal.helpful_action

    if action == "close" or executive.mode == "close":
        return (
            "Рад был поговорить.\n\n"
            "Если захотите вернуться — продолжим с того места, где остановились."
        )

    if goal.real_goal == "correction" or executive.mode == "correct":
        return _correction_reply(goal, messages or [], open_)

    if goal.real_goal == "life_context":
        return _life_context_reply(goal, state, open_)

    if goal.real_goal == "doubt":
        return _doubt_reply(goal, state, open_, raw)

    if goal.real_goal == "future_vision":
        return _future_vision_reply(goal, state, open_, raw)

    if goal.real_goal == "emotional_need":
        return _emotional_reply(goal, open_, raw)

    if goal.real_goal == "business_intent" and goal.helpful_action == "acknowledge":
        return _business_ack_reply(state, open_)

    if goal.real_goal == "small_talk":
        return _small_talk_reply(raw, visitor_id, turn_index, open_)

    if goal.real_goal == "curiosity":
        return f"{open_} С удовольствием объясню.\n\n{_curiosity_stub(raw)}"

    if action == "one_question" and goal.optional_question:
        ack = _context_ack(state)
        return f"{open_} {ack}{goal.optional_question}".strip()

    return f"{open_} Слушаю Вас — расскажите, что для Вас сейчас важнее всего."


def _context_ack(state: ConversationState) -> str:
    if state.budget_display():
        return f"Бюджет **{state.budget_display()}** — принял. "
    if state.user_age:
        return f"{state.user_age} лет — принял. "
    if state.country:
        return f"{state.country} — учту. "
    return ""


def _doubt_reply(goal: GoalBrief, state: ConversationState, open_: str, raw: str) -> str:
    age_note = ""
    if state.user_age:
        age_note = (
            f" В {state.user_age} у Вас ещё длинный горизонт — "
            "и это реальное преимущество, не маркетинговая фраза."
        )

    anxious = goal.emotion == "anxious" or re.search(r"страш|боюсь", raw, re.I)
    if anxious:
        body = (
            "Сомнение — нормальная часть пути, особенно когда ставки кажутся высокими.\n\n"
            "Я не могу гарантировать результат — никто честный не может. "
            "Но могу сказать: люди, которые добиваются большого, чаще отличаются не талантом, "
            "а готовностью долго возвращаться к цели после ошибок."
        )
    else:
        body = (
            "Думаю, шансы есть — но не потому, что кто-то может это пообещать.\n\n"
            "Успех почти никогда не приходит одним прыжком. "
            "Чаще это годы маленьких шагов, ошибок и упрямого «ещё раз попробую». "
            "Это качество встречается у людей, которые строят что-то своё, "
            "гораздо чаще, чем «гениальность с неба»."
        )

    close = (
        "\n\nГораздо важнее не метка «успешный», "
        "а система, которая каждый день приближает Вас к тому, что для Вас значит успех."
    )
    return f"{open_} {body}{age_note}{close}"


def _future_vision_reply(
    goal: GoalBrief, state: ConversationState, open_: str, raw: str
) -> str:
    age = state.user_age
    horizon = ""
    if age and age <= 30:
        horizon = (
            f" В {age} лет у Вас есть то, чего нет у многих — "
            "время на эксперименты и обучение без спешки «уже поздно»."
        )
    elif age:
        horizon = f" В {age} — всё ещё достаточно времени, если строить системно."

    thread_note = ""
    if goal.thread.mentioned_doubt:
        thread_note = (
            "\n\nВы раньше сомневались — и это нормально. "
            "Амбиция и сомнение часто идут рядом у тех, кто реально что-то строит."
        )

    body = (
        "Стать миллионером возможно — но деньги обычно следствие, а не цель.\n\n"
        "Они приходят, когда долго создаёте ценность: продукт, компанию, экспертизу, "
        "реputation. Цифра на счёте — итог, а не руль."
        f"{horizon}{thread_note}\n\n"
        f"Если смотреть на то, что Вы уже делаете — {BRAND_NAME}, идеи, проекты — "
        "это как раз тип пути, где можно построить систему, а не гнаться за лотереей."
    )
    return f"{open_} {body}"


def _life_context_reply(goal: GoalBrief, state: ConversationState, open_: str) -> str:
    age = state.user_age
    theme = goal.thread.dominant_theme()

    if age and theme == "doubt":
        return (
            f"{open_} {age} — хороший возраст, чтобы сомневаться и всё равно пробовать.\n\n"
            "Вы спрашивали о своих шансах — при таком горизонте времени "
            "имеет смысл думать не «получится ли разом», а «что я готов строить 5–10 лет». "
            "Это другой разговор, и он обычно честнее."
        )

    if age and theme == "future":
        return (
            f"{open_} Записал: Вам {age}.\n\n"
            "На фоне разговора о будущем и деньгах это важная деталь — "
            "у Вас ещё много итераций, чтобы найти своё дело и масштабировать его. "
            "Не нужно успеть всё к тридцати."
        )

    if age:
        return (
            f"{open_} {age} — принял.\n\n"
            "Если хотите — свяжем это с тем, о чём говорили, или начнём новую тему."
        )

    return (
        f"{open_} Понял — это про Вас, не отдельный вопрос.\n\n"
        "Расскажите, если хотите продолжить мысль."
    )


def _correction_reply(
    goal: GoalBrief, messages: list[dict[str, str]], open_: str
) -> str:
    prior = _prior_user(messages)
    if prior and re.search(r"успеш|миллион|получ|стану", prior, re.I):
        return (
            f"{open_} Вы правы — я неверно понял.\n\n"
            "Вы спрашивали не про сайт или бизнес-форму, а про своё будущее и себя.\n\n"
            "Если коротко: шансы есть, когда цель ясна и Вы готовы долго учиться и пробовать. "
            "Это не гарантия — это честная логика тех, кто добивается большого."
        )
    return (
        f"{open_} Вы правы — ответил не на тот вопрос. Спасибо, что поправили.\n\n"
        "Давайте вернёмся к тому, о чём Вы спрашивали."
    )


def _emotional_reply(goal: GoalBrief, open_: str, raw: str) -> str:
    if re.search(r"плохо|тяжело|грустн|одинок", raw, re.I):
        return (
            f"{open_} Понимаю — бывает непросто.\n\n"
            "Не обязательно сразу что-то решать. "
            "Могу просто выслушать — или помочь с чем-то конcretным, если так легче."
        )
    return (
        f"{open_} Слышу Вас.\n\n"
        "Такие чувства нормальны. Если захотите — разберём, что за ними стоит."
    )


def _business_ack_reply(state: ConversationState, open_: str) -> str:
    ack = _context_ack(state).strip()
    if state.uncertain_niche and state.has_budget():
        return (
            f"{open_} {ack}\n\n"
            "Что ближе — работа с людьми лично (кафе, салон, сервис) "
            "или онлайн (обучение, digital)?"
        ).strip()
    if ack:
        return f"{open_} {ack}\n\nПродолжим — что для Вас важнее сейчас?"
    return f"{open_} Принял. Расскажите, что для Вас важнее сейчас?"


def _small_talk_reply(raw: str, visitor_id: str, turn_index: int, open_: str) -> str:
    low = raw.lower()
    elif "как дела" in low or "как ты" in low or "как вы" in low:
        variants = [
            "Всё хорошо, спасибо! 😊 А у вас как?",
            "Отлично, на связи. Чем могу помочь?",
            "Нормально, спасибо что спросили. А вы как?",
        ]
    elif re.match(r"^(привет|здравствуй|hello|hi)\b", low):
        variants = [
            "Привет! Рад на связи — о чём думаете?",
            "Здравствуйте! Чем займёмся?",
            "Привет! С чего начнём?",
        ]
    else:
        variants = [
            "Слушаю вас. О чём хотите поговорить?",
            "Хорошо. Продолжайте — я здесь.",
        ]
    seed = f"{visitor_id}:{turn_index}:{raw[:20]}"
    idx = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(variants)
    return variants[idx]


def _curiosity_stub(raw: str) -> str:
    low = raw.lower()
    if "factory" in low or "фабрик" in low:
        return (
            f"**Factory** — продуктовый отдел {BRAND_NAME}: сайты, боты, приложения под ключ.\n\n"
            "Спросите, если нужен лендинг под ключ — /order."
        )
    return "Опишите, что именно хотите понять — отвечу доступно, без воды."


def _prior_user(messages: list[dict[str, str]]) -> str:
    users = [m.get("content") or "" for m in messages if m.get("role") == "user"]
    if len(users) >= 2:
        return users[-2]
    return users[0] if users else ""
