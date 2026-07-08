#!/usr/bin/env python3
"""
Workforce Reality Gate — Genesis cannot claim PASS until Workforce is proven in Dev Mode.

Verifies debug trace contains full workforce_reality:
  chosen employee, score, latency, why, not_chosen, calibration, second_pass.
Also proves escalation: dry answer → calibration fail → next employee.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("GENESIS_ACCEPTANCE_GATE", "1")

from app.integration.genesis_brain.brain import GenesisBrain  # noqa: E402
from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief  # noqa: E402
from app.integration.genesis_brain.types import ChatResult  # noqa: E402
from app.integration.genesis_brain.workforce_manager import WorkforceManager  # noqa: E402

REALITY_KEYS = (
    "chosen_employee",
    "chosen_score",
    "chosen_latency_sec",
    "why_chosen",
    "not_chosen",
    "attempts",
    "second_pass",
    "escalation_count",
    "final_calibration",
    "emotional_mood",
    "thinking_implicit_need",
)


class _MockEmployee:
    def __init__(self, provider_id: str, answer: str) -> None:
        self.provider_id = provider_id
        self._answer = answer

    def available(self) -> bool:
        return True

    def chat(self, **kwargs: object) -> ChatResult:
        return ChatResult(answer=self._answer, provider_id=self.provider_id)


def _assert_reality(trace: dict) -> None:
    reality = trace.get("workforce_reality")
    assert isinstance(reality, dict), "missing workforce_reality block"
    for key in REALITY_KEYS:
        assert key in reality, f"workforce_reality missing: {key}"
    assert reality["chosen_employee"], "empty chosen_employee"
    assert isinstance(reality["not_chosen"], list), "not_chosen must be list"
    assert isinstance(reality["attempts"], list), "attempts must be list"
    cal = reality["final_calibration"]
    assert isinstance(cal, dict) and "passed" in cal, "final_calibration invalid"
    assert "reasons" in cal, "calibration reasons missing"


def test_emotional_message_reality() -> None:
    """«Я сегодня очень переживаю» — emotion → brief → workforce → calibration."""
    brain = GenesisBrain()
    result = brain.chat(
        system="Genesis public",
        messages=[{"role": "user", "content": "Я сегодня очень переживаю"}],
        visitor_id="workforce-reality-gate",
        debug=True,
    )
    assert result.answer.strip(), "empty answer"
    assert result.trace is not None
    _assert_reality(result.trace)
    reality = result.trace["workforce_reality"]
    mood = reality.get("emotional_mood") or result.trace.get("emotional_mood")
    assert mood, "emotion not detected"
    brief = result.trace.get("thinking_brief") or {}
    assert brief.get("implicit_need") or brief.get("real_goal") or brief.get("emotional_state"), (
        "Thinking Brief not built"
    )
    assert result.trace.get("brief_injected_into_llm") is True


def test_escalation_second_pass() -> None:
    """Dry first employee → calibration fail → second employee wins."""
    brain = GenesisBrain()
    wm = WorkforceManager()
    thinking = ThinkingBrief(
        real_goal="эмоциональная поддержка при тревоге",
        implicit_need="услышать что переживания нормальны и его не осудят",
        emotional_state="тревога",
        recommended_action="comfort",
        confidence=0.75,
    )
    plan = wm.plan(
        "Я сегодня очень переживаю",
        thinking,
        available_employees=["mock-dry", "mock-good"],
    )
    dry = _MockEmployee("mock-dry", "Ок.")
    good = _MockEmployee(
        "mock-good",
        "Понимаю, что сейчас непросто. Переживания в такой ситуации естественны — "
        "вы не один, и то, что вы об этом говорите, уже важный шаг.",
    )
    decision = SimpleNamespace(action="comfort", confidence=0.8)
    _result, draft, needs_rewrite, fallback, route_log = brain._route_providers(
        "system",
        [{"role": "user", "content": "Я сегодня очень переживаю"}],
        thinking_brief=thinking,
        executive_decision=decision,
        providers=[dry, good],
        workforce_plan=plan,
        conversation_messages=[{"role": "user", "content": "Я сегодня очень переживаю"}],
        available_employees=["mock-dry", "mock-good"],
    )
    assert route_log.chosen_employee == "mock-good", route_log.to_dict()
    assert route_log.second_pass is True, "expected second_pass after escalation"
    assert route_log.escalation_count >= 1
    escalated = [a for a in route_log.attempts if a.outcome == "escalated"]
    assert len(escalated) >= 1, route_log.to_dict()
    assert draft.strip()
    assert needs_rewrite is False


def test_not_chosen_explained() -> None:
    brain = GenesisBrain()
    result = brain.chat(
        system="Genesis",
        messages=[{"role": "user", "content": "Привет, как настроение?"}],
        visitor_id="workforce-reality-not-chosen",
        debug=True,
    )
    assert result.trace
    reality = result.trace["workforce_reality"]
    scores = result.trace.get("workforce_scores") or []
    if len(scores) > 1:
        assert len(reality["not_chosen"]) >= 1
        row = reality["not_chosen"][0]
        assert row.get("employee_id")
        assert row.get("why")


def main() -> int:
    tests = [
        ("emotional_reality", test_emotional_message_reality),
        ("escalation_second_pass", test_escalation_second_pass),
        ("not_chosen_explained", test_not_chosen_explained),
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
    if passed == len(tests):
        print("\nWorkforce Reality: proven in Dev Mode trace.")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
