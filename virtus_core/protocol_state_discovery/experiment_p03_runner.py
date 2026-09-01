"""CLI: py -3.12 -m virtus_core.protocol_state_discovery.experiment_p03_runner"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from virtus_core.protocol_state_discovery.experiment_p03 import run_experiment_p03

    report = run_experiment_p03()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n--- P-03 SUMMARY ---")
    print("outcome:", report.get("experiment_outcome"))
    print("taxonomy:", report.get("taxonomy", {}).get("current_id"), report.get("taxonomy", {}).get("current", {}).get("id"))
    print("dimensions:", report.get("research_dimensions"))
    print("brick:", report.get("economic_brick"))
    print("message:", report.get("message"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
