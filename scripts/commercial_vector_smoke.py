#!/usr/bin/env python3
"""Commercial Vector smoke — three scenarios via live API (Genesis stack).

Run while Genesis.exe / backend is up:
  py -3.12 scripts/commercial_vector_smoke.py

Checks Create Website / Analysis / Repair speech; no CMS auto-fix promises.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

BASES = (
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
)

SCENARIOS = [
    {
        "id": "create_website",
        "question": (
            "Хочу заказать сайт для клининговой компании в Берлине. "
            "Объясни пакеты Basic, Business и Premium и какой выбрать."
        ),
        "must_any": ("basic", "business", "premium", "350", "650", "1200"),
        "forbid_positive_cms": True,
    },
    {
        "id": "analysis",
        "question": (
            "Я проверил сайт: нет HTTPS, нет CTA, медленная загрузка. "
            "Объясни простым языком, что это значит для бизнеса."
        ),
        "must_any": ("https", "cta", "медлен", "проблем", "сайт"),
        "forbid_positive_cms": True,
    },
    {
        "id": "repair",
        "question": (
            "Смета ремонта 349 € (Repair Standard). Что входит и почините ли вы "
            "автоматически любой WordPress или Wix без моего участия?"
        ),
        "must_any": ("ремонт", "349", "оператор", "не обеща", "cms", "wordpress", "смет"),
        "forbid_positive_cms": True,
    },
]


def _post(base: str, question: str, visitor_id: str) -> dict:
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
        f"{base}/api/public/genesis-ai",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as res:
        return json.loads(res.read().decode("utf-8"))


def _answer_text(body: dict) -> str:
    for key in ("answer", "reply", "text", "message", "content"):
        v = body.get(key)
        if isinstance(v, str) and v.strip():
            return v
    # nested
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    for key in ("answer", "reply", "text"):
        v = data.get(key)
        if isinstance(v, str) and v.strip():
            return v
    return json.dumps(body, ensure_ascii=False)[:2000]


def _has_positive_cms_promise(text: str) -> bool:
    low = text.casefold()
    # Negations are OK
    if "не обеща" in low or "не обещаем" in low or "do not promise" in low:
        return False
    bad = (
        "автоматически починим любой wordpress",
        "ai fixes everything",
        "сами починим любой cms без",
        "полностью автоматически исправим ваш wordpress",
    )
    return any(b in low for b in bad)


def main() -> int:
    base_ok = None
    for b in BASES:
        try:
            urllib.request.urlopen(f"{b}/api/public/genesis-ai/workforce-health?force=1", timeout=8)
            base_ok = b
            break
        except Exception:
            try:
                # frontend rewrite may still proxy
                urllib.request.urlopen(f"{b}/site", timeout=5)
                base_ok = b
                break
            except Exception:
                continue
    if not base_ok:
        print("FAIL live_vector — Genesis stack not reachable on :8000/:3000")
        print("Start Genesis.exe → Запустить → then re-run this script.")
        return 1

    print(f"Using {base_ok}")
    fails = 0
    for sc in SCENARIOS:
        try:
            vid = f"commercial-smoke-{sc['id']}-{os.getpid()}"
            body = _post(base_ok, sc["question"], visitor_id=vid)
            text = _answer_text(body)
            low = text.casefold()
            hit = any(m.casefold() in low for m in sc["must_any"])
            cms_bad = _has_positive_cms_promise(text) if sc.get("forbid_positive_cms") else False
            ok = hit and not cms_bad and len(text.strip()) > 40
            mark = "PASS" if ok else "FAIL"
            if not ok:
                fails += 1
            print(f"[{mark}] {sc['id']} — chars={len(text)} hit={hit} cms_bad={cms_bad}")
            print(f"  Q: {sc['question'][:80]}…")
            print(f"  A: {text[:280].replace(chr(10), ' ')}")
        except Exception as exc:
            fails += 1
            print(f"[FAIL] {sc['id']} — {type(exc).__name__}: {exc}")

    if fails:
        print(f"\nOVERALL FAIL ({fails} scenarios)")
        return 1
    print("\nOVERALL PASS — Vector commercial speech")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
