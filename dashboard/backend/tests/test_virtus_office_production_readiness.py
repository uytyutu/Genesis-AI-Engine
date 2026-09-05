"""Phase A — Virtus Office production readiness (E2E + gates, no LIVE flip)."""

from __future__ import annotations

from pathlib import Path

from app.integration.virtus_office import OFFICE_PIPELINE_LIVE
from app.integration.virtus_office.production_readiness import (
    PHASE_A_GROUPS,
    build_production_readiness,
    format_production_readiness,
)


def test_pipeline_live_untouched():
    assert OFFICE_PIPELINE_LIVE is True


def test_phase_a_production_readiness_go(tmp_path: Path):
    # Unit gate: mock email + offline translate allowed via conftest.
    # Live Resend/Groq path is scripts/office_production_readiness.py with OFFICE_E2E_LIVE=1.
    report = build_production_readiness(tmp_path, run_e2e=True, live_email=False)
    text = format_production_readiness(report)
    assert "PRODUCTION_READINESS" in text
    assert "RELEASE VERDICT:" in text
    assert report["pipeline_live"] is True
    assert report["auto_flip"] is False

    for group in PHASE_A_GROUPS:
        gid = group["id"]
        assert gid in report["sellable_groups"], gid
        row = report["sellable_groups"][gid]
        assert row["ok"] is True, (gid, row)

    assert all(r["ok"] for r in report["payment"]), report["payment"]
    assert all(r["ok"] for r in report["security"]), report["security"]
    assert all(r["ok"] for r in report["api_ssot"]), report["api_ssot"]
    assert report["inconsistencies"] == []
    assert report["verdict"] == "GO", (report["verdict"], report.get("blockers"), text)
