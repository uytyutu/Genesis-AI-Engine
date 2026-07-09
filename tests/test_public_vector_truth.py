"""Truth Pass Stage 2 — public Vector wired to mission1 truth catalog."""

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.layers.knowledge import GenesisKnowledgeLayer
from app.integration.genesis_brain.reasoned_reply import reasoned_business_reply
from app.integration.genesis_core_intelligence import build_core_system_prompt
from app.integration.public_truth_catalog import (
    build_mission1_vector_commerce_rules,
    load_public_pricing_display,
)

_PACKAGES = [
    {"id": "basic", "name": "Landing Basic", "price_eur": 350, "deliverables": []},
    {"id": "business", "name": "Landing Business", "price_eur": 650, "deliverables": []},
    {"id": "premium", "name": "Landing Premium", "price_eur": 1200, "deliverables": []},
]


def test_load_public_pricing_display_uses_truth_catalog():
    data = load_public_pricing_display()
    assert data["version"].startswith("mission1-truth")
    assert data["subscriptions"][0]["id"] == "free"


def test_knowledge_layer_no_legacy_studio_prices():
    block = GenesisKnowledgeLayer(_PACKAGES).build_block()
    low = block.lower()
    assert "49 €/мес" not in block
    assert "basic 49" not in low
    assert "350" in block
    assert "в разработке" in low


def test_system_prompt_mission1_commerce():
    prompt = build_core_system_prompt(_PACKAGES)
    low = prompt.lower()
    assert "49 €/мес" not in prompt
    assert "basic — **49" not in low
    assert "350" in prompt
    assert "в разработке" in low


def test_reasoned_studio_honest():
    state = ConversationState()
    state.wants_studio = True
    state.goal = "open_business"
    out = reasoned_business_reply(state, "Хочу Genesis Studio", visitor_id="t1")
    assert out is not None
    assert "разработк" in out.lower()
    assert "49" not in out


def test_mission1_commerce_rules_block():
    block = build_mission1_vector_commerce_rules(_PACKAGES)
    assert "350 €" in block
    assert "650 €" in block
    assert "1200 €" in block
    assert "недоступн" in block.lower() or "разработк" in block.lower()
