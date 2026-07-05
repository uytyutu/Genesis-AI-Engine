"""Genesis Release Guardian — ship gate before new features or «done» reports."""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

STABILITY_HEALTH_MIN = 95

PRODUCT_NOT_READY = (
    "❌ Product is not ready. Continue fixing stability."
)

READY_FOR_CEO_VERIFY = (
    "READY FOR CEO VERIFY — Launch Pipeline OPEN until CEO confirms from Desktop."
)

LAUNCH_PIPELINE_CLOSED = "Launch Pipeline: CEO verified — ready to ship."


@dataclass
class ReleaseVerdict:
    ship: bool
    headline: str  # "ДА" or "НЕТ"
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    overall_health: int = 0

    def render(self) -> str:
        lines = [
            "Genesis Release Guardian",
            "",
            f"Можно ли выпускать / добавлять функции?  {self.headline}",
            f"Overall Health: {self.overall_health}%",
            "",
        ]
        if self.reasons:
            if self.headline == "READY FOR CEO VERIFY":
                lines.append(READY_FOR_CEO_VERIFY)
            else:
                lines.append(PRODUCT_NOT_READY)
            lines.append("")
            for r in self.reasons:
                lines.append(f"  ❌ {r}")
        if self.warnings:
            lines.append("")
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        if self.ship:
            lines.append("  ✓ Launch chain · HTTP 200 · Health ≥95% · CEO verified")
        elif self.headline == "READY FOR CEO VERIFY":
            lines.append("  ✓ Programmatic + GUI cycles passed")
            lines.append("  ⏳ Waiting for CEO Desktop verify (double-click Genesis.exe)")
        return "\n".join(lines)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def compute_overall_health(root: Path | None = None) -> tuple[int, list[str]]:
    """Simple live score — same probes CEO uses (no fiction)."""
    from launcher.deps import check_dependencies, frontend_build_integrity, frontend_build_ready
    from launcher.health import probe_backend_live, probe_frontend_live
    from launcher.paths import find_project_root

    root = root or find_project_root()
    reasons: list[str] = []
    deps = check_dependencies(root)

    scores: list[int] = []
    exe = root / "dist" / "Genesis.exe"
    scores.append(100 if exe.is_file() else 0)
    if not exe.is_file():
        reasons.append("Genesis.exe missing in dist/")

    be = probe_backend_live()
    scores.append(100 if be else 0)
    if not be:
        reasons.append("Backend not ready (/api/status)")

    fe = probe_frontend_live()
    scores.append(100 if fe else 0)
    if not fe:
        reasons.append("Frontend not ready (HTTP 200 :3000)")

    scores.append(100 if deps.python_ok and deps.node_ok else 0)
    build_ok = frontend_build_ready(root) and frontend_build_integrity(root)
    scores.append(100 if build_ok else 0)
    if not build_ok:
        reasons.append("Frontend build (.next) not ready")

    overall = int(sum(scores) / len(scores)) if scores else 0
    return overall, reasons


def evaluate_stability(*, min_health: int = STABILITY_HEALTH_MIN) -> ReleaseVerdict:
    """
    CEO gate — before new features or closing Launch Pipeline:

    Genesis.exe → Launch → Mission Control HTTP 200 → Backend + Frontend ready → Health ≥95%
    """
    root = _repo_root()
    reasons: list[str] = []
    warnings: list[str] = []

    stale = [root / "dist" / "Genesis Launcher.exe", root / "dist" / "Genesis-test.exe"]
    for path in stale:
        if path.is_file():
            reasons.append(f"Stale executable: {path.name}")

    exe = root / "dist" / "Genesis.exe"
    if not exe.is_file():
        reasons.append("Genesis.exe not built — run launcher/build.ps1")

    from launcher.health import owner_ready_live, probe_backend_live, probe_frontend_live

    if not probe_backend_live():
        reasons.append("Backend Ready: FAIL")
    if not probe_frontend_live():
        reasons.append("Frontend Ready: FAIL")
    if not owner_ready_live():
        reasons.append("Mission Control: not HTTP 200 on owner URLs")

    overall, health_reasons = compute_overall_health(root)
    if overall < min_health:
        reasons.append(f"Overall Health {overall}% < {min_health}%")
    for hr in health_reasons:
        if hr not in reasons:
            reasons.append(hr)

    ship = not reasons
    return ReleaseVerdict(
        ship=ship,
        headline="ДА" if ship else "НЕТ",
        reasons=reasons,
        warnings=warnings,
        overall_health=overall,
    )


def evaluate_release(*, run_regression: bool = True) -> ReleaseVerdict:
    """Full gate: live stability + launcher smoke + pytest tier."""
    verdict = evaluate_stability()
    if not verdict.ship:
        return verdict

    root = _repo_root()
    try:
        from launcher.app import GenesisLauncher

        app = GenesisLauncher()
        if not callable(app._root):
            verdict.reasons.append("Launcher UI broken (tkinter _root)")
            verdict.ship = False
            verdict.headline = "НЕТ"
        app.destroy()
    except Exception as exc:
        verdict.reasons.append(f"Launcher failed to open: {exc}")
        verdict.ship = False
        verdict.headline = "НЕТ"

    if run_regression and verdict.ship:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(root / "tests"),
                "-q",
                "--tb=line",
                "-k",
                "launcher or reconnect or release or startup or frontend_repair or backend_repair or genesis_learning",
            ],
            cwd=root / "dashboard" / "backend",
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            tail = (result.stdout + result.stderr).strip().splitlines()[-2:]
            verdict.reasons.append("Regression: " + " | ".join(tail))
            verdict.ship = False
            verdict.headline = "НЕТ"

    return verdict


def evaluate_launch_pipeline(
    *,
    min_cycles: int = 10,
    min_health: int = STABILITY_HEALTH_MIN,
) -> ReleaseVerdict:
    """
    Three-tier gate (Reality First):

    1. Stability + programmatic cycles → engineering OK
    2. GUI exe cycles (Genesis.exe) → READY FOR CEO VERIFY
    3. CEO manual confirm → ship ДА
    """
    from launcher.launch_pipeline_state import (
        ceo_manual_verified,
        gui_passed,
        programmatic_passed,
    )

    verdict = evaluate_stability(min_health=min_health)
    if not verdict.ship:
        return verdict

    root = _repo_root()
    if not programmatic_passed(root, min_cycles=min_cycles):
        verdict.ship = False
        verdict.headline = "НЕТ"
        verdict.reasons = [
            f"Programmatic launch cycles: need {min_cycles}x HTTP 200 "
            "(run scripts/launch_cycle_test.py)"
        ]
        return verdict

    if not gui_passed(root, min_cycles=min_cycles):
        verdict.ship = False
        verdict.headline = "НЕТ"
        verdict.reasons = [
            f"GUI launch cycles: need {min_cycles}x Genesis.exe "
            "(run scripts/ceo_gui_verification.py)"
        ]
        return verdict

    if not ceo_manual_verified(root):
        verdict.ship = False
        verdict.headline = "READY FOR CEO VERIFY"
        verdict.reasons = []
        verdict.warnings = [
            "Programmatic 10/10 and GUI 10/10 passed.",
            "CEO must verify: Desktop → Genesis.exe → ▶ → Mission Control HTTP 200.",
            "Then run: py scripts/ceo_confirm_launch_pipeline.py",
        ]
        return verdict

    verdict.headline = "ДА"
    verdict.warnings.append(LAUNCH_PIPELINE_CLOSED)
    return verdict
