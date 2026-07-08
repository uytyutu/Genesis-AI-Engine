"""
Browser acceptance scenarios — same messages as CTO checklist.
Run against live API (backend must be restarted with latest code).

Usage:
  py scripts/browser_acceptance_api.py
  py scripts/browser_acceptance_api.py --base http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

try:
    import httpx
except ImportError:
    print("pip install httpx")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = [
    "Привет",
    "Как дела",
    "Давай поговорим",
    "Стой",
    "Остановись",
    "Придумай бизнес",
    "Мне грустно",
    "Я устал",
    "Что такое квантовая физика",
    "Хочу открыть кофейню",
    "Придкмай бизнесс",
    "Хачу сайт",
]

BANNED = (
    "расскажите о задаче",
    "я — genesis",
    "что для вас сейчас важнее",
    "notallowederror",
    "permission denied",
)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://127.0.0.1:8000")
    args = p.parse_args()
    base = args.base.rstrip("/")
    vid = f"accept-{uuid.uuid4().hex[:8]}"
    history: list[dict[str, str]] = []
    out_path = ROOT / "scripts" / "browser_acceptance_results.json"
    results: list[dict] = []

    with httpx.Client(timeout=60.0) as client:
        st = client.get(f"{base}/api/public/genesis-ai/status").json()
        print(f"hi_build={st.get('hi_build')} mode={st.get('mode')}")

        for msg in SCENARIOS:
            r = client.post(
                f"{base}/api/public/genesis-ai",
                json={
                    "question": msg,
                    "history": history,
                    "visitor_id": vid,
                },
            )
            data = r.json()
            answer = (data.get("answer") or "").strip()
            low = answer.lower()
            bad = [b for b in BANNED if b in low]
            results.append({"user": msg, "answer": answer, "violations": bad})
            history.append({"role": "user", "content": msg})
            history.append({"role": "assistant", "content": answer})
            status = "FAIL" if bad else "OK"
            print(f"[{status}] {msg} -> {answer[:80]}...")
            if bad:
                print(f"       banned: {bad}")

    violations = [r for r in results if r["violations"]]
    out_path.write_text(json.dumps({"visitor_id": vid, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")
    print(f"Total violations: {len(violations)}")
    if violations:
        sys.exit(1)


if __name__ == "__main__":
    main()
