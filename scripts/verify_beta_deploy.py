#!/usr/bin/env python3
"""Smoke-check Beta deploy — run after Railway + Vercel beta are live.

Usage:
  py scripts/verify_beta_deploy.py
  py scripts/verify_beta_deploy.py --frontend https://beta.genesis-ai-engine.com --backend https://xxx.up.railway.app

Env (optional):
  BETA_FRONTEND_URL, BETA_BACKEND_URL
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _get(url: str, timeout: float = 15) -> tuple[int, str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")[:2000]
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")[:500]


def _post_json(url: str, payload: dict, timeout: float = 60) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")[:2000]
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")[:500]


def main() -> int:
    parser = argparse.ArgumentParser(description="Beta deploy smoke test")
    parser.add_argument("--frontend", default=os.getenv("BETA_FRONTEND_URL", "").strip())
    parser.add_argument("--backend", default=os.getenv("BETA_BACKEND_URL", "").strip())
    args = parser.parse_args()

    fe = args.frontend.rstrip("/")
    be = args.backend.rstrip("/")
    if not fe or not be:
        print(
            "ERROR: set --frontend and --backend or BETA_FRONTEND_URL / BETA_BACKEND_URL",
            file=sys.stderr,
        )
        return 2

    failures: list[str] = []

    code, body = _get(f"{be}/api/status")
    print(f"[backend] GET /api/status → {code}")
    if code != 200:
        failures.append("backend /api/status")
    else:
        try:
            data = json.loads(body)
            print(f"  git_commit={data.get('git_commit')} uptime_sec={data.get('uptime_sec')}")
        except json.JSONDecodeError:
            pass

    code, _ = _get(f"{be}/api/public/genesis-ai/attachments/policy?visitor_id=beta-smoke")
    print(f"[backend] GET attachments/policy → {code}")
    if code != 200:
        failures.append("attachments/policy (Expert Review path)")

    code, _ = _get(f"{be}/api/public/genesis-ai/status")
    print(f"[backend] GET genesis-ai/status → {code}")
    if code != 200:
        failures.append("genesis-ai/status")

    code, body = _get(f"{be}/api/public/genesis-ai/tts/status")
    print(f"[backend] GET genesis-ai/tts/status → {code}")
    if code != 200:
        failures.append("genesis-ai/tts/status (Voice backend)")
    else:
        try:
            tts = json.loads(body)
            print(f"  tts_ready={tts.get('ready')} providers={tts.get('providers')}")
        except json.JSONDecodeError:
            pass

    code, body = _post_json(
        f"{be}/api/public/genesis-ai",
        {"question": "Beta smoke: ответь одним словом «ок»", "history": [], "visitor_id": "beta-smoke"},
    )
    print(f"[backend] POST genesis-ai → {code}")
    if code != 200:
        failures.append("POST genesis-ai (chat)")
    else:
        try:
            ans = json.loads(body).get("answer", "")[:120]
            print(f"  answer preview: {ans!r}")
        except json.JSONDecodeError:
            pass

    code, _ = _get(f"{fe}/site")
    print(f"[frontend] GET /site → {code}")
    if code != 200:
        failures.append("frontend /site")

    if failures:
        print("\nFAIL:", ", ".join(failures))
        return 1

    print(f"\nOK Beta smoke passed\n  Frontend: {fe}/site\n  Backend:  {be}/api/status")
    print("  Manual in browser: PDF upload, Voice mic, Dictation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
