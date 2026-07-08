"""
Communication Gate — intent-first context loading before any LLM call.

Genesis Communication Constitution Rule #1:
Answer the user's real intention first. Offer Genesis products only when appropriate.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.layers.conversation_type import (
    ConversationKind,
    classify_conversation_type,
    should_load_product_mind,
)

COMMUNICATION_CONSTITUTION = """## Genesis Communication Constitution

**Rule #1:** Always answer the user's real intention first.
Only after satisfying the request may Genesis offer its own products when appropriate.

**Order:** human companion → expert → Genesis consultant (only when the user asks about business, sites, bots, or automation).
"""


@dataclass(frozen=True)
class CommunicationGate:
    """Resolved per turn — controls what context reaches the LLM."""

    conversation_kind: ConversationKind
    product_mind: bool
    commercial_knowledge: bool
    confidence: float


def resolve_communication_gate(
    last_user: str,
    messages: list[dict[str, str]] | None = None,
    state: ConversationState | None = None,
) -> CommunicationGate:
    """Classify intent before loading Product Mind or commercial knowledge."""
    kind = classify_conversation_type(last_user, messages, state)
    commercial = should_load_product_mind(kind)
    confidence = 0.95 if commercial else 0.9
    if kind in ("emotional_support", "personal_reflection", "meta_correction"):
        confidence = 1.0
    return CommunicationGate(
        conversation_kind=kind,
        product_mind=commercial,
        commercial_knowledge=commercial,
        confidence=confidence,
    )
