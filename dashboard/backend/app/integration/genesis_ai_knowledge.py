"""Genesis product knowledge — delegates to Core Intelligence v2."""

from __future__ import annotations

from typing import Any

from app.integration.genesis_core_intelligence import build_core_system_prompt


def build_system_prompt(packages: list[dict[str, Any]]) -> str:
    return build_core_system_prompt(packages)
