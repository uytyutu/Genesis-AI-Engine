#!/usr/bin/env python3
"""Quick compare: normal vs cloud-proof for greeting/emotional messages."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))
os.environ.pop("GENESIS_ACCEPTANCE_GATE", None)

from app.env_loader import load_local_env

load_local_env()

QUESTIONS = ["Как дела?", "Мне плохо", "Привет"]


def run(q: str, cloud: bool) -> None:
    if cloud:
        os.environ["GENESIS_CLOUD_PROOF"] = "1"
    else:
        os.environ.pop("GENESIS_CLOUD_PROOF", None)
    from app.integration.genesis_brain.brain import GenesisBrain

    b = GenesisBrain()
    r = b.chat(
        system="Genesis public",
        messages=[{"role": "user", "content": q}],
        visitor_id=f"cmp-{'cloud' if cloud else 'norm'}",
        debug=True,
    )
    pipe = (r.trace or {}).get("runtime_pipeline") or {}
    raw = (pipe.get("raw_response") or "")[:100]
    print(f"  mode={'CLOUD_PROOF' if cloud else 'NORMAL':11} emp={pipe.get('employee_chosen')} src={pipe.get('answer_source')}")
    print(f"  RAW:   {raw}...")
    print(f"  FINAL: {(r.answer or '')[:100]}...")
    print(f"  replaced: {raw.strip() != (r.answer or '')[:100].strip() and 'YES' or 'no'}")


for q in QUESTIONS:
    print(f"\n=== {q} ===")
    run(q, False)
    run(q, True)
