"""CLI: py -3.12 -m virtus_core.protocol_state_discovery.experiment_p01"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from virtus_core.protocol_state_discovery.experiment_p01 import run_experiment_p01

    slug = "livepeer_arbitrum"
    for i, a in enumerate(sys.argv[1:]):
        if a == "--protocol" and i + 2 <= len(sys.argv[1:]):
            slug = sys.argv[i + 2]

    report = run_experiment_p01(protocol_slug=slug)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n--- P-01 SUMMARY ---")
    print("outcome:", report.get("experiment_outcome"))
    print("verdict:", report.get("verdict"))
    ps = report.get("pass_schema") or {}
    print("state:", ps.get("state"))
    print("theory:", report.get("theory_check"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
