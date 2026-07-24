"""Sanitize outbound commercial API payloads — never expose Virtus core internals."""

from __future__ import annotations

from typing import Any

_STRIP_KEYS = frozenset(
    {
        "engine_id",
        "ENGINE_ID",
        "memory_dir",
        "prompt",
        "system_prompt",
        "raw_html",
        "debug",
        "traceback",
        "stack",
        "adapter",
        "brain",
        "internal",
        "operator_notes",
        "ceo_only",
        "farm",
        "swarm",
        "toloka",
        "scale_ai",
    }
)


def sanitize_public(value: Any, *, depth: int = 0) -> Any:
    if depth > 8:
        return None
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            k = str(key)
            if k.lower() in {s.lower() for s in _STRIP_KEYS}:
                continue
            if k.startswith("_"):
                continue
            out[k] = sanitize_public(item, depth=depth + 1)
        return out
    if isinstance(value, list):
        return [sanitize_public(v, depth=depth + 1) for v in value[:200]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)[:500]
