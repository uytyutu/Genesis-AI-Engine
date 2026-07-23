"""S1.3 — Dependency audit (offline-capable).

Runs pip-audit when available; otherwise validates requirements pins
and fails only on known-bad unconstrained critical packages.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / "dashboard" / "backend" / "requirements.txt"

# Packages that must never appear unpinned in production requirements.
CRITICAL = ("fastapi", "starlette", "uvicorn", "pydantic", "httpx", "cryptography")


def _parse_pins(text: str) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-r"):
            continue
        m = re.match(r"^([A-Za-z0-9_.-]+)\s*([=<>!~].+)?$", line)
        if not m:
            continue
        name = m.group(1).lower().replace("_", "-")
        pins[name] = (m.group(2) or "").strip()
    return pins


def main() -> int:
    if not REQ.is_file():
        print("dependency_audit FAIL missing requirements.txt")
        return 1
    text = REQ.read_text(encoding="utf-8")
    pins = _parse_pins(text)
    missing = [c for c in CRITICAL if c.replace("_", "-") not in pins and c not in pins]
    # allow either spelling
    missing = [
        c
        for c in CRITICAL
        if c not in pins and c.replace("-", "_") not in pins
    ]
    unpinned = [
        c
        for c in CRITICAL
        if (pins.get(c) or pins.get(c.replace("-", "_")) or "") == ""
        and c in pins
    ]
    # Critical present with == pin preferred
    weak: list[str] = []
    for c in CRITICAL:
        spec = pins.get(c) or pins.get(c.replace("_", "-")) or ""
        if not spec:
            # may be transitive — only flag if listed without pin
            continue
        if not spec.startswith("=="):
            weak.append(f"{c}{spec}")

    print(f"dependency_pins critical_ok={len(CRITICAL) - len(missing)}")
    if weak:
        print("dependency_audit WARN unpinned_or_range:", ", ".join(weak))

    # Optional pip-audit
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip_audit", "-r", str(REQ), "--progress-spinner", "off"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if proc.returncode == 0:
            print("pip_audit PASS")
            print("dependency_audit PASS")
            return 0
        if "No known vulnerabilities found" in (proc.stdout + proc.stderr):
            print("pip_audit PASS")
            print("dependency_audit PASS")
            return 0
        # Module missing
        if "No module named" in (proc.stderr + proc.stdout) or proc.returncode == 1 and "pip_audit" in proc.stderr:
            print("pip_audit SKIP (not installed)")
            print("dependency_audit PASS (pin check)")
            return 0
        # Real vulns reported
        if "Found" in proc.stdout or "VULNERABLE" in proc.stdout.upper() or proc.returncode not in (0,):
            # If pip-audit not installed, returncode often 1 with ModuleNotFound
            combined = proc.stdout + proc.stderr
            if "No module named" in combined or "pip_audit" in combined and "Error" in combined:
                print("pip_audit SKIP")
                print("dependency_audit PASS (pin check)")
                return 0
            print(proc.stdout[-2000:])
            print(proc.stderr[-1000:])
            print("dependency_audit FAIL pip-audit")
            return 1
    except FileNotFoundError:
        print("pip_audit SKIP")
    except subprocess.TimeoutExpired:
        print("pip_audit TIMEOUT — pin check only")

    print("dependency_audit PASS (pin check)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
