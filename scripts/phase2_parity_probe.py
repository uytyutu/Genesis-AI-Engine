#!/usr/bin/env python3
"""Phase 2 parity probe — status + debug routing (read-only)."""

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

DEFAULT_QUESTIONS = [
    "Что там в Америке с погодой?",
    "Кто такой Наполеон?",
    "Расскажи про космос",
    "Ты чего так общаешься?",
    "Можно проще?",
    "Йо",
    "Привет",
]


def _get_status(base: str) -> dict:
    with urllib.request.urlopen(f"{base.rstrip('/')}/api/public/genesis-ai/status", timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def _chat(base: str, question: str, *, debug: bool) -> dict:
    vid = f"phase2-{uuid.uuid4().hex[:8]}"
    url = f"{base.rstrip('/')}/api/public/genesis-ai"
    if debug:
        url += "?debug=true"
    payload = json.dumps(
        {"question": question, "history": [], "visitor_id": vid},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="Phase 2 Groq parity probe")
    p.add_argument(
        "--base",
        default="https://beta.genesis-ai-engine.com",
        help="API base (default: beta)",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="Request ?debug=true (localhost / GENESIS_DEV_MODE only)",
    )
    args = p.parse_args()
    base = args.base.rstrip("/")

    print(f"=== Phase 2 parity probe: {base} ===\n")
    try:
        st = _get_status(base)
    except Exception as exc:
        print(f"status ERROR: {exc}")
        return 1

    llm = st.get("llm_configured")
    cloud = (st.get("workforce") or {}).get("cloud_employees_ready", 0)
    print(f"llm_configured: {llm}")
    print(f"cloud_employees_ready: {cloud}")
    print(f"brain_version: {st.get('brain_version')}\n")

    ok_status = bool(llm) and int(cloud or 0) >= 1
    print(f"[{'OK' if ok_status else 'FAIL'}] status gate (llm + cloud)\n")

    print("| Question | provider | score | cloud | fallback |")
    print("|----------|----------|-------|-------|----------|")
    groq_hits = 0
    for q in DEFAULT_QUESTIONS:
        try:
            body = _chat(base, q, debug=args.debug)
        except urllib.error.HTTPError as exc:
            print(f"| {q[:40]} | HTTP {exc.code} | - | - | - |")
            continue
        except Exception as exc:
            print(f"| {q[:40]} | ERROR | - | - | {exc} |")
            continue
        ans = (body.get("answer") or "").strip()
        dbg = body.get("debug") or {}
        prov = dbg.get("workforce_selected") or dbg.get("provider") or "?"
        score = dbg.get("provider_score", "-")
        cloud_used = dbg.get("cloud_llm_used", "?")
        fb = "yes" if "Слушаю Вас" in ans else "no"
        if prov == "groq":
            groq_hits += 1
        print(f"| {q[:40]} | {prov} | {score} | {cloud_used} | {fb} |")

    print(f"\nGroq-selected turns: {groq_hits}/{len(DEFAULT_QUESTIONS)}")
    return 0 if ok_status else 2


if __name__ == "__main__":
    raise SystemExit(main())
