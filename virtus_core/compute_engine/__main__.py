"""CLI: py -3.12 -m virtus_core.compute_engine [--measure] [--json]"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from repo root without install
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Virtus Compute Engine V1")
    parser.add_argument("--measure", action="store_true", help="Run local SHA-256 measure worker (reward=0)")
    parser.add_argument("--json", action="store_true", help="Print full JSON to stdout")
    parser.add_argument("--report", action="store_true", help="Write markdown report")
    args = parser.parse_args(argv)

    from virtus_core.compute_engine.service import run_full_audit, write_markdown_report

    report = run_full_audit(run_measure=args.measure)
    if args.report or not args.json:
        path = write_markdown_report(report)
        print(f"Report: {path}")
        print(f"Conclusion: {report.get('conclusion')}")
        hw = report.get("hardware") or {}
        gpu = hw.get("gpu") or {}
        print(f"GPU: {gpu.get('name')} · {gpu.get('power_watts')} W · CUDA={gpu.get('cuda_available')}")
        for b in report.get("benchmarks") or []:
            print(f"  bench {b.get('algorithm')}: {b.get('ops_per_sec')} {b.get('unit')}")
        tw = report.get("treasury") or {}
        print(
            f"Treasury CONFIRMED: {tw.get('confirmed')} {tw.get('currency')} "
            f"(PENDING {tw.get('pending')} · EXPECTED {tw.get('expected')})"
        )
        if report.get("current_worker"):
            w = report["current_worker"]
            print(f"Worker: {w.get('state')} — {w.get('message')}")
    if args.json:
        # Avoid Windows console encoding issues
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
