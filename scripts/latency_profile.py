"""One-off latency profiler for Vector fast lane — not shipped."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dashboard" / "backend"))

from app.env_loader import load_local_env

load_local_env()

import httpx

from app.integration.genesis_brain.brain import GenesisBrain
from app.integration.genesis_brain.communication_presets import resolve_effective_style, style_llm_block
from app.integration.genesis_brain.conversation_rhythm import rhythm_instruction
from app.integration.genesis_brain.layers.emotional_intelligence import EmotionalIntelligenceLayer
from app.integration.genesis_brain.layers.knowledge import GenesisKnowledgeLayer
from app.integration.genesis_brain.layers.memory import GenesisMemoryLayer
from app.integration.genesis_brain.layers.personality import GenesisPersonalityLayer
from app.integration.genesis_brain.layers.conversation_state import ConversationStateLayer
from app.integration.genesis_brain.layers.product_mind import product_mind_llm_rules
from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME
from app.integration.locale_service import assistant_llm_language_hint
from app.integration.provider_health_service import probe_providers, viable_cloud_employees

q = "Почему Virtus Core отличается от ChatGPT?"
messages = [{"role": "user", "content": q}]
visitor = "latency-profile"
mem_dir = Path(__file__).resolve().parents[1] / "dashboard" / "backend" / "memory"

brain = GenesisBrain(memory_dir=mem_dir)
personality = GenesisPersonalityLayer(mode="public")
memory = GenesisMemoryLayer(mem_dir)
conv = ConversationStateLayer(memory)
knowledge = GenesisKnowledgeLayer()
emotion = EmotionalIntelligenceLayer()

memory.observe_messages(visitor, messages)
conv_state = conv.process(visitor, messages)
memory_block = memory.build_context_block(visitor)
knowledge_block = knowledge.build_block()
state_block = conv_state.to_prompt_block()
inferences = memory.get_inferences(visitor)
style = resolve_effective_style(None, q, inferences)
emotional = emotion.analyze(q)

base_system = getattr(brain, "_system", "") or ""
parts = {
    "personality_block": len(personality.personality_block()),
    "knowledge_block": len(knowledge_block),
    "memory_block": len(memory_block),
    "state_block": len(state_block),
    "base_system": len(base_system),
}

full = personality.wrap_system(
    base_system=base_system,
    knowledge_block=knowledge_block,
    memory_block=memory_block,
    emotional_hint=emotion.to_prompt_hint(emotional),
)
if state_block:
    full += "\n\n" + state_block
full += (
    f"\n\n[{BRAND_NAME} — Vector]\n"
    f"Вы — {ASSISTANT_NAME}. Один голос для клиента. Отвечайте естественно, как современный AI.\n"
    f"{assistant_llm_language_hint('ru', ASSISTANT_NAME, BRAND_NAME)}\n"
    f"{style_llm_block(style)}\n"
    f"{rhythm_instruction(q)}\n"
    + product_mind_llm_rules()
)
parts["full_system_total"] = len(full)

print("=== PROMPT SIZES (chars) ===")
for key, val in parts.items():
    print(f"  {key}: {val}")

t0 = time.perf_counter()
vc = viable_cloud_employees(mem_dir)
print(f"viable_cloud_employees: {round(time.perf_counter() - t0, 3)}s -> {vc}")

t0 = time.perf_counter()
probe_providers(memory_dir=mem_dir, force=True)
print(f"probe_providers(force): {round(time.perf_counter() - t0, 3)}s")

for max_tok in (400, 800, 1200):
    payload = {
        "model": "llama3.2",
        "messages": [
            {"role": "system", "content": full[:12000]},
            {"role": "user", "content": q},
        ],
        "temperature": 0.75,
        "max_tokens": max_tok,
    }
    t0 = time.perf_counter()
    res = httpx.post(
        "http://127.0.0.1:11434/v1/chat/completions",
        json=payload,
        timeout=120,
    )
    print(
        f"ollama direct (sys={min(len(full), 12000)}, max_tokens={max_tok}): "
        f"{round(time.perf_counter() - t0, 2)}s status={res.status_code}"
    )

t0 = time.perf_counter()
result = brain.chat(
    system=base_system,
    messages=messages,
    visitor_id=visitor,
    workforce_task="conversation",
    debug=True,
)
elapsed = time.perf_counter() - t0
ans_len = len(result.answer or "")
print(f"full brain.chat: {round(elapsed, 2)}s provider={result.provider_id} answer_len={ans_len}")
route = result.dev_route or {}
for attempt in route.get("attempts") or []:
    emp = attempt.get("employee_id")
    outcome = attempt.get("outcome")
    lat = attempt.get("latency_ms")
    err = (attempt.get("error") or "")[:80]
    print(f"  attempt {emp} {outcome} {lat}ms {err}")
