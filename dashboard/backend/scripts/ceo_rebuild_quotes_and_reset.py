"""One-shot CEO repair: rebuild lead quotes + zero quota/wallet on live memory."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.integration.context import get_integration  # noqa: E402


def main() -> int:
    ctx = get_integration()
    acq = ctx.acquisition
    print("memory:", acq._memory_dir)
    rebuild = acq.rebuild_pipeline_quotes(limit=120)
    print("rebuild:", rebuild.get("message_ru"), "failed_sample=", rebuild.get("failed_sample"))
    reset = acq.reset_desk_counters_and_wallet()
    print("reset:", reset.get("message_ru"))
    pipe = acq.pipeline_leads(limit=8)
    for item in pipe[:5]:
        print(
            "-",
            item.get("company_name"),
            item.get("market"),
            item.get("recommended_price_label"),
            item.get("recommended_currency"),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
