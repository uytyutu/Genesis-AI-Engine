"""Shared types for Factory engines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class EngineError(Exception):
    """Hard failure for an explicit engine run (never silent-fallback)."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class ClaudeEngineAuthError(EngineError):
    """Missing Anthropic/OpenRouter credentials for claude research engine."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            "claude_no_key",
            message
            or (
                "GENESIS_ANTHROPIC_API_KEY (or OpenRouter key) required for claude engine. "
                "No silent Classic fallback."
            ),
        )


@dataclass
class EngineRequest:
    description: str
    business_name: str = ""
    market_code: str = "DE"
    language: str = "en"
    package_id: str = "basic"
    city: str = ""
    phone: str = ""
    email: str = ""
    whatsapp: str = ""
    niche_hint: str = ""
    motion_level: str = "none"


@dataclass
class EngineResult:
    engine_id: str
    html: str
    meta: dict[str, Any] = field(default_factory=dict)
