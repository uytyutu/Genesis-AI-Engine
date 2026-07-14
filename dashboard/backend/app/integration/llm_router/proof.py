"""Reproducible architecture proof — pin provider via env, no code changes."""

from __future__ import annotations

import os

from app.config import is_development
from app.integration.llm_router.policies import CLOUD_EMPLOYEES

_VALID = frozenset(CLOUD_EMPLOYEES) | {"genesis-local"}


def proof_provider_pin() -> str | None:
    """
    GENESIS_LLM_PROOF_PROVIDER=groq|gemini|ollama|openrouter|...

    Development only. Forces Router primary for reproducible Architecture Proof.
    Example: «Сегодня тестируем через Gemini» — set env, restart backend, no code edit.
    """
    if not is_development():
        return None
    raw = os.getenv("GENESIS_LLM_PROOF_PROVIDER", "").strip().lower()
    if raw in _VALID:
        return raw
    return None


def proof_provider_label() -> str | None:
    pin = proof_provider_pin()
    if not pin:
        return None
    return f"architecture_proof:{pin}"
