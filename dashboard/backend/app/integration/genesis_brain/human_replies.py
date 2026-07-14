"""Substantive offline replies for non-business modes — no chatbot pools."""

from __future__ import annotations

import re

from app.integration.genesis_brain.layers.conversation_state import ConversationState
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
) -> str | None:
    """Substantive content only — None lets LLM / brief_speech handle the turn."""
    low = raw.lower()

    if kind == "meta_correction":
        return _meta_correction(messages or [])

    if kind == "personal_reflection":
        if re.search(r"миллионер|миллион|разбогат|богат", low):
            return _millionaire_reply()
        if re.search(r"успеш|получится|получит|стану", low):
            return _success_reply()
        return _success_reply()

    if kind == "philosophy":
        return (
            "Такие вопросы не имеют одного правильного ответа — "
            "и в этом их ценность.\n\n"
            "Смысл часто появляется в том, что для Вас "
            "действительно важно: люди, дело, свобода, творчество."
        )

    return None


def _success_reply() -> str:
    return (
        "Думаю, да — но не потому, что кто-то может это гарантировать.\n\n"
        "Успех редко приходит одним прыжком. Чаще это годы последовательных шагов, "
        "ошибок и упрямого возвращения к цели.\n\n"
        "Гораздо важнее построить систему, которая приносит ценность людям."
    )


def _millionaire_reply() -> str:
    return (
        "Стать миллионером возможно — но деньги обычно следствие, а не цель.\n\n"
        "Они приходят, когда долго строишь что-то ценное для людей: продукт, компанию, "
        f"экспертизу. {BRAND_NAME} может стать частью такого пути — но он длинный, "
        "и это нормально.\n\n"
        "Главное — не гнаться за цифрой, а за системой, которая её создаёт."
    )


def _meta_correction(messages: list[dict[str, str]]) -> str:
    topic = _prior_user_topic(messages)
    if topic and re.search(r"успеш|миллион|получ", topic, re.I):
        return (
            "Вы правы — я неверно понял Ваш вопрос.\n\n"
            "Вы спрашивали не про сайт или бизнес-форму, а про своё будущее.\n\n"
            + _success_reply()
        )
    return (
        "Вы правы — я ответил не на тот вопрос. Спасибо, что поправили.\n\n"
        "Вернёмся к исходному вопросу."
    )


def _prior_user_topic(messages: list[dict[str, str]]) -> str:
    users = [m.get("content") or "" for m in messages if m.get("role") == "user"]
    if len(users) >= 2:
        return users[-2]
    return users[0] if users else ""
