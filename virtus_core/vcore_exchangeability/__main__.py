"""CLI: py -3.12 -m virtus_core.vcore_exchangeability [--offline]  (VCORE-X01)"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from virtus_core.vcore_exchangeability.engine import run_x01_external_exchangeability

    offline = "--offline" in sys.argv
    report = run_x01_external_exchangeability(offline=offline)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n---")
    s = report["summary"]
    print(f"REAL_EXTERNAL_ASSET={s['REAL_EXTERNAL_ASSET']}")
    print(f"readiness={s['readiness']}")
    print(f"outcome={s['experiment_outcome']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
