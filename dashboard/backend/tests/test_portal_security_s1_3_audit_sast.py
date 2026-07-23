"""S1.3 — Dependency audit + SAST gates as pytest."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_dependency_audit_script_pass():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "s1_dependency_audit.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "dependency_audit PASS" in proc.stdout


def test_sast_scan_script_pass():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "s1_sast_scan.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "sast PASS" in proc.stdout
