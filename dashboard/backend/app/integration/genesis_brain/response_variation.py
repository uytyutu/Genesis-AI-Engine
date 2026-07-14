"""
Response variation — pools removed (L8 Template Convergence).

Stable Vector voice: LLM generation + brief_speech offline paths only.
"""

from __future__ import annotations

_POOLS: dict[str, list[str]] = {}


class ResponseVariationEngine:
    """No random pools — returns empty so callers use LLM or brief_speech."""

    def pick(self, intent: str, visitor_id: str, message: str) -> str:
        return ""

    def vary(self, text: str, intent: str, visitor_id: str, salt: str = "") -> str:
        return (text or "").strip()
