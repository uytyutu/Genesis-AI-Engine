#!/usr/bin/env python3
"""Visual Reality rebuild — mandatory after any Visual Studio / Factory visual change.

Philosophy:
  Code change → rebuild demos → open Starter/Business/Premium/Store → eyes → next task.

Never leave gallery stale while code is new.

    py -3.12 scripts/visual_reality_rebuild.py
    py -3.12 scripts/visual_reality_rebuild.py --ceo-only
    py -3.12 scripts/visual_reality_rebuild.py --full

CEO-only (fast gate set):
  sites/{basic,business,premium}/dental
  stores/{basic,business,premium}/fashion

Full: premium niches + store categories the CEO cares about.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts" / "sync_public_package_previews.py"


def _run(args: list[str]) -> int:
    print("+", " ".join(args), flush=True)
    proc = subprocess.run(args, cwd=str(ROOT))
    return int(proc.returncode or 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild Demo Gallery after visual changes")
    parser.add_argument(
        "--ceo-only",
        action="store_true",
        help="Only CEO Visual Review set (dental ladder + fashion store tiers)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Premium niches + stores + dental ladder",
    )
    parser.add_argument(
        "--skip-review",
        action="store_true",
        help="Skip CEO Visual Review gate at the end",
    )
    args = parser.parse_args()
    py = sys.executable

    # Always rebuild dental ladder (Starter / Business / Premium)
    rc = _run(
        [
            py,
            str(SYNC),
            "--tiers",
            "basic,business,premium",
            "--folders",
            "dental",
            "--websites-only",
        ]
    )
    if rc != 0:
        return rc

    if args.full or not args.ceo_only:
        # Premium websites: niches that must prove diversity
        rc = _run(
            [
                py,
                str(SYNC),
                "--tiers",
                "premium",
                "--folders",
                "dental,psychology,law,restaurant,auto,realestate,energy",
                "--websites-only",
            ]
        )
        if rc != 0:
            return rc
        # Business baseline for ladder niches
        rc = _run(
            [
                py,
                str(SYNC),
                "--tiers",
                "business",
                "--folders",
                "dental,psychology,law,restaurant,auto,beauty",
                "--websites-only",
            ]
        )
        if rc != 0:
            return rc

    # Store tiers for CEO Visual Review (+ categories when full)
    store_args = [py, str(SYNC), "--stores-only", "--store-tiers", "basic,business,premium"]
    if args.ceo_only:
        store_args.extend(["--store-folders", "fashion"])
    else:
        store_args.extend(
            ["--store-folders", "fashion,beauty,electronics,furniture,accessories,psychology"]
        )
    rc = _run(store_args)
    if rc != 0:
        return rc

    if args.skip_review:
        print("Skipped CEO Visual Review (--skip-review)")
        return 0

    # Gate
    sys.path.insert(0, str(ROOT / "dashboard" / "backend"))
    from app.integration.ceo_visual_review import run_ceo_visual_review

    review = run_ceo_visual_review()
    print()
    mark = "PASS" if review.get("ok") else "FAIL"
    print(f"CEO Visual Review: {review['status']}  mark={mark}")
    print(f"KPI: {review['kpi_ru']}")
    for s in review.get("samples") or []:
        mark = "OK" if s.get("ok") else "FAIL"
        print(f"  [{mark}] {s.get('id')}  issues={len(s.get('issues') or [])}")
        for issue in (s.get("issues") or [])[:5]:
            print(f"       - {issue}")
    print(review.get("action_ru") or "")
    if not review.get("ok"):
        print("\nHuman checklist still required after files PASS:")
        for q in review.get("human_checklist_ru") or []:
            print(f"  [ ] {q}")
        return 2
    print("\nFiles ready. Now open URLs and answer with your eyes:")
    for q in review.get("human_checklist_ru") or []:
        print(f"  [ ] {q}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
