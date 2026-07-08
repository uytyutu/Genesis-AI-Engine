#!/usr/bin/env python3
"""Genesis Setup v2 gate — AI Workforce status, not OpenAI-only."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("GENESIS_ACCEPTANCE_GATE", "1")

from app.integration.workforce_setup import WorkforceSetupService  # noqa: E402


def test_status_has_workforce() -> None:
    st = WorkforceSetupService().status()
    assert st["genesis_ready"] is True
    assert st["workforce_tier"] in ("full", "limited")
    employees = st["employees"]
    assert employees[0]["id"] == "genesis-local"
    assert employees[0]["core"] is True
    assert employees[0]["status"] == "ready"
    assert employees[0].get("roles")
    ids = {e["id"] for e in employees}
    for need in ("groq", "gemini", "openrouter", "ollama", "openai", "genesis-local"):
        assert need in ids, f"missing employee {need}"


def test_no_openai_required() -> None:
    st = WorkforceSetupService().status()
    assert st["genesis_ready"] is True
    assert "employees" in st
    assert "connectable" in st
    assert "groq" in st["connectable"]
    assert "openai" in st["connectable"]


def main() -> int:
    tests = [
        ("workforce_status", test_status_has_workforce),
        ("no_openai_required", test_no_openai_required),
    ]
    ok = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
            ok += 1
        except Exception as exc:
            print(f"FAIL {name}: {exc}")
    print(f"\n{ok}/{len(tests)} PASS")
    return 0 if ok == len(tests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
