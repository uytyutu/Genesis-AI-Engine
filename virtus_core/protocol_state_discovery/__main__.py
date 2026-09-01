"""CLI: py -3.12 -m virtus_core.protocol_state_discovery [--offline]"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from virtus_core.protocol_state_discovery.engine import run_protocol_state_discovery

    offline = "--offline" in sys.argv
    report = run_protocol_state_discovery(offline=offline)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n---")
    print(report.get("epoch_status"), "·", report.get("scientific_result"))
    print(report.get("message"))
    print("insight_fit:", report.get("insight_fit_ids"))
    print("missing_freq:", report.get("missing_field_frequency"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
