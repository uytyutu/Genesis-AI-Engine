#!/usr/bin/env python3
"""Remove demo spider seeds (wikipedia/python/…) and reset lab farm counters."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]
MEM = REPO / "dashboard" / "backend" / "app" / "memory"

DEMO_HOSTS = frozenset(
    {
        "wikipedia.org",
        "python.org",
        "mozilla.org",
        "debian.org",
        "nginx.com",
        "cloudflare.com",
        "example.com",
        "f5.com",
        "w3.org",
        "github.com",
        "google.com",
        "facebook.com",
        "apache.org",
        "kernel.org",
        "gnu.org",
    }
)


def _host(url: str) -> str:
    h = (urlparse(url or "").hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def _is_demo(row: dict) -> bool:
    host = _host(str(row.get("website_url") or ""))
    if not host:
        # no website + asset_scan junk from seeds
        if str(row.get("source_id") or "") in ("asset_scan",) and str(row.get("company_name") or "").lower() in (
            "wikipedia",
            "python",
            "cloudflare",
        ):
            return True
        return False
    return any(host == d or host.endswith("." + d) for d in DEMO_HOSTS)


def main() -> int:
    MEM.mkdir(parents=True, exist_ok=True)
    path = MEM / "opportunities.jsonl"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    removed = 0
    kept: list[dict] = []

    if path.is_file():
        bak = MEM / f"opportunities.demo_backup_{stamp}.jsonl"
        text = path.read_text(encoding="utf-8", errors="replace")
        bak.write_text(text, encoding="utf-8")
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if _is_demo(row):
                removed += 1
                continue
            kept.append(row)
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in kept) + ("\n" if kept else ""),
            encoding="utf-8",
        )
    else:
        bak = None

    # Reset farm journal counters (lab — not Stripe)
    farm_path = MEM / "micro_farm_state.json"
    if farm_path.is_file():
        try:
            farm = json.loads(farm_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            farm = {}
        farm.update(
            {
                "total_tasks_done": 0,
                "total_earned_eur": 0.0,
                "today_earned_eur": 0.0,
                "llm_cost_eur": 0.0,
                "dry_run_streak": 0,
                "dry_run_total_potential_eur": 0.0,
                "dry_run_milestone_reached": False,
                "workers_active": 0,
                "demo_purge_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        farm_path.write_text(json.dumps(farm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    harvest = MEM / "engine_harvest.json"
    if harvest.is_file():
        harvest.write_text(
            json.dumps(
                {
                    "lifetime_harvest_eur": 0.0,
                    "pipeline_potential_eur": 0.0,
                    "junk_micro_revenue_eur": 0.0,
                    "last_sync_at": None,
                    "demo_purge_at": datetime.now(timezone.utc).isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    print(f"ok=true removed={removed} kept={len(kept)}")
    if bak:
        print(f"backup={bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
