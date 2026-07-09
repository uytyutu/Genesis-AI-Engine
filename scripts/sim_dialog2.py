#!/usr/bin/env python3
"""Offline simulation of acceptance dialog 2 — business consulting."""

from __future__ import annotations

import io
import sys
import uuid

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, "dashboard/backend")

from app.integration.genesis_brain.brief_speech import BriefSpeechSynthesizer, clean_user_messages
from app.integration.genesis_brain.layers.conversation_state import ConversationStateLayer
from app.integration.genesis_brain.layers.emotional_intelligence import EmotionalIntelligenceLayer
from app.integration.genesis_brain.layers.executive_brain import GenesisExecutiveBrain
from app.integration.genesis_brain.layers.memory import GenesisMemoryLayer
from app.integration.genesis_brain.layers.thinking_engine import ThinkingEngine

MESSAGES = [
    "Хочу открыть бизнес.",
    "Посоветуй идеи.",
    "Почему именно эти?",
    "У меня бюджет 1000 евро.",
]


def main() -> int:
    history: list[dict[str, str]] = []
    mem = GenesisMemoryLayer(None)
    vid = "d2-" + uuid.uuid4().hex[:8]

    for i, msg in enumerate(MESSAGES, 1):
        messages = history + [{"role": "user", "content": msg}]
        cleaned = clean_user_messages(messages)
        state = ConversationStateLayer(mem).process(vid, cleaned)
        em = EmotionalIntelligenceLayer().analyze(msg)
        thinking = ThinkingEngine().think(
            last_user=msg,
            messages=cleaned,
            state=state,
            emotional=em,
            memory_inferences={},
        )
        decision = GenesisExecutiveBrain().decide_from_thinking(
            thinking, state=state, messages=cleaned, last_user=msg
        )
        brief = getattr(decision, "brief", decision)
        ans = BriefSpeechSynthesizer().speak(
            thinking,
            decision,
            state=state,
            visitor_id=vid,
            turn_index=i,
            last_user=msg,
            messages=cleaned,
        )
        print(f"Turn {i} U: {msg}")
        print(f"  mode={getattr(brief, 'mode', '?')} ctx={state.has_business_context()} advise={state.ready_for_advise_mode()}")
        print(f"  A: {ans[:220].replace(chr(10), ' | ')}\n")
        history = messages + [{"role": "assistant", "content": ans}]

  # acceptance consultant_ideas: turns 2-3
    t2 = history[3]["content"] if len(history) > 3 else ""
    t3 = history[5]["content"] if len(history) > 5 else ""
    ok = any(
        "направлен" in t.lower() or "иде" in t.lower() or "**1." in t
        for t in (t2, t3)
    )
    print("consultant_ideas (turns 2-3):", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
