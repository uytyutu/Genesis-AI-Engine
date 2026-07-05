#!/usr/bin/env python3
"""CEO confirms Launch Pipeline after personal Desktop verify.

Run ONLY after you completed:
  Desktop → Genesis.exe → ▶ → Mission Control HTTP 200 (several times)

    py scripts/ceo_confirm_launch_pipeline.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from launcher.launch_pipeline_state import record_ceo_manual_verify
    from launcher.paths import find_project_root
    from launcher.release_guardian import evaluate_launch_pipeline

    root = find_project_root(ROOT)
    record_ceo_manual_verify(root, by="CEO")
    verdict = evaluate_launch_pipeline()
    try:
        print(verdict.render())
    except UnicodeEncodeError:
        print(verdict.render().encode("ascii", errors="replace").decode("ascii"))
    return 0 if verdict.ship else 1


if __name__ == "__main__":
    raise SystemExit(main())
