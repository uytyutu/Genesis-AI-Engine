"""Regression: GET /api/farm/opire must not UnboundLocalError on threading."""

from __future__ import annotations

from pathlib import Path

from swarm.opire_farm import OpireFarmEngine


def test_opire_panel_force_scan_false_no_unbound_threading(tmp_path: Path) -> None:
    """
    When healed=False, a local `import threading` inside panel() used to shadow
    the module import and crash at autonomous_tick Thread start.
    """
    eng = OpireFarmEngine(tmp_path)
    # Minimal state — no heal path, still builds panel + autonomous block
    eng._save({"tasks": {}, "last_scan": {"candidates": [], "scanned": 0}})
    out = eng.panel(force_scan=False, enrich_top=0)
    assert out.get("ok") is True
    assert "funnel" in out or "scan" in out
    assert "autonomous" in out
