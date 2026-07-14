"""
Communication Gate — Journey-first context loading before any LLM call.

Controls what context reaches the model — not how Vector speaks.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.layers.conversation_type import (
    ConversationKind,
    should_load_commercial_knowledge,
    should_load_product_mind,
)
from app.integration.vector_intelligence.pipeline import analyze_turn
from app.integration.vector_intelligence.types import JourneyPhase

# Deleted: Communication Constitution role ladder (companion → expert → consultant).
# Journey phase from pipeline is the single behavior source.


@dataclass(frozen=True)
class CommunicationGate:
    """Resolved per turn — controls what context reaches the LLM."""

    conversation_kind: ConversationKind
    journey_phase: JourneyPhase
    product_mind: bool
    commercial_knowledge: bool
    confidence: float


def resolve_communication_gate(
    last_user: str,
    messages: list[dict[str, str]] | None = None,
    state: ConversationState | None = None,
) -> CommunicationGate:
    """Journey-first gate — load commerce/product context only when the phase requires it."""
    _ = state
    history = messages[:-1] if messages and len(messages) > 1 else messages
    plan = analyze_turn(last_user, history=history)
    kind = plan.conversation_kind
    journey = plan.journey_phase

    work_phase = journey not in ("open_dialog",)
    product = work_phase and should_load_product_mind(kind)
    commercial = work_phase and should_load_commercial_knowledge(kind)
    confidence = 0.95 if commercial else 0.9
    if journey == "open_dialog":
        confidence = 1.0
    elif kind in ("emotional_support", "personal_reflection", "meta_correction"):
        confidence = 1.0

    return CommunicationGate(
        conversation_kind=kind,
        journey_phase=journey,
        product_mind=product,
        commercial_knowledge=commercial,
        confidence=confidence,
    )
