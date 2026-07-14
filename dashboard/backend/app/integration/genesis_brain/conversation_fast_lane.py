"""Conversation fast lane — LLM-only path without template substitution."""

from __future__ import annotations

import os

FAST_ROUTE_BUDGET_SEC = float(os.getenv("GENESIS_FAST_ROUTE_BUDGET_SEC", "14"))
FAST_MAX_CLOUD_ATTEMPTS = int(os.getenv("GENESIS_FAST_MAX_CLOUD_ATTEMPTS", "1"))
FAST_LANE_MAX_TURNS = 4
FAST_LANE_MAX_CONTEXT_CHARS = 700
FAST_LANE_MAX_SYSTEM_CHARS = 12000


def trim_messages_for_fast_lane(
    messages: list[dict[str, str]],
    *,
    max_turns: int = FAST_LANE_MAX_TURNS,
) -> list[dict[str, str]]:
    """Keep recent dialogue only — long threads slow Ollama prefill."""
    if not messages or max_turns <= 0:
        return list(messages)
    kept: list[dict[str, str]] = []
    turns = 0
    for msg in reversed(messages):
        kept.append(msg)
        if msg.get("role") == "user":
            turns += 1
            if turns >= max_turns:
                break
    kept.reverse()
    return kept


def cap_context_block(block: str, *, max_chars: int = FAST_LANE_MAX_CONTEXT_CHARS) -> str:
    text = (block or "").strip()
    if len(text) <= max_chars:
        return text
    return text[-max_chars:].lstrip()


def cap_system_prompt(system: str, *, max_chars: int = FAST_LANE_MAX_SYSTEM_CHARS) -> str:
    text = (system or "").strip()
    if len(text) <= max_chars:
        return text
    head = text[: int(max_chars * 0.35)].rstrip()
    tail = text[-int(max_chars * 0.6) :].lstrip()
    return f"{head}\n\n[…]\n\n{tail}"


def prioritize_local_provider(providers: list) -> list:
    """CEO path: local Ollama first — avoid cloud timeout eating the fast-lane budget."""
    local = [p for p in providers if getattr(p, "provider_id", "") == "genesis-local"]
    rest = [p for p in providers if p not in local]
    return local + rest


_COMPLEX_TASKS = frozenset(
    {
        "document_analysis",
        "code",
        "website",
        "business_plan",
        "execution",
        "premium",
    }
)


def should_use_conversation_fast_lane(
    *,
    has_attachments: bool,
    workforce_task: str | None,
    last_user: str,
) -> bool:
    """Most dialogue turns — skip Mind v3 pre-cycle, still call LLM."""
    if has_attachments:
        return False
    task = (workforce_task or "conversation").strip().lower()
    if task in _COMPLEX_TASKS:
        return False
    text = (last_user or "").strip()
    if not text or len(text) > 4000:
        return False
    return True
