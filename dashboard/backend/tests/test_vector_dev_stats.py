"""Tests for Vector developer stats (debug mode)."""

from __future__ import annotations

from app.integration.vector_dev_stats import build_dev_stats, format_dev_stats_lines
from app.integration.vector_intelligence.pipeline import analyze_turn


def test_dev_stats_no_fallback_cloud():
    turn = analyze_turn("Привет")
    stats = build_dev_stats(
        turn_plan=turn,
        provider_id="groq",
        elapsed_sec=1.23,
        route={
            "chosen_employee": "groq",
            "chosen_model": "llama-3.3-70b-versatile",
            "cloud_llm_used": True,
            "used_brief_speech_fallback": False,
            "attempts": [
                {"employee_id": "groq", "outcome": "selected", "latency_sec": 1.1},
            ],
        },
    )
    assert stats["planner"] == "Open dialog"
    assert stats["journey_phase"] == "open_dialog"
    assert stats["worker"] == "groq"
    assert stats["elapsed_sec"] == 1.23
    assert stats["fallback_label"] == "нет"
    text = format_dev_stats_lines(stats)
    assert "Planner: Open dialog" in text
    assert "Fallback: нет" in text


def test_dev_stats_fallback_with_reasons():
    turn = analyze_turn("Как дела?")
    stats = build_dev_stats(
        turn_plan=turn,
        provider_id="genesis-local",
        elapsed_sec=1.1,
        route={
            "chosen_employee": "genesis-local",
            "cloud_llm_used": False,
            "used_brief_speech_fallback": True,
            "attempts": [
                {
                    "employee_id": "groq",
                    "outcome": "error",
                    "error": "HTTPStatusError: Client error '429 Too Many Requests'",
                },
                {
                    "employee_id": "gemini",
                    "outcome": "skipped",
                    "skip_code": "health",
                },
            ],
        },
        health_excluded=[
            {"employee_id": "openrouter", "reason": "payment_required"},
        ],
    )
    assert stats["fallback_label"] == "да"
    assert stats["reasons"]
    assert any("429" in r for r in stats["reasons"])
    text = format_dev_stats_lines(stats)
    assert "Fallback: да" in text
    assert "Причина:" in text
