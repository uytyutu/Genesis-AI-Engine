"""G3.1 — Evolution Center: AI Support & Continuous Improvement.

Canon rule: AI may recommend changes. Only the Owner approves changes.
G3.1 never auto-applies code, prices, or platform behaviour.
"""

from __future__ import annotations

from app.evolution.analyzer import analyze_support_message
from app.evolution.service import EvolutionSupportService

ENGINE_ID = "g31_evolution_support_v1"

__all__ = [
    "ENGINE_ID",
    "EvolutionSupportService",
    "analyze_support_message",
]
