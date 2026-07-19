"""Engine router — explicit engine id only; no silent Classic fallback for Claude."""

from __future__ import annotations

import os

from app.factory.engines.base import EngineError, EngineRequest, EngineResult
from app.factory.engines.classic_engine import generate as classic_generate
from app.factory.engines.claude_engine import generate as claude_generate

_KNOWN = frozenset({"classic", "claude"})


def resolve_research_engine(explicit: str | None = None) -> str:
    """Research CLI / FACTORY_RESEARCH_ENGINE only — never used by Path A checkout."""
    raw = (explicit or os.getenv("FACTORY_RESEARCH_ENGINE") or "classic").strip().lower()
    if raw not in _KNOWN:
        raise EngineError("unknown_engine", f"Unknown engine '{raw}'. Use classic|claude.")
    return raw


def generate_with_engine(engine_id: str, request: EngineRequest) -> EngineResult:
    eid = (engine_id or "").strip().lower()
    if eid == "classic":
        return classic_generate(request)
    if eid == "claude":
        # Hard fail inside claude_engine — never call classic here.
        return claude_generate(request)
    raise EngineError("unknown_engine", f"Unknown engine '{engine_id}'. Use classic|claude.")
