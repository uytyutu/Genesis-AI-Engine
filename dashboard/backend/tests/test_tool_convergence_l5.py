"""L5 — Tool Convergence: knowledge facts only, product mind next-step only."""

from __future__ import annotations

from app.integration.genesis_brain.layers.knowledge import GenesisKnowledgeLayer
from app.integration.genesis_brain.layers.product_mind import product_mind_llm_rules

_PACKAGES = [
    {"id": "basic", "name": "Landing Basic", "price_eur": 350, "deliverables": []},
    {"id": "business", "name": "Landing Business", "price_eur": 650, "deliverables": []},
    {"id": "premium", "name": "Landing Premium", "price_eur": 1200, "deliverables": []},
]

_BEHAVIOR_MARKERS = (
    "как продавать",
    "консультирует, не продаёт",
    "примеры тона",
    "нужный тон",
    "product mind — разговор",
    "полезность > выручка",
    "не говорить:",
    "platform_directive",
    "голос vector",
    "руководитель проектов",
    "мотивация:",
    "ai-помощник",
)


def test_knowledge_block_facts_only():
    block = GenesisKnowledgeLayer(_PACKAGES).build_block()
    low = block.lower()
    assert "каталог" in low and "(факты)" in low
    assert "350" in block
    assert "в разработке" in low
    for marker in _BEHAVIOR_MARKERS:
        assert marker not in low, f"behavior marker found: {marker}"


def test_knowledge_no_dialogue_examples():
    block = GenesisKnowledgeLayer(_PACKAGES).build_block()
    assert "Ответь своими словами" not in block
    assert "живо, без шаблонов" not in block


def test_knowledge_no_mission1_commerce_rules_duplicate():
    """Full commerce rules belong in core prompt — not duplicated in knowledge."""
    block = GenesisKnowledgeLayer(_PACKAGES).build_block()
    assert "универсальная модель услуг (единая правда)" not in block.lower()


def test_product_mind_rules_next_step_only():
    rules = product_mind_llm_rules()
    low = rules.lower()
    assert "следующий шаг" in low or "следующего шага" in low
    assert "руководитель проектов" not in low
    assert "мотивация" not in low
    assert "продажа — не задача" not in low
    assert "не каталог и не продажа" in low
    assert "350" in rules


def test_product_mind_rules_compact():
    assert len(product_mind_llm_rules()) < 500
