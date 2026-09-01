"""CLI: py -3.12 -m virtus_core.protocol_state_discovery.experiment_p02_runner"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from virtus_core.protocol_state_discovery.experiment_p02 import run_experiment_p02

    report = run_experiment_p02(include_p01_control=True)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n--- P-02 SUMMARY ---")
    print("outcome:", report.get("experiment_outcome"))
    print("message:", report.get("message"))
    bc = report.get("best_candidate") or {}
    print("best:", bc.get("protocol"), "| p02_filter_pass:", bc.get("p02_filter_pass"), "| brick:", bc.get("brick_status"))
    print("counts:", report.get("counts"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
