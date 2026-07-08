#!/usr/bin/env python3
"""
Runtime pipeline probe — prove ONE real message through Genesis Mind (not unit tests).

Usage:
  python scripts/runtime_pipeline_probe.py
  python scripts/runtime_pipeline_probe.py "How do you think I can become a millionaire?"
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.env_loader import load_local_env

load_local_env()

from app.integration.genesis_brain.brain import GenesisBrain  # noqa: E402

DEFAULT_MSG = "How do you think I can become a millionaire?"


def _bar(label: str) -> None:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}")


def main() -> int:
    question = " ".join(sys.argv[1:]).strip() or DEFAULT_MSG
    brain = GenesisBrain()

    _bar("RUNTIME PIPELINE PROBE")
    print(f"User message: {question}")

    result = brain.chat(
        system="Genesis public",
        messages=[{"role": "user", "content": question}],
        visitor_id="runtime-pipeline-probe",
        debug=True,
    )

    trace = result.trace or {}
    pipe = trace.get("runtime_pipeline") or {}

    _bar("1. THINKING BRIEF")
    print(pipe.get("thinking_brief") or trace.get("thinking_brief_text") or "(missing)")

    _bar("2. EMPLOYEE CHOSEN")
    print(f"Employee:  {pipe.get('employee_chosen')}")
    print(f"Model:     {pipe.get('employee_model')}")
    print(f"Why:       {pipe.get('employee_why')}")

    _bar("3. WHY CLOUD NOT USED (per employee)")
    for d in pipe.get("employee_diagnostics") or []:
        mark = "OK" if d.get("callable") else "NO"
        print(f"  [{mark}] {d.get('employee_id')}: {d.get('code')} — {d.get('reason')}")

    _bar("4. RAW PROMPT -> EMPLOYEE")
    raw = pipe.get("raw_prompt") or {}
    print("--- system (first 2000 chars) ---")
    print((raw.get("system") or "")[:2000])
    print("--- messages ---")
    for m in raw.get("messages") or []:
        role = m.get("role", "?")
        content = (m.get("content") or "")[:500]
        print(f"  [{role}] {content}...")

    _bar("5. RAW RESPONSE")
    print(pipe.get("raw_response") or "(empty — local/brief_speech path)")

    _bar("6. CALIBRATION")
    print(json.dumps(pipe.get("calibration") or {}, ensure_ascii=False, indent=2))

    _bar("7. FINAL RESPONSE")
    print(result.answer)

    _bar("CONVERSATION PIPELINE")
    for s in pipe.get("steps") or trace.get("conversation_pipeline") or []:
        print(f"  {s.get('step', '?')}: {s.get('status', '?')}")

    _bar("VERDICT")
    cloud = pipe.get("cloud_llm_used")
    src = pipe.get("answer_source")
    print(f"current_employee: {trace.get('current_employee')}")
    print(f"current_model:    {trace.get('current_model')}")
    print(f"current_provider: {trace.get('current_provider')}")
    print(f"answer_source:    {src}")
    print(f"cloud_llm_used:   {cloud}")
    if pipe.get("fallback_started_at"):
        print(f"fallback_started: {pipe.get('fallback_started_at')}")
    warn = pipe.get("local_fallback_warning")
    if warn:
        print(f"\n*** {warn} ***")
        print("FAIL: conversation did not use a cloud LLM.")
        print("Fix: connect free Groq or Gemini at /setup (Owner only)")
        return 1

    print("\nPASS: Cloud LLM was used for this message.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
