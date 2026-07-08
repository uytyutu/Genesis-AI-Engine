#!/usr/bin/env python3
"""
Mind Pipeline Gate — verify Genesis Mind v3 controls LLM, not the reverse.

Checks:
1. Thinking Brief mandate is built with memory + executive decision
2. Brief is injected into LLM messages (not raw user-only)
3. Full pipeline runs: Think → LLM/local → Calibrate → Personality
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("GENESIS_ACCEPTANCE_GATE", "1")

from app.integration.genesis_brain.brain import GenesisBrain  # noqa: E402
from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief  # noqa: E402


def test_mandate_structure() -> None:
    brief = ThinkingBrief(
        conversation_goal="финансовая свобода",
        real_goal="поддержка при сомнении",
        implicit_need="услышать честный наставник",
        emotional_state="сомнение",
        known_facts=("Age: 27",),
        best_response_strategy="честная поддержка без штампов",
    )
    mandate = brief.to_llm_mandate(
        executive_action="comfort",
        executive_confidence=0.82,
        memory_inferences={
            "long_term_goals": ["создать AI-компанию"],
            "communication_style": "прямой, уважительный",
        },
        personality="Genesis",
    )
    for needle in (
        "THINKING BRIEF",
        "Age: 27",
        "Long goals",
        "Implicit Need",
        "Executive Decision",
        "comfort",
        "language cortex",
    ):
        assert needle in mandate, f"missing in mandate: {needle}"


def test_llm_message_injection() -> None:
    messages = [
        {"role": "user", "content": "Привет"},
        {"role": "assistant", "content": "Здравствуйте."},
        {"role": "user", "content": "Как думаешь, я стану успешным?"},
    ]
    mandate = "THINKING BRIEF\nImplicit Need: поддержка"
    wrapped = GenesisBrain._build_llm_messages(messages, mandate)
    assert len(wrapped) == 3
    last = wrapped[-1]["content"]
    assert "GENESIS MIND" in last
    assert "THINKING BRIEF" in last
    assert "User message:" in last
    assert "успешным" in last
    assert wrapped[0]["content"] == "Привет"


def test_full_pipeline_debug() -> None:
    brain = GenesisBrain()
    result = brain.chat(
        system="Test",
        messages=[{"role": "user", "content": "Как думаешь, я стану успешным?"}],
        visitor_id="mind-pipeline-gate",
        debug=True,
    )
    assert result.answer.strip(), "empty answer"
    assert result.trace is not None
    assert result.trace.get("brief_injected_into_llm") is True
    brief = result.trace.get("thinking_brief") or {}
    assert brief.get("implicit_need") or brief.get("real_goal")
    pipeline = result.trace.get("pipeline") or []
    assert "HumanCalibration" in str(pipeline)
    assert "GenesisPersonalityLayer" in str(pipeline)


def main() -> int:
    tests = [
        ("mandate_structure", test_mandate_structure),
        ("llm_message_injection", test_llm_message_injection),
        ("full_pipeline_debug", test_full_pipeline_debug),
    ]
    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
            passed += 1
        except Exception as exc:
            print(f"FAIL {name}: {exc}")
    print(f"\n{passed}/{len(tests)} PASS")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
