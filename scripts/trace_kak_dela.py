#!/usr/bin/env python3
"""Trace «Как дела?» through pipeline — draft must survive finalize + critique."""

from __future__ import annotations

import io
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.integration.genesis_brain.brain import GenesisBrain
from app.integration.genesis_brain.layers import GenesisPersonalityLayer, GenesisSelfCritiqueLayer
from app.integration.genesis_brain.layers.conversation_style import ConversationStyleEngine
from app.integration.genesis_brain.response_variation import _POOLS

_BANNED_TEMPLATE_MARKERS = (
    "на связи. давайте поговорим",
    "чем могу помочь сегодня?",
    "отлично, на связи. чем могу помочь",
)


def _is_template_pool_line(text: str) -> bool:
    norm = " ".join((text or "").lower().split())
    for pool in _POOLS.values():
        for line in pool:
            pooled = " ".join(line.lower().split())
            if pooled == norm or (len(norm) > 24 and norm in pooled):
                return True
    return any(m in norm for m in _BANNED_TEMPLATE_MARKERS)


def _norm(text: str) -> str:
    return " ".join((text or "").split())


def main() -> int:
    visitor_id = "trace-kak-dela"
    user_msg = "Как дела?"
    messages = [{"role": "user", "content": user_msg}]
    brain = GenesisBrain()
    result = brain.chat(system="You are Vector.", messages=messages, visitor_id=visitor_id)

    personality = GenesisPersonalityLayer(mode="public")
    critique = GenesisSelfCritiqueLayer()
    style = ConversationStyleEngine()

    # Simulate offline draft (what BriefSpeech produces without cloud)
    offline_draft = (
        "Всё хорошо, спасибо что спросили!\n\n"
        "А у вас как? Что на уме сегодня?"
    )
    after_finalize = personality.finalize(
        offline_draft,
        messages=messages,
        visitor_id=visitor_id,
        cloud_llm_used=False,
    )
    intent = brain._reasoning.analyze(messages, {}).intent
    after_critique = critique.polish(
        after_finalize,
        intent=intent,
        messages=messages,
        visitor_id=visitor_id,
        provider_id="genesis-local",
        cloud_llm_used=False,
    )

    print("=== TRACE: «Как дела?» ===")
    print(f"provider: {result.provider_id}")
    print(f"offline draft:\n  {offline_draft}")
    print(f"after personality.finalize:\n  {after_finalize}")
    print(f"after self_critique.polish:\n  {after_critique}")
    print(f"brain.chat final:\n  {result.answer}")
    print()
    print(f"offline draft preserved in finalize: {_norm(offline_draft) == _norm(after_finalize)}")
    print(f"finalize preserved in critique: {_norm(after_finalize) == _norm(after_critique)}")
    pool_pick = style.pick_small_talk(style.build_context({}, visitor_id), user_msg)
    print(f"finalize != pick_small_talk: {_norm(after_finalize) != _norm(pool_pick)}")
    print(f"pick_small_talk (old path) would be: {pool_pick}")
    print(f"final looks like canned pool: {_is_template_pool_line(result.answer)}")
    ok = (
        _norm(offline_draft) == _norm(after_finalize)
        and _norm(after_finalize) == _norm(after_critique)
        and _norm(after_finalize) != _norm(pool_pick)
        and "на связи. давайте поговорим" not in after_finalize.lower()
    )
    print(f"\nPASS: {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
