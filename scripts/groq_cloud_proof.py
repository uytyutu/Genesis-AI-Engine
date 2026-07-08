#!/usr/bin/env python3
"""
Groq/Gemini cloud proof — facts, not architecture.

Usage:
  python scripts/groq_cloud_proof.py
  python scripts/groq_cloud_proof.py --cloud-only   # 20 questions, local fallbacks OFF
  python scripts/groq_cloud_proof.py --one "Как думаешь, я стану успешным?"
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

# Never use acceptance gate for proof runs
os.environ.pop("GENESIS_ACCEPTANCE_GATE", None)

PROOF_QUESTION = "Как думаешь, я стану успешным?"

TWENTY_QUESTIONS = [
    "Как думаешь, я стану успешным?",
    "Как думаешь, стану миллионером?",
    "Мне плохо",
    "Как дела?",
    "Привет",
    "Что ты умеешь?",
    "Сколько стоит сайт?",
    "Хочу открыть бизнес",
    "У меня нет денег",
    "Расскажи анекдот",
    "Ты бот?",
    "Как научиться программировать?",
    "Помоги с маркетингом",
    "Я устал от работы",
    "Спасибо за помощь",
    "Нет, это не то",
    "Объясни квантовую физику простыми словами",
    "Какой смысл жизни?",
    "Погода сегодня хорошая",
    "Можешь написать стихотворение?",
]


def _bar(label: str) -> None:
    w = 72
    print(f"\n{'=' * w}\n{label}\n{'=' * w}")


def _run_chat(question: str, *, cloud_proof: bool, visitor_suffix: str = "") -> dict:
    if cloud_proof:
        os.environ["GENESIS_CLOUD_PROOF"] = "1"
    else:
        os.environ.pop("GENESIS_CLOUD_PROOF", None)

    # Fresh brain per mode so provider chain is rebuilt
    from app.integration.genesis_brain.brain import GenesisBrain

    brain = GenesisBrain()
    result = brain.chat(
        system="Genesis public",
        messages=[{"role": "user", "content": question}],
        visitor_id=f"cloud-proof-{visitor_suffix}",
        debug=True,
    )
    trace = result.trace or {}
    pipe = trace.get("runtime_pipeline") or {}
    raw = pipe.get("raw_response") or ""
    final = result.answer or ""
    return {
        "question": question,
        "thinking_brief": pipe.get("thinking_brief") or trace.get("thinking_brief_text") or "",
        "raw_prompt_system": (pipe.get("raw_prompt") or {}).get("system") or "",
        "raw_prompt_messages": (pipe.get("raw_prompt") or {}).get("messages") or [],
        "raw_response": raw,
        "draft_after_employee": pipe.get("draft_after_employee") or "",
        "after_calibration": pipe.get("after_calibration") or "",
        "final_response": final,
        "employee": pipe.get("employee_chosen"),
        "model": pipe.get("employee_model"),
        "answer_source": pipe.get("answer_source"),
        "cloud_llm_used": pipe.get("cloud_llm_used"),
        "used_brief_fallback": pipe.get("used_brief_speech_fallback"),
        "used_brief_rewrite": pipe.get("used_brief_speech_rewrite"),
        "fallback_started_at": pipe.get("fallback_started_at"),
        "diagnostics": pipe.get("employee_diagnostics") or [],
        "groq_wrote_text": bool(
            pipe.get("cloud_llm_used")
            and raw.strip()
            and pipe.get("answer_source") not in ("brief_speech", "genesis-local")
        ),
        "template_replaced_llm": bool(
            raw.strip()
            and final.strip()
            and raw.strip() != final.strip()
            and not pipe.get("used_brief_speech_rewrite")
        ),
    }


def _print_full_pipeline(row: dict) -> None:
    _bar("USER")
    print(row["question"])

    _bar("THINKING BRIEF (internal mandate → LLM, not shown to user)")
    print(row["thinking_brief"] or "(empty)")

    _bar("RAW PROMPT → GROQ/GEMINI (system — FULL)")
    print(row["raw_prompt_system"] or "(empty — cloud was NOT called)")

    _bar("RAW PROMPT → messages")
    print(json.dumps(row["raw_prompt_messages"], ensure_ascii=False, indent=2))

    _bar("RAW RESPONSE (before Personality / Calibration rewrite / Self Critique)")
    print(row["raw_response"] or "(empty)")

    _bar("AFTER CALIBRATION (draft path)")
    print(row["after_calibration"] or row["draft_after_employee"] or "(same as raw)")

    _bar("FINAL RESPONSE")
    print(row["final_response"])

    _bar("PROOF FIELDS")
    print(f"employee:              {row['employee']}")
    print(f"model:                 {row['model']}")
    print(f"answer_source:         {row['answer_source']}")
    print(f"cloud_llm_used:        {row['cloud_llm_used']}")
    print(f"used_brief_fallback:   {row['used_brief_fallback']}")
    print(f"used_brief_rewrite:    {row['used_brief_rewrite']}")
    print(f"fallback_started_at:   {row['fallback_started_at']}")
    print(f"groq_wrote_text:       {row['groq_wrote_text']}")
    print(f"personality_changed:   {row['template_replaced_llm']}")

    if row["raw_response"] and row["final_response"]:
        if row["raw_response"].strip() == row["final_response"].strip():
            print("\n→ RAW == FINAL (Groq text survived Personality)")
        elif row["used_brief_rewrite"] or row["used_brief_fallback"]:
            print("\n→ LOCAL brief_speech REPLACED cloud draft")
        elif row["template_replaced_llm"]:
            print("\n→ Personality/templates CHANGED cloud draft (e.g. greeting pool)")
        else:
            print("\n→ Minor post-process only")


def _print_diagnostics() -> None:
    from app.integration.genesis_brain.providers import build_provider_registry
    from app.integration.genesis_brain.provider_diagnostics import diagnose_workforce

    reg = build_provider_registry()
    diag = diagnose_workforce(reg, plan_order=list(reg.keys()), premium_ids=set())
    _bar("EMPLOYEE AVAILABILITY")
    for d in diag:
        mark = "OK" if d.get("callable") else "NO"
        print(f"  [{mark}] {d.get('employee_id')}: {d.get('code')} — {d.get('reason')}")


def main() -> int:
    args = sys.argv[1:]
    cloud_only = "--cloud-only" in args
    one_mode = "--one" in args
    if one_mode:
        idx = args.index("--one")
        question = args[idx + 1] if idx + 1 < len(args) else PROOF_QUESTION
    else:
        question = PROOF_QUESTION

    _print_diagnostics()

    if not cloud_only:
        _bar("PART A — NORMAL MODE (production path)")
        normal = _run_chat(question, cloud_proof=False, visitor_suffix="normal")
        _print_full_pipeline(normal)

    _bar("PART B — CLOUD PROOF MODE (brief_speech / greeting templates OFF)")
    print("GENESIS_CLOUD_PROOF=1 — Thinking → Groq → Personality (light) → Response")

    if one_mode and not cloud_only:
        cloud = _run_chat(question, cloud_proof=True, visitor_suffix="cloud")
        _print_full_pipeline(cloud)
        return 0 if cloud["groq_wrote_text"] else 1

    results: list[dict] = []
    for i, q in enumerate(TWENTY_QUESTIONS, 1):
        row = _run_chat(q, cloud_proof=True, visitor_suffix=f"q{i}")
        results.append(row)
        status = "GROQ" if row["groq_wrote_text"] else "NO_CLOUD"
        changed = "CHANGED" if row["template_replaced_llm"] else "same"
        print(
            f"{i:2}. [{status:8}] emp={row['employee'] or '?':18} "
            f"src={str(row['answer_source']):14} pers={changed:7} | {q[:40]}"
        )
        print(f"    → { (row['final_response'] or '')[:120] }")

    _bar("CLOUD PROOF SUMMARY (20 questions)")
    groq_count = sum(1 for r in results if r["groq_wrote_text"])
    brief_count = sum(1 for r in results if r["used_brief_fallback"] or r["used_brief_rewrite"])
    failed = sum(1 for r in results if not (r["final_response"] or "").strip())
    print(f"Groq/cloud wrote answer:     {groq_count}/20")
    print(f"brief_speech used:           {brief_count}/20")
    print(f"empty / failed:              {failed}/20")

    if groq_count == 0:
        print("\nVERDICT: Groq was NOT used — check API keys / diagnostics above.")
        return 1
    if groq_count == 20:
        print("\nVERDICT: All 20 answers came from cloud LLM (local fallbacks disabled).")
    else:
        print(f"\nVERDICT: Mixed — {groq_count} cloud, {20 - groq_count} without cloud.")

    # Save artifact
    out = ROOT / "scripts" / "groq_cloud_proof_last.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nFull JSON: {out}")
    return 0 if groq_count >= 15 else 1


if __name__ == "__main__":
    raise SystemExit(main())
