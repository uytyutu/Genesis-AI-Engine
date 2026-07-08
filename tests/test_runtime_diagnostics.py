"""Runtime diagnostics formatting."""

from __future__ import annotations

from launcher.runtime_diagnostics import format_runtime_diagnostics


def test_runtime_diagnostics_contains_core_fields():
    text = format_runtime_diagnostics()
    assert "Runtime" in text
    assert "Python:" in text
    assert "Backend:" in text
    assert "Dependencies:" in text
