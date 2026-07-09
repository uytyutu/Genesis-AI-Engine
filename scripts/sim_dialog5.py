#!/usr/bin/env python3
"""Offline simulation of acceptance dialog 5 — long coffee context."""

from __future__ import annotations

import io
import sys
import uuid
from collections import Counter

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
    "Привет, хочу открыть небольшую кофейню",
    "В Берлине",
    "Бюджет около 5000 евро",
    "Какие риски?",
    "А если бюджет только 2000?",
    "Что насчёт доставки кофе?",
    "Нужен ли сайт сразу?",
    "Сколько человек в команде минимум?",
    "Как привлечь первых клиентов?",
    "Соцсети или карты?",
    "А если аренда дорогая?",
    "Можно начать с coffee to go?",
    "Сколько месяцев до окупаемости — грубо?",
    "Что бы ты сделал на моём месте?",
    "Спасибо, это полезно",
    "Ещё один вопрос: нужна ли касса?",
    "Итого — с чего начать в первую неделю?",
]


def main() -> int:
    history: list[dict[str, str]] = []
    mem = GenesisMemoryLayer(None)
    vid = "d5-" + uuid.uuid4().hex[:8]
    answers: list[str] = []

    for msg in MESSAGES:
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
        ans = BriefSpeechSynthesizer().speak(
            thinking,
            decision,
            state=state,
            visitor_id=vid,
            turn_index=sum(1 for m in messages if m.get("role") == "user"),
            last_user=msg,
            messages=cleaned,
        )
        answers.append(ans.strip().lower())
        print(f"U: {msg}")
        if state.budget_amount:
            print(f"  budget: {state.budget_display()}")
        preview = ans.replace("\n", " | ")[:160]
        print(f"A: {preview}\n")
        history = messages + [{"role": "assistant", "content": ans}]

    repeat = len(answers) != len(set(answers))
    print("no_exact_repeats:", not repeat)
    if repeat:
        for text, count in Counter(answers).items():
            if count > 1:
                print(f"  DUP x{count}: {text[:100]}...")
    return 1 if repeat else 0


if __name__ == "__main__":
    raise SystemExit(main())
