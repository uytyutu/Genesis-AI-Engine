#!/usr/bin/env python3
"""Verify production build — import app, probe health endpoints, security gates."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

os.environ.setdefault("GENESIS_ENV", "production")
os.environ.setdefault("GENESIS_ACCEPTANCE_GATE", "1")


def main() -> int:
    from fastapi.testclient import TestClient

    from app.integration.context import get_integration, reset_integration
    from app.main import app

    print("=== Genesis production verification ===")
    print(f"GENESIS_ENV={os.environ.get('GENESIS_ENV')}")

    reset_integration()
    mem = BACKEND / "memory" / "_verify_probe"
    mem.mkdir(parents=True, exist_ok=True)
    get_integration(mem)

    errors: list[str] = []

    with TestClient(app) as client:
        for path in ("/health", "/status", "/api/status", "/api/sales/packages"):
            r = client.get(path)
            ok = r.status_code == 200
            print(f"  {'PASS' if ok else 'FAIL'} GET {path} -> {r.status_code}")
            if not ok:
                errors.append(f"{path} returned {r.status_code}")

        r = client.get("/api/owner/dashboard")
        blocked = r.status_code == 403
        print(f"  {'PASS' if blocked else 'FAIL'} GET /api/owner/dashboard blocked -> {r.status_code}")
        if not blocked:
            errors.append("owner dashboard not blocked in production")

        r = client.post(
            "/api/public/concierge",
            json={"question": "ping", "history": []},
            params={"debug": "true"},
        )
        if r.status_code == 200:
            body = r.json()
            if body.get("debug") or body.get("thinking_brief"):
                errors.append("debug/thinking_brief leaked in production concierge")
                print("  FAIL debug leak in concierge response")
            else:
                print("  PASS concierge debug suppressed in production")
        else:
            print(f"  WARN concierge returned {r.status_code} (non-fatal)")

    reset_integration()
    if errors:
        print("\nFAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nAll production checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
