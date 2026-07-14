"""P0 diagnostic — trace Vector chat chain locally."""
from __future__ import annotations

import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "dashboard" / "backend"


def main() -> None:
    import os
    import sys

    os.chdir(BACKEND)
    sys.path.insert(0, str(BACKEND))

    from app.env_loader import load_local_env

    load_local_env()

    from app.integration.genesis_brain.providers import build_provider_chain

    print("=== PROVIDERS ===")
    chain = build_provider_chain([])
    for p in chain:
        t0 = time.perf_counter()
        av = p.available()
        ms = round((time.perf_counter() - t0) * 1000)
        model = getattr(p, "model_name", None)
        print(f"  {p.provider_id}: available={av} probe_ms={ms} model={model}")

    from app.integration.genesis_ai_service import GenesisAIService

    mem = BACKEND / "app" / "memory"
    svc = GenesisAIService([], memory_dir=mem)
    print("\n=== SERVICE STATUS ===")
    print("llm_configured:", svc.llm_configured())
    print("intelligence_active:", svc.intelligence_active())

    print("\n=== CHAT (Привет) ===")
    t0 = time.perf_counter()
    r = svc.chat("Привет", visitor_id="test-p0", history=[])
    elapsed = round(time.perf_counter() - t0, 2)
    print("elapsed_s:", elapsed)
    print("provider:", r.get("provider"))
    print("answer_len:", len(r.get("answer", "")))
    preview = (r.get("answer") or "")[:400]
    try:
        print("answer_preview:", preview)
    except UnicodeEncodeError:
        print("answer_preview:", preview.encode("ascii", errors="backslashreplace").decode("ascii"))

    print("\n=== CHAT DEBUG ===")
    t0 = time.perf_counter()
    r2 = svc.chat("Привет", visitor_id="test-p0-debug", history=[], debug=True)
    elapsed2 = round(time.perf_counter() - t0, 2)
    print("elapsed_s:", elapsed2)
    print("provider:", r2.get("provider"))
    dbg = r2.get("debug") or {}
    wr = dbg.get("workforce_reality") or {}
    attempts = wr.get("attempts") or dbg.get("all_attempts") or []
    print("attempts:", len(attempts))
    for a in attempts[:12]:
        if isinstance(a, dict):
            print(
                " ",
                a.get("employee_id"),
                a.get("outcome"),
                a.get("latency_ms"),
                (a.get("error") or "")[:80],
            )
    rp = dbg.get("runtime_pipeline") or {}
    print("chosen:", rp.get("employee_chosen"), rp.get("employee_model"))
    print("answer_len:", len(r2.get("answer", "")))


if __name__ == "__main__":
    main()
