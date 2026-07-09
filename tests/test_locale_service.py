"""Locale detection tests."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.integration.locale_service import (  # noqa: E402
    assistant_response_locale,
    detect_locale_from_text,
    effective_chat_locale,
)


def test_detect_russian():
    assert detect_locale_from_text("Что мне делать дальше?") == "ru"


def test_detect_german():
    assert detect_locale_from_text("Hallo, was soll ich tun?") == "de"


def test_detect_arabic():
    assert detect_locale_from_text("مرحبا كيف الحال") == "ar"


def test_effective_prefers_message_over_ui():
    assert effective_chat_locale("ru", "Hello, what is the status?") == "en"


def test_assistant_fallback_for_unpacked_locale():
    assert assistant_response_locale("fr", "Bonjour") == "en"


def test_resolve_assistant_locale_explicit():
    from app.integration.locale_service import resolve_assistant_locale

    assert resolve_assistant_locale("en", ui_locale="de") == "en"
    assert resolve_assistant_locale(None, ui_locale="de", legacy_locale="en") == "en"


def test_assistant_llm_language_hint_english():
    from app.integration.locale_service import assistant_llm_language_hint

    hint = assistant_llm_language_hint("en", "Vector", "Virtus Core")
    assert "English" in hint
    assert "Vector" in hint
