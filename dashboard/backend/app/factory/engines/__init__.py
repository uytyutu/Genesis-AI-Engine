"""Factory generation engines — Classic (Path A) + research Claude.

Path A commerce always uses classic. Claude is research-only via router/CLI.
"""

from __future__ import annotations

from app.factory.engines.base import EngineError, EngineRequest, EngineResult
from app.factory.engines.router import generate_with_engine, resolve_research_engine

__all__ = [
    "EngineError",
    "EngineRequest",
    "EngineResult",
    "generate_with_engine",
    "resolve_research_engine",
]
