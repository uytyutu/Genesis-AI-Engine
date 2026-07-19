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


@dataclass
class EngineResult:
    engine_id: str
    html: str
    meta: dict[str, Any] = field(default_factory=dict)
