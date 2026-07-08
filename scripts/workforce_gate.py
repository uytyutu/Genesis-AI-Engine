#!/usr/bin/env python3
"""AI Workforce Manager gate — Employee Score routing + calibration learning."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("GENESIS_ACCEPTANCE_GATE", "1")

from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief  # noqa: E402
from app.integration.genesis_brain.workforce_manager import WorkforceManager  # noqa: E402
from app.integration.genesis_brain.workforce_performance import WorkforcePerformance  # noqa: E402
from app.integration.genesis_brain.providers import build_provider_registry  # noqa: E402


def test_classify_code() -> None:
    wm = WorkforceManager()
    t = wm.classify_task("исправь ошибку в python функции", ThinkingBrief())
    assert t == "code"


def test_classify_conversation() -> None:
    wm = WorkforceManager()
    t = wm.classify_task("Как думаешь, я стану успешным?", ThinkingBrief(confidence=0.7))
    assert t == "conversation"


def test_score_order_code_prefers_quality() -> None:
    wm = WorkforceManager()
    available = ["groq", "gemini", "anthropic", "genesis-local"]
    plan = wm.plan(
        "исправь ошибку в python",
        ThinkingBrief(),
        premium_allowed=True,
        available_employees=available,
    )
    assert plan.task == "code"
    assert plan.selected in ("anthropic", "groq", "gemini")
    assert plan.employee_order[0] == plan.selected
    assert plan.scores[0].employee_id == plan.selected


def test_score_order_conversation_prefers_groq() -> None:
    wm = WorkforceManager()
    available = ["groq", "gemini", "genesis-local"]
    plan = wm.plan(
        "Привет, как дела?",
        ThinkingBrief(confidence=0.8),
        premium_allowed=False,
        available_employees=available,
    )
    assert plan.task == "conversation"
    assert plan.employee_order[0] == "groq"
    assert "openai" not in plan.employee_order


def test_rating_updates_after_outcome() -> None:
    perf = WorkforcePerformance()
    before = perf.learned_quality("groq", "conversation")
    perf.record_outcome(
        "groq",
        "conversation",
        latency_ms=800,
        calibration_passed=True,
    )
    after = perf.learned_quality("groq", "conversation")
    daily = perf.daily_snapshot()
    assert daily.get("groq", {}).get("requests", 0) >= 1
    if before is not None and after is not None:
        assert after >= before


def test_registry_has_groq_slot() -> None:
    os.environ.pop("GENESIS_ACCEPTANCE_GATE", None)
    reg = build_provider_registry([])
    assert "groq" in reg
    assert "gemini" in reg
    assert "genesis-local" in reg


def main() -> int:
    tests = [
        ("classify_code", test_classify_code),
        ("classify_conversation", test_classify_conversation),
        ("score_order_code", test_score_order_code_prefers_quality),
        ("score_order_conversation", test_score_order_conversation_prefers_groq),
        ("rating_updates", test_rating_updates_after_outcome),
        ("registry", test_registry_has_groq_slot),
    ]
    ok = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
            ok += 1
        except Exception as exc:
            print(f"FAIL {name}: {exc}")
    print(f"\n{ok}/{len(tests)} PASS")
    return 0 if ok == len(tests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
