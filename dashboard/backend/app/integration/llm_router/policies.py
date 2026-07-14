"""
LLM Router policies — Rule #0: only the Router is designed, never a specific model.

Providers are interchangeable backends behind capabilities.
"""

from __future__ import annotations

from typing import Literal

from app.integration.llm_router.capabilities import (
    CAPABILITY_PRIORITY,
    LLMCapability,
    capability_chain,
    normalize_capability,
    task_to_capability,
)

RouterTask = Literal[
    "conversation",
    "simple",
    "code",
    "complex",
    "search",
    "sales",
    "document_analysis",
    "architecture",
    "reasoning",
]

CLOUD_EMPLOYEES = frozenset(
    {
        "groq",
        "gemini",
        "openai",
        "openrouter",
        "ollama",
        "anthropic",
        "deepseek",
    }
)

FREE_TIER_EMPLOYEES = frozenset({"groq", "gemini", "openrouter", "ollama"})

PREMIUM_EMPLOYEES = frozenset({"openai", "anthropic", "deepseek"})

EMERGENCY_ONLY = "genesis-local"

# Legacy alias — tasks map to capabilities internally.
TASK_PRIORITY = CAPABILITY_PRIORITY

_WORKFORCE_ALIASES: dict[str, str] = {
    "document_analysis": "analysis",
    "website": "coding",
    "business_plan": "analysis",
    "execution": "reasoning",
    "premium": "reasoning",
}


def normalize_task(task: str | None) -> str:
    """Workforce task label (backward compatible)."""
    key = (task or "conversation").strip().lower()
    if key in CAPABILITY_PRIORITY:
        return key
    mapped = _WORKFORCE_ALIASES.get(key)
    return mapped or key


def priority_chain(task: str | None, *, premium_allowed: bool = True) -> tuple[str, ...]:
    """Task → capability → provider chain."""
    cap = task_to_capability(task)
    return capability_chain(cap, premium_allowed=premium_allowed)


__all__ = [
    "CAPABILITY_PRIORITY",
    "CLOUD_EMPLOYEES",
    "EMERGENCY_ONLY",
    "FREE_TIER_EMPLOYEES",
    "LLMCapability",
    "PREMIUM_EMPLOYEES",
    "RouterTask",
    "capability_chain",
    "normalize_capability",
    "normalize_task",
    "priority_chain",
    "task_to_capability",
]
