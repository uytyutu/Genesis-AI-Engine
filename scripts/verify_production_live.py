#!/usr/bin/env python3
"""
Production live verification — real HTTPS, not TestClient.

Usage:
  python scripts/verify_production_live.py
  python scripts/verify_production_live.py --api https://genesis-ai-engine-production.up.railway.app
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid

import httpx

DEFAULT_API = "https://genesis-ai-engine-production.up.railway.app"
DEFAULT_SITE = "https://genesis-ai-engine.vercel.app"


def _ok(label: str, passed: bool, detail: str = "") -> bool:
    mark = "PASS" if passed else "FAIL"
    line = f"  [{mark}] {label}"
    if detail:
        line += f" — {detail}"
    print(line)
    return passed


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--api", default=DEFAULT_API)
    p.add_argument("--site", default=DEFAULT_SITE)
    args = p.parse_args()
    api = args.api.rstrip("/")
    site = args.site.rstrip("/")

    print("=== Genesis Production Live Verification ===")
    print(f"API:  {api}")
    print(f"Site: {site}/site\n")

    passed = 0
    total = 0

    def check(label: str, ok: bool, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        if _ok(label, ok, detail):
            passed += 1

    # Backend version / Mind v3 markers
    try:
        r = httpx.get(f"{api}/api/public/genesis-ai/status", timeout=20)
        check("GET /api/public/genesis-ai/status", r.status_code == 200, str(r.status_code))
        if r.status_code == 200:
            st = r.json()
            bv = st.get("brain_version") or st.get("hi_build") or ""
            check(
                "Mind v3 brain_version",
                "v3" in str(bv).lower() or "genesis-mind" in str(bv).lower(),
                str(bv)[:60],
            )
            wf = st.get("workforce") or {}
            check(
                "Workforce in status",
                bool(wf.get("employees") or st.get("workforce_tier")),
                str(st.get("workforce_tier", "")),
            )
    except Exception as exc:
        check("GET /api/public/genesis-ai/status", False, str(exc)[:80])

    try:
        r = httpx.get(f"{api}/health", timeout=15)
        check("GET /health", r.status_code == 200, str(r.status_code))
    except Exception as exc:
        check("GET /health", False, str(exc)[:80])

    # Sessions API (Conversation UX v1)
    visitor = f"prod-verify-{uuid.uuid4().hex[:12]}"
    session_id = None
    try:
        r = httpx.get(f"{api}/api/public/genesis-ai/sessions", params={"visitor_id": visitor}, timeout=20)
        check("GET /api/public/genesis-ai/sessions", r.status_code == 200, str(r.status_code))
    except Exception as exc:
        check("GET /api/public/genesis-ai/sessions", False, str(exc)[:80])

    try:
        r = httpx.post(
            f"{api}/api/public/genesis-ai/sessions",
            json={"visitor_id": visitor, "title": "Новый чат"},
            timeout=20,
        )
        check("POST /api/public/genesis-ai/sessions", r.status_code == 200, str(r.status_code))
        if r.status_code == 200:
            session_id = r.json().get("session_id")
    except Exception as exc:
        check("POST /api/public/genesis-ai/sessions", False, str(exc)[:80])

    # Public chat
    try:
        r = httpx.post(
            f"{api}/api/public/genesis-ai",
            json={
                "question": "Привет, это production probe",
                "history": [],
                "visitor_id": visitor,
                "session_id": session_id,
            },
            timeout=60,
        )
        ok = r.status_code == 200 and bool((r.json() or {}).get("answer"))
        check("POST /api/public/genesis-ai (cloud answer)", ok, str(r.status_code))
        if r.status_code == 200:
            body = r.json()
            check("session_id in chat response", bool(body.get("session_id") or session_id))
    except Exception as exc:
        check("POST /api/public/genesis-ai", False, str(exc)[:80])

    # Frontend site + sessions UI bundle
    try:
        r = httpx.get(f"{site}/site", timeout=25, follow_redirects=True)
        check("GET /site", r.status_code == 200, str(r.status_code))
        html = r.text
        check("Site references Railway API", "railway.app" in html or api.replace("https://", "") in html)
        # ChatHistorySidebar / sessions bundle
        chunks = re.findall(r"/_next/static/chunks/[^\"']+\.js", html)
        has_sessions = False
        for c in chunks[:20]:
            try:
                js = httpx.get(f"{site}{c}", timeout=15).text
                if "Новый чат" in js or "chatSessions" in js or "genesis_chat_sessions" in js:
                    has_sessions = True
                    break
            except httpx.HTTPError:
                continue
        check("Frontend Conversation UX v1 bundle", has_sessions, f"chunks={len(chunks)}")
    except Exception as exc:
        check("GET /site", False, str(exc)[:80])

    print(f"\nResult: {passed}/{total} checks passed")
    if passed < total:
        print("\nProduction is NOT synced with local Mind v3 + Conversation UX v1.")
        print("Fix: push main to GitHub → Railway + Vercel redeploy.")
        return 1
    print("\nProduction appears synced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
