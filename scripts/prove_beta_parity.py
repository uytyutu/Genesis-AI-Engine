#!/usr/bin/env python3
"""Prove beta parity — status + 3 CEO questions with provider (read-only)."""

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

QUESTIONS = (
    "Почему Земля круглая?",
    "Хочу открыть стоматологическую клинику.",
    "Что там с погодой в США?",
)


def _get_status(base: str) -> dict:
    with urllib.request.urlopen(f"{base.rstrip('/')}/api/public/genesis-ai/status", timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def _chat(base: str, question: str) -> dict:
    vid = f"prove-{uuid.uuid4().hex[:8]}"
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
    p = argparse.ArgumentParser(description="Prove beta Groq parity")
    p.add_argument(
        "--base",
        default="https://beta.genesis-ai-engine.com",
        help="API base (default: beta)",
    )
    p.add_argument(
        "--label",
        default="beta",
        help="Label in report (beta / localhost)",
    )
    args = p.parse_args()
    base = args.base.rstrip("/")

    print(f"Railway deploy:")
    try:
        st = _get_status(base)
        deploy_ok = True
    except Exception as exc:
        print(f"❌ Failed — status unreachable: {exc}")
        return 1

    llm = bool(st.get("llm_configured"))
    cloud = int((st.get("workforce") or {}).get("cloud_employees_ready") or 0)
    print(f"{'✅' if llm and cloud >= 1 else '❌'} {'Success' if llm and cloud >= 1 else 'Not parity yet'}")
    print()
    print("Status API:")
    print(f"llm_configured = {llm}")
    print(f"cloud_employees_ready = {cloud}")
    print(f"brain_version = {st.get('brain_version', '?')}")
    print()

    for i, q in enumerate(QUESTIONS, 1):
        print(f"Вопрос {i}:")
        print(q)
        try:
            body = _chat(base, q)
        except urllib.error.HTTPError as exc:
            print(f"Provider: HTTP {exc.code}")
            print()
            continue
        except Exception as exc:
            print(f"Provider: ERROR ({exc})")
            print()
            continue
        prov = body.get("provider") or "unknown"
        ans = (body.get("answer") or "").strip().replace("\n", " ")
        if len(ans) > 100:
            ans = ans[:97] + "..."
        print(f"Provider: {prov}")
        print(f"Answer: {ans}")
        print()

    if not llm or cloud < 1:
        print("BLOCKER: GENESIS_GROQ_API_KEY missing on Railway genesis-beta.")
        print("CEO one-liner: py scripts/push_groq_to_railway.py")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
