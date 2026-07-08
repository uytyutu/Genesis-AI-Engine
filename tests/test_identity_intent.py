"""Identity intent detection and Virtus Core / Vector brand replies."""

import pytest

from app.integration.genesis_brain.ai_identity import (
    ASSISTANT_NAME,
    BRAND_NAME,
    INTERNAL_CORE_NAME,
    UNIVERSAL_AI_IDENTITY,
    compose_identity_reply,
    scrub_identity_violations,
    try_local_identity_reply,
)
from app.integration.genesis_brain.identity_intent import IdentityIntent, detect_identity_intent

_IDENTITY_THREAD = [
    {"role": "user", "content": "Кто ты?"},
    {
        "role": "assistant",
        "content": (
            "Я — Vector, интеллектуальный ИИ-помощник платформы Virtus Core.\n"
            "Я помогаю искать информацию, создавать проекты."
        ),
    },
]


@pytest.mark.parametrize(
    "phrase",
    [
        "Кто ты?",
        "ты кто",
        "кто ты такой",
        "кто ты вообще",
        "что ты",
        "что ты такое?",
        "Чем ты занимаешься?",
        "чем занимаешся",
        "Что ты умеешь?",
        "Расскажи о себе",
        "раскажи о себе",
        "Расскажи немного о себе",
        "Представься",
        "Представь себя",
        "Откуда ты?",
        "Как ты появился?",
        "Кто тебя создал?",
        "Кто тебя сделал?",
        "Для чего ты создан?",
        "Чем можешь помочь?",
        "Какие у тебя возможности?",
        "Что ты можешь делать?",
        "В чем твоя задача?",
        "Какова твоя цель?",
        "Что ты из себя представляешь?",
        "Кто со мной сейчас разговаривает?",
        "Кто отвечает мне?",
        "Что это за система?",
        "Что это за ИИ?",
        "Ты искусственный интеллект?",
        "Ты чат-бот?",
        "Ты программа?",
        "Зачем ты существуешь?",
        "Чем ты отличаешься от других ИИ?",
        "Как тебя зовут?",
        "Что такое Virtus Core?",
        "Что такое Genesis?",
        "А ты вообще кто такой?",
        "Genesis — это ты?",
        "Ты человек?",
        "Ты нейросеть?",
        "Что это за программа?",
        "Как тебя зовут полностью?",
        "Почему такое название?",
        "Чем Vector отличается от Genesis?",
        "Чем Vector отличается от Virtus Core?",
        "Почему Genesis?",
        "Кем ты создан?",
        "Зачем тебя создали?",
        "Как называется этот ИИ?",
    ],
)
def test_identity_intent_detects_natural_phrasings(phrase: str):
    assert detect_identity_intent(phrase) is not None


@pytest.mark.parametrize(
    "phrase",
    [
        "Кто такой Томас Шелби?",
        "Кто такой Наполеон?",
        "Какая погода в Москве?",
        "Напиши код на Python",
        "Исправь ошибку в программе",
    ],
)
def test_identity_intent_not_triggered_for_other_topics(phrase: str):
    assert detect_identity_intent(phrase) is None


@pytest.mark.parametrize(
    "follow_up,expected_kind",
    [
        ("А чем занимаешься?", "help"),
        ("А что умеешь?", "capabilities"),
        ("А кто тебя сделал?", "creator"),
        ("А когда ты появился?", "origin"),
        ("Какие у тебя возможности?", "capabilities"),
        ("А Genesis тогда что?", "genesis"),
        ("А чем Virtus Core отличается?", "vector_vs_virtus"),
        ("А почему тебя так зовут?", "why_name"),
    ],
)
def test_identity_follow_up_in_thread(follow_up: str, expected_kind: str):
    messages = _IDENTITY_THREAD + [{"role": "user", "content": follow_up}]
    intent = detect_identity_intent(follow_up, messages=messages)
    assert intent is not None
    assert intent.is_follow_up
    assert intent.kind == expected_kind


def test_brand_who_are_you_reply():
    reply = try_local_identity_reply("Кто ты?")
    assert reply
    assert ASSISTANT_NAME in reply
    assert BRAND_NAME in reply
    assert "crm" not in reply.lower()
    assert "studio" not in reply.lower()
    assert "groq" not in reply.lower()


def test_brand_name_reply():
    reply = try_local_identity_reply("Как тебя зовут?")
    assert reply == f"Меня зовут {ASSISTANT_NAME}."


def test_brand_virtus_core_reply():
    reply = try_local_identity_reply("Что такое Virtus Core?")
    assert reply
    assert BRAND_NAME in reply
    assert ASSISTANT_NAME in reply


def test_brand_genesis_reply():
    reply = try_local_identity_reply("Что такое Genesis?")
    assert reply
    assert INTERNAL_CORE_NAME in reply
    assert ASSISTANT_NAME in reply
    assert "внутренн" in reply.lower()


def test_brand_creator_reply():
    reply = try_local_identity_reply("Кто тебя создал?")
    assert reply
    assert BRAND_NAME in reply
    assert "groq" not in reply.lower()


def test_capabilities_list():
    reply = try_local_identity_reply("Что ты умеешь?")
    assert reply
    assert "•" in reply
    assert "программированием" in reply.lower()


def test_identity_prompt_brand_roles():
    low = UNIVERSAL_AI_IDENTITY.lower()
    assert "virtus core" in low
    assert "vector" in low
    assert "genesis" in low
    assert "внутренн" in low


def test_scrub_identity_violations():
    bad = "Я — цифровой собеседник на Groq через OpenRouter."
    out = scrub_identity_violations(bad)
    assert "groq" not in out.lower()
    assert "openrouter" not in out.lower()


def test_compose_reply_varies_by_kind():
    who = compose_identity_reply(IdentityIntent(kind="who_are_you", confidence=0.9))
    cap = compose_identity_reply(IdentityIntent(kind="capabilities", confidence=0.9))
    assert who != cap
    assert ASSISTANT_NAME in who
    assert "•" in cap


def test_brand_genesis_is_you_reply():
    reply = try_local_identity_reply("Genesis — это ты?")
    assert reply
    assert "нет" in reply.lower()
    assert "Vector" in reply
    assert "внутренн" in reply.lower()


def test_brand_program_reply():
    reply = try_local_identity_reply("Что это за программа?")
    assert reply
    assert "Virtus Core" in reply
    assert "Vector" in reply


def test_brand_speaker_reply():
    reply = try_local_identity_reply("Кто со мной разговаривает?")
    assert reply
    assert "Сейчас с вами" in reply or "с вами разговаривает" in reply.lower()
    assert "Vector" in reply


def test_public_brand_signature():
    from app.integration.genesis_brain.public_brand import brand_signature_text

    sig = brand_signature_text()
    assert "Vector" in sig
    assert "Virtus Core" in sig


def test_follow_up_help_not_repeat_full_intro():
    messages = _IDENTITY_THREAD + [{"role": "user", "content": "А чем занимаешься?"}]
    reply = try_local_identity_reply("А чем занимаешься?", messages=messages)
    assert reply
    assert BRAND_NAME in reply
    assert reply.count(ASSISTANT_NAME) <= 2
