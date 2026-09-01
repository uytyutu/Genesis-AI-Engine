"""CLI: py -3.12 -m virtus_core.bip39_compute_lab [--bench|--dual|--offline]"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from virtus_core.bip39_compute_lab.lab import (
        evaluate_found_candidate,
        reject_foreign_seed_path,
        run_bip39_bench,
        run_dual_architecture,
    )

    args = [a.lower() for a in sys.argv[1:]]
    workers = 8
    batch = 150
    for i, a in enumerate(args):
        if a == "--workers" and i + 1 < len(args):
            workers = int(args[i + 1])
        if a == "--batch" and i + 1 < len(args):
            batch = int(args[i + 1])

    if "--reject-demo" in args:
        report = reject_foreign_seed_path("video_wallet_cracker")
    elif "--bench" in args:
        report = run_bip39_bench(workers=workers, batch_per_worker=batch)
    elif "--found-trap" in args:
        report = evaluate_found_candidate({"confirmed_balance": 999999})
    else:
        offline = "--offline" in args
        report = run_dual_architecture(workers=workers, batch=batch, offline=offline)

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n---")
    if "vectors_per_sec" in report:
        print(f"BIP39 lab: {report['vectors_per_sec']} vectors/s · workers={report.get('workers')} · income_claimed={report.get('income_claimed')}")
    elif "bip39_compute_lab" in report:
        b = report["bip39_compute_lab"]
        print(f"Dual: {b.get('vectors_per_sec')} vec/s · telegram={report.get('telegram_required')} · FOUND trap={report.get('screen_number_is_not_found',{}).get('found')}")
        print(f"Opportunity AI: {(report.get('opportunity_ai') or {}).get('epoch_status')} · {(report.get('opportunity_ai') or {}).get('outcome')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
