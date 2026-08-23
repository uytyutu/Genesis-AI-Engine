"""Commercial UX Gate — no Landing-era buyer copy."""

from __future__ import annotations

from app.integration.commercial_ux_gate import audit_commercial_ux_gate
from app.integration.golden_website_launch import build_golden_website_launch


def test_commercial_ux_gate_passes_on_current_locales():
    snap = audit_commercial_ux_gate()
    assert snap["ok"] is True, snap.get("detail") or snap.get("violations")
    assert snap["status"] == "PASS"
    assert snap["checked_locales"] >= 3


def test_commercial_ux_in_launch_blockers(tmp_path):
    out = build_golden_website_launch(tmp_path)
    ids = [b["id"] for b in out["launch_blockers"]]
    assert "commercial_ux_gate" in ids
    cux = next(b for b in out["launch_blockers"] if b["id"] == "commercial_ux_gate")
    assert cux["status"] == "done"
