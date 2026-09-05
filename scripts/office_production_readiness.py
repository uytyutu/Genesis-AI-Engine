#!/usr/bin/env python3
"""Run Virtus Office Phase A production readiness → print GO/NO-GO checklist.

Loads .env.local (Resend + Groq). Does NOT flip OFFICE_PIPELINE_LIVE or Stripe Live.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ["OFFICE_E2E_LIVE"] = "1"
os.environ.pop("OFFICE_ALLOW_OFFLINE_TRANSLATE", None)

from app.env_loader import load_local_env  # noqa: E402

load_local_env()

from app.integration.virtus_office.production_readiness import (  # noqa: E402
    build_production_readiness,
    format_production_readiness,
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="office-prod-ready-") as tmp:
        report = build_production_readiness(Path(tmp), run_e2e=True, live_email=None)
    text = format_production_readiness(report)
    print(text)
    return 0 if report.get("verdict") == "GO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
