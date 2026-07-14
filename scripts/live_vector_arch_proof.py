"""Agent live proof — 3-question Vector session with dev_stats (CEO arch review)."""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

QUESTIONS = [
    "Почему Virtus Core отличается от ChatGPT?",
    "Какие слабые стороны у Virtus Core сегодня?",
    "Почему ты так считаешь?",
]

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3000"
CHAT_URL = f"{BASE}/api/public/genesis-ai?debug=true"
VISITOR = "agent-live-proof-001"

FAIL_PROVIDERS = frozenset({"genesis-instant", "genesis-identity"})


def fetch_health() -> dict:
    with urllib.request.urlopen(
        f"{BASE}/api/public/genesis-ai/workforce-health?force=1", timeout=60
    ) as res:
        return json.loads(res.read().decode("utf-8", errors="replace"))


def post_chat(question: str, history: list[dict]) -> dict:
    payload = json.dumps(
        {
            "question": question,
            "history": history,
            "visitor_id": VISITOR,
            "ui_locale": "ru",
            "assistant_locale": "ru",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        CHAT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as res:
        return json.loads(res.read().decode("utf-8", errors="replace"))


def turn_passes(data: dict, stats: dict) -> tuple[bool, str]:
    answer = (data.get("answer") or "").strip()
    if not answer:
        return False, "empty answer"
    worker = str(stats.get("worker") or data.get("provider") or "")
    if worker in FAIL_PROVIDERS:
        return False, f"template provider {worker}"
    if stats.get("fallback") and worker == "genesis-local":
        return False, "genesis-local fallback with cloud available"
    if not stats.get("cloud_llm_used") and worker not in (
        "groq",
        "gemini",
        "ollama",
        "openrouter",
        "anthropic",
        "openai",
        "execution",
    ):
        return False, f"no cloud_llm_used (worker={worker})"
    return True, "ok"


def main() -> int:
    print("=== WORKFORCE HEALTH ===")
    try:
        health = fetch_health()
        print("viable_cloud:", health.get("viable_cloud"))
        print("why_fallback:", health.get("why_fallback"))
        for row in health.get("employees") or []:
            print(
                f"  {row.get('employee_id')}: available={row.get('available')} "
                f"responds={row.get('responds')} latency_ms={row.get('latency_ms')}"
            )
    except Exception as exc:
        print("HEALTH FAIL:", type(exc).__name__, exc)
        return 2

    print("\n=== LIVE 3-QUESTION SESSION (debug=true) ===")
    history: list[dict] = []
    failed = 0
    for i, q in enumerate(QUESTIONS, 1):
        t0 = time.perf_counter()
        try:
            data = post_chat(q, history)
            elapsed = time.perf_counter() - t0
            answer = (data.get("answer") or "").strip()
            dbg = data.get("debug") or {}
            stats = dbg.get("dev_stats") or {}
            worker = stats.get("worker") or data.get("provider") or "—"
            latency = stats.get("elapsed_sec")
            if latency is None:
                latency = round(elapsed, 2)
            planner = stats.get("planner") or "—"
            fallback = stats.get("fallback_label") or (
                "да" if stats.get("fallback") else "нет"
            )
            ok, reason = turn_passes(data, stats)
            status = "PASS" if ok else "FAIL"
            if not ok:
                failed += 1
            print(f"--- Turn {i}: {q!r} ---")
            print(f"Status: {status} ({reason})")
            print(f"Capability: {stats.get('llm_capability') or '—'}")
            print(f"Provider: {worker}")
            print(f"Latency: {latency} s")
            print(f"Planner: {planner}")
            print(f"Fallback: {fallback}")
            print(f"cloud_llm_used: {stats.get('cloud_llm_used')}")
            preview = answer[:200].replace("\n", " ")
            print(f"Answer preview: {preview!r}")
            if stats.get("reasons"):
                print("Reasons:", stats.get("reasons"))
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": answer})
            print()
        except Exception as exc:
            failed += 1
            elapsed = time.perf_counter() - t0
            print(f"--- Turn {i}: {q!r} ---")
            print(f"Status: FAIL ({type(exc).__name__}: {exc}) after {elapsed:.1f}s")
            print()

    print(f"RESULT: {len(QUESTIONS) - failed}/{len(QUESTIONS)} architectural PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
