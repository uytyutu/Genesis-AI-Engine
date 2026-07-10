"""Routing — thread follow-up and substantive curiosity (offline beta)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.integration.genesis_brain.brief_speech import clean_user_messages
from app.integration.genesis_brain.brain import GenesisBrain


def _chat(messages: list[dict]) -> str:
    brain = GenesisBrain()
    result = brain.chat(system="You are Vector.", messages=clean_user_messages(messages), visitor_id="test-routing")
    return (result.answer or "").strip()


def test_thread_follow_up_after_greeting():
    messages = [
        {"role": "assistant", "content": "Привет! Рад на связи."},
        {"role": "user", "content": "В смысле рад на связи?"},
    ]
    answer = _chat(messages)
    assert "Слушаю Вас" not in answer
    assert "рад начать разговор" in answer.lower() or "имел в виду" in answer.lower()


def test_curiosity_earth_not_generic_stub():
    messages = [
        {"role": "assistant", "content": "Привет!"},
        {"role": "user", "content": "Ну объясни почему земля круглая?"},
    ]
    answer = _chat(messages)
    assert "Опишите, что именно хотите понять" not in answer
    assert "земл" in answer.lower() or "гравитац" in answer.lower() or "сфер" in answer.lower()


def test_weather_america_not_listen_fallback():
    messages = [{"role": "user", "content": "Что там в Америке с погодой?"}]
    answer = _chat(messages)
    assert "Слушаю Вас — расскажите, что для Вас сейчас важнее всего" not in answer
