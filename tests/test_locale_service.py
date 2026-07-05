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
