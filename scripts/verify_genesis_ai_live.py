"""Live verification of Genesis AI — run: python scripts/verify_genesis_ai_live.py"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.env_loader import load_local_env
from app.integration.genesis_ai_knowledge import build_system_prompt
from app.integration.genesis_ai_service import GenesisAIService

LOCAL = os.getenv("GENESIS_VERIFY_URL", "http://localhost:8000")
PROD = "https://genesis-ai-engine-production.up.railway.app"

TESTS = [
    "Я сегодня хорошо поспал.",
    "Расскажи про чёрные дыры.",
    "Хочу сайт для кофейни.",
    "Не знаю, как лучше.",
    "Хочу пользоваться Genesis Studio.",
]


def ask_api(base: str, question: str, history: list | None = None) -> dict:
    r = httpx.post(
        f"{base}/api/public/genesis-ai",
        json={"question": question, "history": history or []},
        timeout=60.0,
    )
    return {"status": r.status_code, "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:500]}


def status_api(base: str) -> dict:
    r = httpx.get(f"{base}/api/public/genesis-ai/status", timeout=15.0)
    return r.json() if r.status_code == 200 else {"error": r.status_code, "text": r.text[:200]}


def main() -> None:
    load_local_env()
    svc = GenesisAIService([])
    print("=== Q1: Real LLM configured (local .env)? ===")
    print("НЕТ" if not svc.llm_configured() else "ДА")
    key_set = bool(os.getenv("GENESIS_LLM_API_KEY", "").strip())
    print(f"GENESIS_LLM_API_KEY in .env: {'set' if key_set else 'EMPTY'}")

    print("\n=== Q1b: Production API status ===")
    try:
        prod_st = status_api(PROD)
        print(json.dumps(prod_st, ensure_ascii=False))
        prod_llm = prod_st.get("llm_configured") if isinstance(prod_st, dict) else None
        print("Production real LLM:", "ДА" if prod_llm else "НЕТ")
    except Exception as e:
        print("Production unreachable:", e)

    print("\n=== Q5: Old Concierge in public path? ===")
    src = Path(ROOT / "dashboard/backend/app/integration/genesis_ai_service.py").read_text(encoding="utf-8")
    print("НЕТ" if "ConciergeService" not in src else "ДА (import still present)")

    print("\n=== Q1c: Local running server status ===")
    try:
        print(json.dumps(status_api(LOCAL), ensure_ascii=False))
    except Exception as e:
        print("Local server down:", e)

    print("\n=== LIVE API RESPONSES (localhost) ===")
    history: list[dict] = []
    for i, q in enumerate(TESTS, 1):
        try:
            res = ask_api(LOCAL, q, history)
            body = res["body"]
            if isinstance(body, dict):
                ans = body.get("answer", body)
                mode = body.get("mode", "?")
                print(f"\n--- Test {i}: {q}")
                print(f"mode: {mode}")
                print(f"answer:\n{ans}")
                if isinstance(ans, str):
                    history.append({"role": "user", "content": q})
                    history.append({"role": "assistant", "content": ans})
            else:
                print(f"\n--- Test {i} ERROR ---\n{res}")
        except Exception as e:
            print(f"\n--- Test {i} FAILED: {e}")

    print("\n=== Q7: Memory test ===")
    mem_history = [{"role": "user", "content": "Меня зовут Рамиш."}]
    try:
        r1 = ask_api(LOCAL, "Меня зовут Рамиш.", [])
        a1 = r1["body"].get("answer", "") if isinstance(r1["body"], dict) else ""
        mem_history.append({"role": "assistant", "content": a1})
        for _ in range(3):
            mem_history.append({"role": "user", "content": "Расскажи что-нибудь интересное про космос в двух предложениях."})
            r_mid = ask_api(LOCAL, mem_history[-1]["content"], mem_history[:-1])
            if isinstance(r_mid["body"], dict):
                mem_history.append({"role": "assistant", "content": r_mid["body"].get("answer", "")})
        r2 = ask_api(LOCAL, "Как меня зовут?", mem_history)
        print("Q: Как меня зовут?")
        if isinstance(r2["body"], dict):
            print("A:", r2["body"].get("answer"))
            print("mode:", r2["body"].get("mode"))
        else:
            print(r2)
    except Exception as e:
        print("Memory test failed:", e)

    prompt_path = ROOT / "scripts" / "_genesis_system_prompt_live.txt"
    prompt_path.write_text(build_system_prompt([]), encoding="utf-8")
    print(f"\n=== Q6: Full system prompt written to ===\n{prompt_path}")
    print(f"Length: {len(build_system_prompt([]))} chars")


if __name__ == "__main__":
    main()
