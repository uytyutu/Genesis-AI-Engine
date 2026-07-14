#!/usr/bin/env python3
"""
Director Decision Audit — why Local vs LLM, per dialog class.

Usage:
  py scripts/director_decision_audit.py
  py scripts/director_decision_audit.py --beta-mode
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.integration.genesis_brain.brain import GenesisBrain
from app.integration.genesis_brain.brief_speech import clean_user_messages
from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.layers.emotional_intelligence import EmotionalIntelligenceLayer
from app.integration.genesis_brain.layers.executive_brain import GenesisExecutiveBrain
from app.integration.genesis_brain.layers.goal_analysis import GoalAnalysisLayer
from app.integration.genesis_brain.layers.thinking_engine import ThinkingEngine
from app.integration.genesis_brain.providers import build_provider_chain
from app.integration.genesis_brain.workforce_manager import WorkforceManager

SCENARIOS: list[tuple[str, str, list[dict[str, str]]]] = [
    ("greeting", "Привет", []),
    ("follow-up", "В смысле рад на связи?", [{"role": "assistant", "content": "Привет! Рад на связи."}]),
    ("factual", "Что там с погодой в Америке?", []),
    ("curiosity", "Почему Земля круглая?", []),
    ("meta", "Ты чего так общаешься?", [{"role": "assistant", "content": "Слушаю Вас — расскажите, что важнее."}]),
    ("business", "Хочу открыть кафе в Москве", []),
    ("product", "Сколько стоит лендинг под ключ?", []),
    ("emotional", "Мне сейчас очень грустно", []),
    ("slang", "Йо", []),
    ("correction", "Не тот вопрос", [{"role": "user", "content": "Стану ли успешным?"}, {"role": "assistant", "content": "Могу предложить сайт."}]),
]

CLOUD_IDS = ("groq", "gemini", "openrouter", "ollama", "openai", "anthropic", "deepseek")
FALLBACK_SNIPPET = "Слушаю Вас — расскажите"


@dataclass
class AuditRow:
    dialog_class: str
    real_goal: str
    conv_type: str
    exec_mode: str
    workforce_task: str
    director_selected: str
    director_top_score: float
    cloud_in_plan: bool
    actual_provider: str
    used_local_templates: bool
    should_prefer_llm: bool
    why_not_llm: str
    answer_preview: str


def _cloud_keys_present() -> bool:
    keys = (
        "GENESIS_GROQ_API_KEY",
        "GENESIS_GEMINI_API_KEY",
        "GENESIS_OPENROUTER_API_KEY",
        "GENESIS_LLM_API_KEY",
    )
    return any(os.getenv(k, "").strip() for k in keys)


def _available_employees(beta_mode: bool) -> list[str]:
    if beta_mode:
        return ["genesis-local"]
    chain = build_provider_chain()
    return [p.provider_id for p in chain if p.available()]


def _should_prefer_llm(dialog_class: str, real_goal: str) -> bool:
    if dialog_class in ("greeting", "slang"):
        return False
    if dialog_class in ("follow-up", "factual", "curiosity", "meta", "correction", "emotional"):
        return True
    if dialog_class in ("business", "product"):
        return True
    if real_goal in ("thread_follow_up", "curiosity", "factual_question", "correction", "emotional_need"):
        return True
    return True


def audit_turn(
    dialog_class: str,
    user_text: str,
    history: list[dict[str, str]],
    *,
    beta_mode: bool,
) -> AuditRow:
    messages = [*history, {"role": "user", "content": user_text}]
    clean = clean_user_messages(messages)
    last = user_text.strip()
    state = ConversationState.from_messages(clean)
    turn_index = sum(1 for m in clean if m.get("role") == "user")

    emotional = EmotionalIntelligenceLayer().analyze(last)
    thinking = ThinkingEngine().think(last_user=last, messages=clean, state=state, emotional=emotional)
    goal = GoalAnalysisLayer().analyze(last, clean, state, emotional)
    executive = GenesisExecutiveBrain()
    exec_brief = executive.decide(
        state=state,
        last_user=last,
        messages=clean,
        turn_index=turn_index,
        emotional=emotional,
    )
    decision = executive.decide_from_thinking(thinking, state=state, messages=clean, last_user=last)

    avail = _available_employees(beta_mode)
    plan = WorkforceManager().plan(
        last, thinking, executive_action=decision.action, available_employees=avail
    )
    top_score = plan.scores[0].total if plan.scores else 0.0
    cloud_in_plan = any(e in avail for e in CLOUD_IDS)

    brain = GenesisBrain()
    result = brain.chat(system="You are Vector.", messages=clean, visitor_id=f"audit-{dialog_class}")
    preview = (result.answer or "").replace("\n", " ")[:90]
    used_local = result.provider_id == "genesis-local"
    prefer_llm = _should_prefer_llm(dialog_class, goal.real_goal)

    why: list[str] = []
    if beta_mode or not cloud_in_plan:
        why.append("cloud employees not callable (no API keys on beta)")
    if used_local and prefer_llm:
        why.append("genesis-local = BriefSpeech → executive_reply/reasoned_human templates")
    if plan.task == "simple" and not beta_mode:
        why.append("WorkforceManager may classify as task=simple (short utterance)")
    if exec_brief.mode == "explain" and goal.real_goal in ("curiosity", "factual_question"):
        why.append("Executive explain mode can hijack before LLM (fixed in 5070db5)")
    if not why:
        why.append("routed to cloud" if not used_local else "local acceptable for class")

    return AuditRow(
        dialog_class=dialog_class,
        real_goal=goal.real_goal,
        conv_type=exec_brief.conversation_type,
        exec_mode=exec_brief.mode,
        workforce_task=plan.task,
        director_selected=plan.selected,
        director_top_score=top_score,
        cloud_in_plan=cloud_in_plan,
        actual_provider=result.provider_id,
        used_local_templates=used_local,
        should_prefer_llm=prefer_llm,
        why_not_llm="; ".join(why),
        answer_preview=preview,
    )


def print_table(rows: list[AuditRow], title: str) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print(f"{'=' * 72}")
    hdr = f"{'Class':<12} {'Goal':<18} {'Task':<14} {'Director':<14} {'Actual':<14} {'LLM?':<5} {'OK?':<4}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        ok = "yes" if (r.should_prefer_llm == (not r.used_local_templates)) or not r.should_prefer_llm else "NO"
        llm = "want" if r.should_prefer_llm else "skip"
        print(
            f"{r.dialog_class:<12} {r.real_goal:<18} {r.workforce_task:<14} "
            f"{r.director_selected:<14} {r.actual_provider:<14} {llm:<5} {ok:<4}"
        )
    print()
    for r in rows:
        print(f"--- {r.dialog_class} ---")
        print(f"  User: {SCENARIOS[[x[0] for x in SCENARIOS].index(r.dialog_class)][1]}")
        print(f"  Goal: {r.real_goal} | conv: {r.conv_type} | exec: {r.exec_mode}")
        print(f"  Director: {r.director_selected} (score {r.director_top_score:.1f}) | task: {r.workforce_task}")
        print(f"  Actual: {r.actual_provider} | prefer LLM: {r.should_prefer_llm}")
        print(f"  Why not LLM: {r.why_not_llm}")
        print(f"  Answer: {r.answer_preview}")
        if FALLBACK_SNIPPET in r.answer_preview:
            print("  ⚠ generic fallback detected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--beta-mode", action="store_true", help="Simulate beta (genesis-local only)")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    mode = "BETA (no cloud keys)" if args.beta_mode else f"LOCAL ENV (cloud keys: {_cloud_keys_present()})"

    rows = [audit_turn(cls, text, hist, beta_mode=args.beta_mode) for cls, text, hist in SCENARIOS]
    print_table(rows, f"Director Decision Audit — {mode}")

    # Policy summary
    print("\n" + "=" * 72)
    print("POLICY GAP SUMMARY")
    print("=" * 72)
    mismatches = [r for r in rows if r.should_prefer_llm and r.used_local_templates]
    print(f"Turns that SHOULD use LLM but used local: {len(mismatches)}/{len(rows)}")
    for r in mismatches:
        print(f"  - {r.dialog_class}: {r.why_not_llm}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
