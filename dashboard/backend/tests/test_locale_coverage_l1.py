"""L1 Locale coverage gate — etalon catalog parity."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "scripts" / "locale_coverage_gate.py"
LOCALES = REPO / "dashboard" / "frontend" / "locales"
ETALON = ("de", "en", "ru", "uk")
REQUIRED = ("common", "site", "order", "client", "vector", "errors")


def test_etalon_namespace_files_exist():
    for loc in ETALON:
        for ns in REQUIRED:
            path = LOCALES / loc / f"{ns}.json"
            assert path.is_file(), f"missing {path}"


def test_terminology_file_exists():
    path = LOCALES / "terminology.json"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for term in ("Virtus Core", "Vector", "Website", "Analytics", "AI Assistant"):
        assert term in text


def test_coverage_gate_script_passes():
    assert SCRIPT.is_file()
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    assert "GATE: PASS" in proc.stdout


def test_resources_exports_l1_namespaces():
    resources = (
        REPO
        / "dashboard"
        / "frontend"
        / "app"
        / "lib"
        / "i18n"
        / "resources.ts"
    ).read_text(encoding="utf-8")
    assert "deOrder" in resources
    assert "deClient" in resources
    assert "deVector" in resources
    assert "ukOrder" in resources
    assert "ukClient" in resources
    assert "ukVector" in resources
    assert "L1_REQUIRED_NAMESPACES" in resources
