#!/usr/bin/env python3
"""Run local dry-run until milestone (100x [DRY RUN] Potential profit lines)."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

os.environ.setdefault("FARM_LIVE_MODE", "dry_run")
os.environ.setdefault("FARM_EXECUTION_MODE", "local")
os.environ.setdefault("APP_ENV", "test")

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main() -> None:
    from app.integration.business_mode_service import BusinessModeService
    from app.integration.finance_service import FinanceService
    from app.integration.micro_farm_service import MicroFarmService
    from app.integration.opportunity_service import OpportunityService
    from swarm.dry_run import MILESTONE_STREAK

    memory = ROOT / "dashboard" / "backend" / "memory" / "dry_run_demo"
    memory.mkdir(parents=True, exist_ok=True)
    opp = OpportunityService(memory)
    for i in range(120):
        opp.create(
            {
                "source_id": "asset_scan",
                "company_name": f"Demo Shop {i}",
                "website_url": f"https://example-{i}.com",
                "status": "new",
                "meta": {"issues": [f"slow page {i}", "no https"], "swarm_labeled": False},
            }
        )
    farm = MicroFarmService(
        opp,
        FinanceService(memory),
        business_mode=BusinessModeService(memory),
        memory_dir=memory,
    )
    print(f"=== DRY RUN demo · local · target streak {MILESTONE_STREAK} ===\n")
    while int(farm._load_state().get("dry_run_streak") or 0) < MILESTONE_STREAK:
        farm.run_tick(workers=25)
    status = farm.dry_run_status()
    print(f"\n=== Done: streak={status['streak']} total_potential={status['total_potential_eur']} € ===")
    if status.get("milestone_reached"):
        print("Milestone 100 — VPS math validated (not bank payout).")


if __name__ == "__main__":
    main()
