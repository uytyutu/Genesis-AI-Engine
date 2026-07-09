"""Natural replies for non-business conversation modes — Human Conversation v2."""

from __future__ import annotations

import hashlib
import re

from app.integration.genesis_brain.layers.conversation_state import ConversationState, pick_opening
from app.integration.genesis_brain.layers.conversation_type import ConversationKind
from app.integration.genesis_brain.public_brand import BRAND_NAME


def human_reply(
    kind: ConversationKind,
    raw: str,
    *,
    state: ConversationState,
    visitor_id: str,
    turn_index: int,
    messages: list[dict[str, str]] | None = None,
) -> str:
    """Wise companion — never sells unless user asked."""
    open_ = pick_opening(visitor_id, turn_index)
    low = raw.lower()

    if kind == "meta_correction":
        return _meta_correction(messages or [], open_)

    if kind == "personal_reflection":
        if re.search(r"миллионер|миллион|разбогат|богат", low):
            return _millionaire_reply(open_)
        if re.search(r"успеш|получится|получит|стану", low):
            return _success_reply(open_)
        return _success_reply(open_)

    if kind == "philosophy":
        return (
            f"{open_} Такие вопросы не имеют одного правильного ответа — "
            "и в этом их ценность.\n\n"
            "Смысл часто появляется не «где-то снаружи», а в том, что для Вас "
            "действительно важно: люди, дело, свобода, творчество."
        )

    if kind == "emotional_support":
        if re.search(r"плохо|тяжело|грустн|одинок", low):
            return (
                "Понимаю — бывает непросто.\n\n"
                "Если хотите — могу просто выслушать. "
                "Или поможем с чем-то конкретным, если так легче."
            )
        return (
            "Слышу Вас.\n\n"
            "Такие чувства нормальны — не обязательно сразу что-то решать."
        )

    if kind == "programming":
        if re.search(r"игр", low):
            return (
                f"{open_} С игрой можно начать с малого: один механик, один уровень, "
                "один цикл «играю → улучшаю».\n\n"
                "На чём хотите писать — Unity, Godot или web?"
            )
        return (
            f"{open_} Помогу с кодом.\n\n"
            "Опишите задачу одним предложением — язык и что должно получиться."
        )

    if kind == "creative":
        return (
            f"{open_} С удовольствием.\n\n"
            "Для кого текст, какой тон и примерная длина?"
        )

    if kind == "casual_conversation":
        return _casual(raw, visitor_id, turn_index)

    if kind == "general_question":
        return (
            f"{open_} Слушаю внимательно.\n\n"
            "Расскажите чуть подробнее — отвечу по существу."
        )

    return _casual(raw, visitor_id, turn_index)


def _success_reply(open_: str) -> str:
    return (
        f"{open_} Думаю, да — но не потому, что кто-то может это гарантировать.\n\n"
        "Успех редко приходит одним прыжком. Чаще это годы последовательных шагов, "
        "ошибок и упрямого возвращения к цели. Это качество встречается у людей, "
        "которые добиваются большого, гораздо чаще, чем «талант с неба».\n\n"
        "Миллионером или просто успешным — путь почти никогда не бывает быстрым. "
        "Гораздо важнее построить систему, которая приносит ценность людям."
    )


def _millionaire_reply(open_: str) -> str:
    return (
        f"{open_} Стать миллионером возможно — но деньги обычно следствие, а не цель.\n\n"
        "Они приходят, когда долго строишь что-то ценное для людей: продукт, компанию, "
        f"экспертизу. Если смотреть на то, что Вы уже создаёте — {BRAND_NAME} как раз может "
        "стать бизнесом, который к этому приведёт. Но путь длинный, и это нормально.\n\n"
        "Главное — не гнаться за цифрой, а за системой, которая её создаёт."
    )


def _meta_correction(messages: list[dict[str, str]], open_: str) -> str:
    topic = _prior_user_topic(messages)
    if topic and re.search(r"успеш|миллион|получ", topic, re.I):
        return (
            f"{open_} Вы правы — я неверно понял Ваш вопрос.\n\n"
            "Вы спрашивали не про сайт или бизнес-форму, а про своё будущее.\n\n"
            + _success_reply("").lstrip()
        )
    return (
        f"{open_} Вы правы — я ответил не на тот вопрос. Спасибо, что поправили.\n\n"
        "Давайте вернёмся к тому, о чём Вы спрашивали. Я слушаю."
    )


def _prior_user_topic(messages: list[dict[str, str]]) -> str:
    """Last user message before the correction (skip current)."""
    users = [m.get("content") or "" for m in messages if m.get("role") == "user"]
    if len(users) >= 2:
        return users[-2]
    return users[0] if users else ""


def _casual(raw: str, visitor_id: str, turn_index: int) -> str:
    low = raw.lower()
    if "как дела" in low or "как ты" in low or "как вы" in low:
        pool = [
            "Всё хорошо, спасибо! 😊 А у вас как?",
            "Отлично, на связи. Чем могу помочь сегодня?",
            "Нормально, спасибо что спросили. А вы как?",
        ]
    elif re.match(r"^(привет|здравствуй|hello|hi)\b", low):
        pool = [
            "Привет! Рад на связи — о чём думаете?",
            "Здравствуйте! Чем займёмся?",
            "Привет! С чего начнём?",
        ]
    else:
        pool = [
            "Слушаю. О чём хотите поговорить?",
            "Хорошо. Я здесь — продолжайте.",
            "Понял. Расскажите подробнее — отвечу по существу.",
        ]
    seed = f"{visitor_id}:{turn_index}:{raw[:30]}"
    idx = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(pool)
    return pool[idx]
