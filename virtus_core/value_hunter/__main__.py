"""CLI: py -3.12 -m virtus_core.value_hunter [discover|sources|verify|simulate|evolve]"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from virtus_core.value_hunter.discovery import discover
    from virtus_core.value_hunter.evolution import run_epoch_tick, status as evo_status
    from virtus_core.value_hunter.pipeline import process_pipeline, simulate_opportunity, verify_opportunity

    args = [a.lower() for a in sys.argv[1:]]
    mode = "discover"
    opp_id = ""
    if not args:
        mode = "discover"
    elif args[0] in ("--sources", "sources", "--hunter-v2", "hunt"):
        mode = "sources"
    elif args[0] in ("--verify", "verify"):
        mode = "verify"
        opp_id = args[1] if len(args) > 1 else ""
    elif args[0] in ("--simulate", "simulate"):
        mode = "simulate"
        opp_id = args[1] if len(args) > 1 else ""
    elif args[0] in ("--evolve", "evolve", "evolution"):
        mode = "evolve"
    elif args[0] in ("--status", "status"):
        mode = "status"
    elif args[0] in ("--discover", "discover"):
        mode = "discover"

    if mode == "sources":
        report = process_pipeline()
    elif mode == "verify":
        if not opp_id:
            report = process_pipeline()
            queued = report.get("queue") or report.get("opportunities") or []
            opp_id = str((queued[0] or {}).get("id") or "") if queued else ""
        report = verify_opportunity(opp_id) if opp_id else {"ok": False, "reason": "no_opportunity_id"}
    elif mode == "simulate":
        if not opp_id:
            report = process_pipeline()
            queued = report.get("queue") or []
            opp_id = str((queued[0] or {}).get("id") or "") if queued else ""
        report = simulate_opportunity(opp_id) if opp_id else {"ok": False, "reason": "no_opportunity_id"}
    elif mode == "evolve":
        report = run_epoch_tick()
    elif mode == "status":
        report = evo_status()
    else:
        report = discover()
        # Embed v2.1 pipeline snapshot
        try:
            report["source_hunter_v21"] = process_pipeline()
        except Exception as e:
            report["source_hunter_v21_error"] = str(e)

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n---")
    if mode == "sources":
        c = report.get("counts") or {}
        print(f"Найдено: {c.get('sources_found')} · Очередь: {c.get('queued')} · Отклонено: {c.get('rejected')}")
        print(report.get("message"))
    elif mode == "evolve":
        a = report.get("agent") or {}
        print(f"Агент {a.get('agent_id')} epoch={a.get('epoch')} remaining={a.get('remaining_sec')}s")
        print((report.get("hunt") or {}).get("message"))
    elif mode == "discover":
        print(f"Worth investigating: {report.get('worth_investigating')}")
        sh = report.get("source_hunter_v21") or report.get("zero_capital_sources") or {}
        print(f"Zero-capital queued: {(sh.get('counts') or {}).get('queued', sh.get('queue_count'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
