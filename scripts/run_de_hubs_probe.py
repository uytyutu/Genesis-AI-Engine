#!/usr/bin/env python3
"""CEO probe: DE major hubs Places search + farm readiness report (limited batch)."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKEND = REPO / "dashboard" / "backend"
MEM = BACKEND / "app" / "memory"
sys.path.insert(0, str(BACKEND))

logging.basicConfig(level=logging.INFO, format="%(message)s")


def _write_config() -> None:
    cfg = {
        "mode": "global_spider",
        "zero_cost": True,
        "freeze_lists": True,
        "target_mode": "places_only",
        "min_task_price": 0.02,
        "polling_interval_sec": 8,
        "seed_targets": [],
        "places_queries": [
            "Autowerkstatt website",
            "IT Service Unternehmen",
            "Elektriker Betrieb",
            "Handwerker",
            "Computer Reparatur",
        ],
        "regions_enabled": True,
        "max_batch": 500,
        "search_region": "de",
        "search_city": "all_major_hubs",
        "note": "DE hubs · freeze_lists · GOOGLE_PLACES_API_KEY required",
    }
    MEM.mkdir(parents=True, exist_ok=True)
    (MEM / "global_spider_config.json").write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    os.chdir(BACKEND)
    from app.env_loader import load_local_env

    load_local_env()
    _write_config()

    from app.integration.finance_service import FinanceService
    from app.integration.global_spider_service import GlobalSpiderService
    from app.integration.google_places_service import GooglePlacesService
    from app.integration.micro_farm_service import MicroFarmService
    from app.integration.opportunity_service import OpportunityService
    from app.integration.business_mode_service import BusinessModeService
    from app.integration.payment_settlement_service import PaymentSettlementService

    places = GooglePlacesService()
    print("=== PLACES ===")
    print(f"configured={places.configured()}")
    if not places.configured():
        print("FAIL: GOOGLE_PLACES_API_KEY missing — no real DE leads without API")
        return 2

    spider = GlobalSpiderService(MEM)
    # Small batch for probe — full 500 is for Genesis UI / overnight
    probe_limit = int(os.getenv("GENESIS_SPIDER_PROBE_LIMIT", "12"))
    print(f"=== DISCOVER batch_limit={probe_limit} ===")
    try:
        urls, stats = spider.discover_candidate_urls(niche="local_service", batch_limit=probe_limit)
    except Exception as exc:  # noqa: BLE001 — report for CEO
        err = str(exc)
        print(f"discover_error={err[:300]}")
        if "OVER_QUERY_LIMIT" in err or "REQUEST_DENIED" in err:
            print("quota_or_denied=true — freemium limit or key restriction")
        return 3

    print(f"hub_mode={stats.get('hub_mode')}")
    print(f"hubs_count={len(stats.get('hubs') or [])}")
    print(f"regions_scanned={stats.get('regions_scanned')}")
    print(f"places_hits={stats.get('places')}")
    print(f"urls_found={len(urls)}")
    for u in urls[:10]:
        print(f"  lead_url={u}")

    # Upsert a few opportunities so /acquisition can show them
    opp = OpportunityService(MEM)
    created = 0
    for u in urls[: min(8, len(urls))]:
        try:
            opp.create(
                {
                    "source_id": "google_maps",
                    "opportunity_type": "lead",
                    "company_name": u.replace("https://", "").replace("http://", "")[:60],
                    "website_url": u,
                    "fit_reason": "DE Places probe · Handwerk/IT",
                    "score": 70,
                    "potential_value_eur": 350,
                    "meta": {"scan_mode": "de_hubs_probe", "country_code": "DE"},
                }
            )
            created += 1
        except ValueError:
            continue
    print(f"opportunities_created={created}")

    print("=== FARM ===")
    farm = MicroFarmService(
        opp,
        FinanceService(MEM),
        business_mode=BusinessModeService(MEM),
        memory_dir=MEM,
    )
    dry = farm.dry_run_status()
    dash = farm.dashboard_lite()
    print(f"dry_run_active={dry.get('active') if isinstance(dry, dict) else dry}")
    print(f"farm_live_env={os.getenv('FARM_LIVE_MODE', 'dry_run')}")
    print(f"total_earned_eur={dash.get('total_earned_eur', 0)}")
    dry_block = dash.get("dry_run") if isinstance(dash.get("dry_run"), dict) else {}
    print(f"dry_run_potential_eur={dry_block.get('total_potential_eur', dash.get('dry_run_total_potential_eur', 0))}")

    try:
        tick = farm.run_tick(workers=2)
        print(f"tick_ok={bool(tick.get('ok') if isinstance(tick, dict) else True)}")
        if isinstance(tick, dict):
            print(f"tick_message={(tick.get('message') or '')[:200]}")
            print(f"tasks_done={tick.get('tasks_done')}")
            print(f"tick_earned={tick.get('earned_eur') or tick.get('pay_eur')}")
    except Exception as exc:  # noqa: BLE001
        print(f"tick_error={str(exc)[:200]}")

    sett = PaymentSettlementService(MEM)
    totals = sett.totals()
    print("=== MONEY HONESTY ===")
    print(f"settlements_paid_by_client_eur={totals.get('paid_by_client_eur')}")
    print(f"settlements_pending_eur={totals.get('pending_settlement_eur')}")
    print(f"settlements_available_eur={totals.get('available_for_withdrawal_eur')}")
    print(
        "verdict_farm="
        + (
            "dry_run_journal_only — cents not Stripe bank"
            if str(os.getenv("FARM_LIVE_MODE", "dry_run")).lower() != "live"
            else "live_mode — exchange wallet only if Toloka/Scale keys work"
        )
    )
    print("verdict_b2b=income only after CEO Outbox + client Stripe checkout")
    return 0 if urls else 1


if __name__ == "__main__":
    raise SystemExit(main())
