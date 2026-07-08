"""
Fuzzy NLP — understand meaning despite typos. Never correct the user in replies.
"""

from __future__ import annotations

import re

from app.integration.genesis_brain.user_text_normalizer import normalize_user_text


def normalize_for_intent(text: str) -> str:
    """Normalize user text for intent matching — delegates to User Text Normalizer."""
    normalized = normalize_user_text(text)
    if not normalized:
        return ""
    return normalized.lower()


def contains_any(normalized: str, *patterns: str) -> bool:
    n = normalized.lower()
    return any(p in n for p in patterns)
