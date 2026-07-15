#!/usr/bin/env python3
"""Weekly DSGVO job — remove lead phone numbers older than 90 days.

CEO / cron (no PowerShell required for scheduling — Task Scheduler or launcher hook):
  py scripts/purge_stale_lead_pii.py
  py scripts/purge_stale_lead_pii.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKEND = REPO / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.env_loader import load_local_env  # noqa: E402
from app.integration.lead_retention_service import purge_stale_lead_phones  # noqa: E402


def _memory_dir() -> Path:
    import os

    raw = os.getenv("GENESIS_MEMORY_DIR", "").strip()
    if raw:
        return Path(raw).expanduser()
    return BACKEND / "app" / "memory"


def main() -> int:
    load_local_env()
    parser = argparse.ArgumentParser(description="Purge stale lead phone numbers (DSGVO)")
    parser.add_argument("--days", type=int, default=90, help="Max age in days (default 90)")
    parser.add_argument("--dry-run", action="store_true", help="Report only, do not write")
    args = parser.parse_args()

    result = purge_stale_lead_phones(
        _memory_dir(),
        max_age_days=args.days,
        dry_run=args.dry_run,
    )
    print(f"ok={str(result.get('ok')).lower()}")
    print(f"scanned={result.get('scanned', 0)}")
    print(f"purged_rows={result.get('purged_rows', 0)}")
    print(f"dry_run={str(args.dry_run).lower()}")
    print(result.get("message", ""))
    if result.get("purged_ids"):
        print("sample_ids=" + ",".join(result["purged_ids"][:5]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
