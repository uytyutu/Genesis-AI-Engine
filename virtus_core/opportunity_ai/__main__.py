"""CLI: py -3.12 -m virtus_core.opportunity_ai [--systematic|--offline]"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from virtus_core.opportunity_ai.systematic import systematic_discover

    offline = "--offline" in sys.argv
    report = systematic_discover(offline=offline)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n---")
    print(report.get("epoch_status"), "·", report.get("scientific_result"))
    print(report.get("message"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
