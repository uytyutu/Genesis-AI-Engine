"""AI Hub provider registry tests."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.integration.ai_hub.provider_registry import (  # noqa: E402
    default_development_provider,
    providers_for_capability,
)


def test_cursor_tool_for_ceo_code():
    providers = providers_for_capability("code", "ceo")
    ids = {p.id for p in providers}
    assert "cursor-tool" in ids


def test_default_development_provider():
    p = default_development_provider()
    assert p is not None
    assert p.id == "cursor-tool"


def test_free_tier_no_cursor():
    providers = providers_for_capability("code", "free")
    assert all(p.id != "cursor-tool" for p in providers)
