#!/usr/bin/env python3
"""Live beta verification — 5 CEO scenarios (routing + UI markers)."""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request

BASE = "https://beta.genesis-ai-engine.com"
VISITOR = "beta-verify-scenarios-001"
FALLBACK_MARKERS = (
    "Слушаю Вас — расскажите, что для Вас сейчас важнее всего",
    "Опишите, что именно хотите понять — отвечу доступно, без воды",
)


def post(question: str, history: list[dict]) -> tuple[str, int]:
    payload = {"question": question, "history": history, "visitor_id": VISITOR}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/api/public/genesis-ai",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return (data.get("answer") or "").strip(), resp.status
    except urllib.error.HTTPError as exc:
        return exc.read().decode("utf-8", errors="replace")[:300], exc.code


def has_fallback(text: str) -> bool:
    return any(m in text for m in FALLBACK_MARKERS)


def fetch_site_html() -> str:
    return urllib.request.urlopen(f"{BASE}/site", timeout=20).read().decode("utf-8", errors="replace")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"=== Beta live check: {BASE} ===\n")

    # UI markers in HTML (SSR welcome state)
    html = fetch_site_html()
    build_id = re.search(r"<!--([A-Za-z0-9_-]+)-->", html)
    print(f"Vercel build id: {build_id.group(1) if build_id else '?'}")
    print(f"  aria-label Home (clickable logo): {'aria-label=\"Home\"' in html or 'aria-label=\"Главная\"' in html}")
    print(f"  welcome collapsed hints: {'chatCollapsed' not in html}")  # client state

  # chunk probe for latest routing strings
    chunk_url = f"{BASE}/_next/static/chunks/6754-803d312b88671db9.js"
    try:
        chunk = urllib.request.urlopen(chunk_url, timeout=15).read().decode("utf-8", errors="replace")
        print(f"  chunk has onConversationActive pattern: {'onConversationActive' in chunk or 'genesis:home' in chunk}")
    except Exception as exc:
        print(f"  chunk probe failed: {exc}")

    print()

    results: list[tuple[str, bool, str]] = []

    # 1. Thread follow-up
    h1: list[dict] = [{"role": "assistant", "content": "Привет! Рад на связи."}]
    a1, c1 = post("В смысле рад на связи?", h1)
    ok1 = c1 == 200 and not has_fallback(a1) and (
        "рад" in a1.lower() or "имел" in a1.lower() or "разговор" in a1.lower()
    )
    results.append(("1. Привет → В смысле рад на связи?", ok1, a1[:220]))
    print(f"[{'PASS' if ok1 else 'FAIL'}] 1. thread follow-up (HTTP {c1})")
    print(f"     {a1[:280]}\n")

    # 2. Earth curiosity
    a2, c2 = post("Почему Земля круглая?", [])
    ok2 = c2 == 200 and not has_fallback(a2) and any(
        w in a2.lower() for w in ("земл", "гравитац", "сфер", "округл")
    )
    results.append(("2. Почему Земля круглая?", ok2, a2[:220]))
    print(f"[{'PASS' if ok2 else 'FAIL'}] 2. earth curiosity (HTTP {c2})")
    print(f"     {a2[:280]}\n")

    # 3. Weather America
    a3, c3 = post("Что там с погодой в Америке?", [])
    ok3 = c3 == 200 and not has_fallback(a3) and (
        "погод" in a3.lower() or "сша" in a3.lower() or "америк" in a3.lower()
    )
    results.append(("3. Погода в Америке", ok3, a3[:220]))
    print(f"[{'PASS' if ok3 else 'FAIL'}] 3. weather america (HTTP {c3})")
    print(f"     {a3[:280]}\n")

    # 4. Йо casual
    a4, c4 = post("Йо", [])
    ok4 = c4 == 200 and not has_fallback(a4) and len(a4) >= 12
    results.append(("4. Йо", ok4, a4[:220]))
    print(f"[{'PASS' if ok4 else 'FAIL'}] 4. casual Йо (HTTP {c4})")
    print(f"     {a4[:280]}\n")

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"=== API scenarios: {passed}/{len(results)} PASS ===")
    print("UI cycle (back/logo/history) requires phone or browser — not API-testable here.")

    if passed < len(results):
        print("\nNOTE: failures may mean Railway backend not redeployed yet (routing is backend).")
        print("      Frontend UI fixes deploy via Vercel separately.")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
