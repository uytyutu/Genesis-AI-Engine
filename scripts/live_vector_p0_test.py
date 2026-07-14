"""P0 live Vector test — five CEO scenarios via frontend rewrite."""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCENARIOS = [
    "Привет",
    "Как дела?",
    "Расскажи о себе",
    "Хочу открыть кофейню",
    "Почему небо голубое?",
]

MAX_SEC = 25.0
BASE = "http://127.0.0.1:3000"


def post_chat(question: str, visitor_id: str) -> dict:
    payload = json.dumps(
        {
            "question": question,
            "history": [],
            "visitor_id": visitor_id,
            "ui_locale": "ru",
            "assistant_locale": "ru",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/api/public/genesis-ai",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=int(MAX_SEC)) as res:
        return json.loads(res.read().decode("utf-8", errors="replace"))


def fetch_health() -> dict:
    with urllib.request.urlopen(f"{BASE}/api/public/genesis-ai/workforce-health?force=1", timeout=60) as res:
        return json.loads(res.read().decode("utf-8", errors="replace"))


def main() -> int:
    print("=== WORKFORCE HEALTH ===")
    try:
        health = fetch_health()
        print("viable_cloud:", health.get("viable_cloud"))
        print("why_fallback:", health.get("why_fallback"))
        for row in health.get("employees") or []:
            print(
                f"  {row.get('employee_id')}: available={row.get('available')} "
                f"responds={row.get('responds')} latency_ms={row.get('latency_ms')} "
                f"excluded={row.get('excluded_reason')}"
            )
    except Exception as exc:
        print("HEALTH FAIL:", type(exc).__name__, exc)
        return 2

    print("\n=== LIVE CHAT (5 scenarios) ===")
    failed = 0
    for i, q in enumerate(SCENARIOS, 1):
        t0 = time.perf_counter()
        try:
            data = post_chat(q, f"p0-live-{i}")
            elapsed = time.perf_counter() - t0
            answer = (data.get("answer") or "").strip()
            ok = bool(answer) and elapsed <= MAX_SEC
            status = "PASS" if ok else "FAIL"
            if not ok:
                failed += 1
            preview = answer[:120].replace("\n", " ")
            print(f"{status} [{i}/5] {elapsed:4.1f}s | {q!r} -> {preview!r}")
        except Exception as exc:
            failed += 1
            elapsed = time.perf_counter() - t0
            print(f"FAIL [{i}/5] {elapsed:4.1f}s | {q!r} -> {type(exc).__name__}: {exc}")

    print(f"\nResult: {len(SCENARIOS) - failed}/{len(SCENARIOS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
