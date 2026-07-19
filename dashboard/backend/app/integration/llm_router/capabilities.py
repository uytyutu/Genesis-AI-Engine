"""
LLM Capabilities — Rule #0: Virtus Core routes by capability, not by vendor.

Pipeline (stable):
  Vector → Identity → Memory → Planner → LLM Router → Capability → Provider (swappable)

The bottom layer changes (Groq today, GPT-6 tomorrow). Router and capabilities do not.
"""

from __future__ import annotations

from typing import Literal

LLMCapability = Literal[
    "conversation",
    "coding",
    "analysis",
    "reasoning",
    "search",
]

# Provider order per capability — vendor-agnostic; any registered backend may serve.
CAPABILITY_PRIORITY: dict[str, tuple[str, ...]] = {
    "conversation": (
        "groq",
        "gemini",
        "openrouter",
        "ollama",
        "openai",
        "anthropic",
        "deepseek",
    ),
    "coding": (
        "groq",
        "gemini",
        "openrouter",
        "ollama",
        "deepseek",
        "openai",
        "anthropic",
    ),
    "analysis": (
        "gemini",
        "groq",
        "openrouter",
        "ollama",
        "openai",
        "anthropic",
        "deepseek",
    ),
    "reasoning": (
        "gemini",
        "groq",
        "openrouter",
        "ollama",
        "deepseek",
        "openai",
        "anthropic",
    ),
    "search": (
        "gemini",
        "groq",
        "openrouter",
        "ollama",
        "openai",
        "anthropic",
        "deepseek",
    ),
}

PREMIUM_EMPLOYEES = frozenset({"openai", "anthropic", "deepseek", "kimi"})

_TASK_TO_CAPABILITY: dict[str, LLMCapability] = {
    "conversation": "conversation",
    "simple": "conversation",
    "sales": "conversation",
    "code": "coding",
    "website": "coding",
    "document_analysis": "analysis",
    "complex": "reasoning",
    "architecture": "reasoning",
    "reasoning": "reasoning",
    "search": "search",
    "business_plan": "analysis",
    "execution": "reasoning",
    "premium": "reasoning",
}


def normalize_capability(raw: str | None) -> LLMCapability:
    key = (raw or "conversation").strip().lower()
    if key in CAPABILITY_PRIORITY:
        return key  # type: ignore[return-value]
    mapped = _TASK_TO_CAPABILITY.get(key)
    if mapped:
        return mapped
    return "conversation"


def task_to_capability(task: str | None) -> LLMCapability:
    """Planner task → LLM capability (stable abstraction)."""
    return normalize_capability(task)


def capability_chain(
    capability: str | None,
    *,
    premium_allowed: bool = True,
) -> tuple[str, ...]:
    norm = normalize_capability(capability)
    chain = CAPABILITY_PRIORITY[norm]
    if premium_allowed:
        return chain
    return tuple(e for e in chain if e not in PREMIUM_EMPLOYEES)
