#!/usr/bin/env python3
"""Deploy parity report — /status + 3 scenarios (read-only)."""

from __future__ import annotations

import argparse
import io
import json
import sys
import uuid
import urllib.error
import urllib.request

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCENARIOS = (
    ("стоматология", "Хочу открыть стоматологическую клинику."),
    ("погода", "Что там с погодой в США?"),
    ("общение", "Привет, как дела? Расскажи о себе."),
)


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def _chat(base: str, question: str) -> dict:
    vid = f"deploy-{uuid.uuid4().hex[:8]}"
    payload = json.dumps(
        {"question": question, "history": [], "visitor_id": vid},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base.rstrip('/')}/api/public/genesis-ai",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--backend", default="https://renewed-reprieve-production.up.railway.app")
    p.add_argument("--frontend", default="https://beta.genesis-ai-engine.com")
    args = p.parse_args()
    backend = args.backend.rstrip("/")

    print("Deploy:")
    try:
        status = _get(f"{backend}/status")
        deploy_ok = status.get("status") in ("ok", "degraded")
        print(f"{'✅' if deploy_ok else '❌'} {'Success' if deploy_ok else 'Failed'}")
    except Exception as exc:
        print(f"❌ Failed — {exc}")
        return 1

    checks = status.get("checks") or {}
    llm_prov = checks.get("llm_providers") or {}
    workforce = checks.get("workforce") or {}
    groq_state = llm_prov.get("groq", "?")

    print()
    print("Groq:")
    if groq_state == "ready":
        print("✅ Registered")
    elif groq_state == "not_configured":
        print("❌ Skipped — missing API key (GENESIS_GROQ_API_KEY)")
    else:
        print(f"⚠️ {groq_state}")

    print()
    print("Status:")
    llm = workforce.get("llm_configured")
    cloud = workforce.get("cloud_employees_ready", 0)
    print(f"llm_configured={llm}")
    print(f"cloud_employees_ready={cloud}")
    print(f"llm_providers={json.dumps(llm_prov, ensure_ascii=False)}")

    print()
    all_pass = bool(llm) and int(cloud or 0) >= 1
    for label, question in SCENARIOS:
        print(f"Scenario ({label}):")
        try:
            body = _chat(args.frontend.rstrip("/"), question)
        except Exception as exc:
            print(f"  ❌ ERROR {exc}")
            all_pass = False
            continue
        prov = body.get("provider") or "unknown"
        ans = (body.get("answer") or "").strip()
        dental_ok = "стомат" in ans.lower() or "клиник" in ans.lower()
        if label == "стоматология":
            ok = prov == "groq" and dental_ok
        else:
            ok = prov == "groq"
        print(f"  provider={prov}")
        print(f"  {'PASS' if ok else 'FAIL'}")
        if not ok:
            all_pass = False

    print()
    print("Оставшиеся проблемы:")
    if groq_state != "ready":
        print("- Groq: ключ не в Railway Variables")
    if llm_prov.get("genesis-local") == "ready" and groq_state != "ready":
        print("- Все запросы идут через genesis-local (offline)")
    if not all_pass:
        print("- A+B+C parity не закрыт")
    else:
        print("- (none — parity OK)")

    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
