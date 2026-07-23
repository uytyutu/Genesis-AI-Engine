"""Security Regression Suite — run all S1 automated gates.

Exit 0 only when every gate passes (N/N).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"

GATES: list[tuple[str, list[str]]] = [
    (
        "pytest_s1",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_portal_security_s1.py",
            "tests/test_portal_security_s1_rate_limit.py",
            "tests/test_portal_security_s1_2_infra.py",
            "tests/test_portal_security_s1_3_authz_matrix.py",
            "tests/test_portal_security_s1_3_negative.py",
            "tests/test_portal_security_s1_3_orders_idor.py",
            "tests/test_portal_security_s1_3_invoices_idor.py",
            "tests/test_portal_security_s1_3_upload_xss.py",
            "tests/test_portal_security_s1_3_audit_sast.py",
            "tests/test_portal_security_s1_4_ai.py",
            "-q",
            "--tb=line",
        ],
    ),
    (
        "frontend_secret_scan",
        [sys.executable, str(ROOT / "scripts" / "s1_frontend_secret_scan.py")],
    ),
    (
        "dependency_audit",
        [sys.executable, str(ROOT / "scripts" / "s1_dependency_audit.py")],
    ),
    (
        "sast",
        [sys.executable, str(ROOT / "scripts" / "s1_sast_scan.py")],
    ),
]


def main() -> int:
    results: list[tuple[str, bool]] = []
    for name, cmd in GATES:
        cwd = str(BACKEND) if name == "pytest_s1" else str(ROOT)
        print(f"--- gate:{name} ---")
        proc = subprocess.run(cmd, cwd=cwd, check=False)
        ok = proc.returncode == 0
        results.append((name, ok))
        print(f"gate:{name} {'PASS' if ok else 'FAIL'} exit={proc.returncode}")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"Security Regression Suite {passed}/{total} {'PASS' if passed == total else 'FAIL'}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
