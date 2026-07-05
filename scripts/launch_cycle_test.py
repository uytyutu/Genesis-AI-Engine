#!/usr/bin/env python3
"""Launch cycle stress test — N× start → ready → stop (CEO verify helper).

Run from repo root:
    py scripts/launch_cycle_test.py --cycles 5
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from launcher.health import owner_ready_live
from launcher.processes import ManagedProcesses, launch_genesis, stop_all, wait_until_ready


def run_cycle(
    cycle: int,
    root: Path,
    *,
    timeout: float,
    stop_after: bool = True,
) -> tuple[bool, str]:
    managed = ManagedProcesses()
    stop_all(managed, root)
    time.sleep(1)

    ok, msg = launch_genesis(managed, root, install_deps=False)
    if not ok:
        stop_all(managed, root)
        return False, f"cycle {cycle} launch_genesis: {msg}"

    ready, err = wait_until_ready(
        timeout=timeout,
        managed=managed,
        root=root,
        auto_repair=True,
    )
    if not ready or not owner_ready_live():
        stop_all(managed, root)
        return False, f"cycle {cycle} not ready: {err}"

    if stop_after:
        stop_all(managed, root)
        time.sleep(1)
    return True, f"cycle {cycle} OK"


def main() -> int:
    parser = argparse.ArgumentParser(description="Genesis launch cycle stress test")
    parser.add_argument("--cycles", type=int, default=10, help="Number of start/stop cycles")
    parser.add_argument("--timeout", type=float, default=180.0, help="Seconds per cycle ready wait")
    args = parser.parse_args()

    from launcher.paths import find_project_root

    root = find_project_root(ROOT)
    print(f"Launch cycle test x{args.cycles}")
    print("=" * 40)

    failures: list[str] = []
    for i in range(1, args.cycles + 1):
        print(f"Cycle {i}/{args.cycles}...", flush=True)
        stop_after = i < args.cycles
        ok, detail = run_cycle(i, root, timeout=args.timeout, stop_after=stop_after)
        print(f"  {'OK' if ok else 'FAIL'}  {detail}")
        if not ok:
            failures.append(detail)

    print("=" * 40)
    if failures:
        print(f"FAILED {len(failures)}/{args.cycles}")
        for f in failures:
            print(f"  - {f}")
        from launcher.release_guardian import PRODUCT_NOT_READY

        print(PRODUCT_NOT_READY)
        return 1

    from launcher.launch_pipeline_state import record_programmatic_cycles
    from launcher.processes import ManagedProcesses, stop_all
    from launcher.release_guardian import evaluate_launch_pipeline

    record_programmatic_cycles(args.cycles, root)
    verdict = evaluate_launch_pipeline(min_cycles=args.cycles)
    print(f"PASSED all {args.cycles} programmatic cycles (NOT GUI — CEO path still OPEN)")
    try:
        print(verdict.render())
    except UnicodeEncodeError:
        print(verdict.render().encode("ascii", errors="replace").decode("ascii"))
    stop_all(ManagedProcesses(), root)
    return 0 if verdict.headline in ("READY FOR CEO VERIFY", "ДА") else 1


if __name__ == "__main__":
    raise SystemExit(main())
