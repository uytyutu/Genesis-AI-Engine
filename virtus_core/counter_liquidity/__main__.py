"""CLI: py -3.12 -m virtus_core.counter_liquidity [discover|verify|routes|simulate|evolve]"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from virtus_core.counter_liquidity.engine import discover, routes_report, simulate_all, verify_sources

    args = [a.lower() for a in sys.argv[1:]]
    mode = args[0] if args else "discover"
    if mode in ("--discover", "discover", "hunt"):
        report = discover()
    elif mode in ("--verify", "verify"):
        report = verify_sources()
    elif mode in ("--routes", "routes"):
        report = routes_report()
    elif mode in ("--simulate", "simulate"):
        report = simulate_all()
    elif mode in ("--evolve", "evolve"):
        # Reuse Value Hunter evolution tick + counter-liquidity discover
        from virtus_core.value_hunter.evolution import run_epoch_tick

        evo = run_epoch_tick()
        liq = discover()
        report = {"evolution": evo, "counter_liquidity": {"outcome": liq.get("outcome"), "counts": liq.get("counts"), "message": liq.get("message")}}
    else:
        report = discover()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n---")
    if "outcome" in report:
        print(report.get("message"))
        c = report.get("counts") or {}
        print(f"outcome={report.get('outcome')} verified_liq={c.get('counter_liquidity_verified')} rejected={c.get('rejected')} hyp={c.get('hypotheses')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
