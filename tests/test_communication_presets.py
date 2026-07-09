"""Communication style presets — Slice 2."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.integration.genesis_brain.communication_presets import (  # noqa: E402
    detect_auto_style,
    resolve_effective_style,
    style_memory_hint,
)


def test_auto_detects_business():
    assert detect_auto_style("Подготовь коммерческое предложение") == "professional"


def test_auto_detects_casual():
    assert detect_auto_style("Здарова брат") == "casual"


def test_manual_preset_overrides_auto():
    assert (
        resolve_effective_style("concise", "Здарова брат", {})
        == "concise"
    )


def test_auto_with_brief_memory_nudges_concise():
    inf = {"preferred_depth": "brief", "communication_style_preference": "casual"}
    assert resolve_effective_style("auto", "привет", inf) == "concise"


def test_casual_preference_nudges_friendly_to_casual():
    inf = {"communication_style_preference": "casual"}
    assert resolve_effective_style("auto", "привет как дела", inf) == "casual"


def test_business_overrides_casual_memory():
    inf = {"communication_style_preference": "casual", "preferred_depth": "brief"}
    assert (
        resolve_effective_style("auto", "Подготовь коммерческое предложение", inf)
        == "professional"
    )


def test_manual_preset_ignores_memory():
    inf = {"communication_style_preference": "casual", "preferred_depth": "brief"}
    assert resolve_effective_style("professional", "го брат", inf) == "professional"


def test_style_memory_hint_only_for_auto():
    hint = style_memory_hint(
        "auto",
        {"communication_style_preference": "casual", "preferred_depth": "brief"},
    )
    assert "Память стиля" in hint
    assert style_memory_hint("concise", {"preferred_depth": "brief"}) == ""


def test_manual_disables_auto_detection():
    assert (
        resolve_effective_style("professional", "че как го", {})
        == "professional"
    )
