"""Language Constitution — post-generation speech integrity."""

from __future__ import annotations

from app.integration.genesis_brain.language_constitution import (
    apply_language_constitution,
    is_translation_request,
    resolve_response_locale,
)


def test_resolve_locale_from_user_message_not_ui():
    assert resolve_response_locale(user_message="Hello, what is the status?", ui_locale="ru") == "en"
    assert resolve_response_locale(user_message="Как дела?", ui_locale="en") == "ru"
    assert resolve_response_locale(user_message="Guten Tag, wie geht es?", ui_locale="ru") == "de"


def test_apply_removes_foreign_slips_for_russian_user():
    raw = "Да, могу помочь. Gracias! I'm glad you asked."
    out = apply_language_constitution(raw, user_message="Нужен сайт")
    assert "gracias" not in out.lower()
    assert "i'm glad" not in out.lower()
    assert "могу помочь" in out.lower()


def test_apply_skips_scrub_on_translation_request():
    raw = "Hello world — это перевод."
    out = apply_language_constitution(
        raw,
        user_message="Переведи на английский: привет мир",
    )
    assert out == raw


def test_is_translation_request_detects_common_phrases():
    assert is_translation_request("Переведи этот текст на немецкий")
    assert is_translation_request("Translate this to Russian")
    assert not is_translation_request("Нужен сайт для кафе")


def test_keeps_technical_names():
    raw = "Vector на Virtus Core использует Python и HTML."
    out = apply_language_constitution(raw, user_message="Расскажи про стек")
    assert "Vector" in out
    assert "Python" in out
    assert "HTML" in out
