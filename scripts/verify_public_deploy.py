#!/usr/bin/env python3
"""P-001 Public Deploy verification — Mission 1 purchase path on HTTPS.

Usage (from repo root):
  py scripts/verify_public_deploy.py
  py scripts/verify_public_deploy.py --frontend https://beta.genesis-ai-engine.com --backend https://renewed-reprieve-production.up.railway.app

Env (optional):
  PUBLIC_FRONTEND_URL, PUBLIC_BACKEND_URL
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request


DEFAULT_FRONTEND = "https://beta.genesis-ai-engine.com"
DEFAULT_BACKEND = "https://renewed-reprieve-production.up.railway.app"


def _get(url: str, timeout: float = 20) -> tuple[int, str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")[:800]


def _post_json(url: str, payload: dict, timeout: float = 30) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")[:800]


def main() -> int:
    parser = argparse.ArgumentParser(description="P-001 public deploy smoke test")
    parser.add_argument("--frontend", default=os.getenv("PUBLIC_FRONTEND_URL", DEFAULT_FRONTEND).strip())
    parser.add_argument("--backend", default=os.getenv("PUBLIC_BACKEND_URL", DEFAULT_BACKEND).strip())
    args = parser.parse_args()

    fe = args.frontend.rstrip("/")
    be = args.backend.rstrip("/")
    failures: list[str] = []
    passed = 0
    total = 0

    def check(label: str, ok: bool, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        mark = "PASS" if ok else "FAIL"
        line = f"  [{mark}] {label}"
        if detail:
            line += f" — {detail}"
        print(line)
        if ok:
            passed += 1
        else:
            failures.append(label)

    print("=== P-001 Public Deploy Verification ===")
    print(f"Frontend: {fe}")
    print(f"Backend:  {be}\n")

    check("Frontend HTTPS", fe.startswith("https://"))
    check("Backend HTTPS", be.startswith("https://"))

    code, body = _get(f"{be}/health")
    check("Backend GET /health", code == 200, str(code))

    code, body = _get(f"{be}/api/status")
    check("Backend GET /api/status", code == 200, str(code))
    if code == 200:
        try:
            st = json.loads(body)
            name = st.get("name", "")
            check("Backend is Virtus Core", "virtus" in name.lower() or "genesis" in name.lower(), name[:40])
        except json.JSONDecodeError:
            pass

    code, body = _get(f"{be}/api/sales/packages")
    check("Backend GET /api/sales/packages", code == 200, str(code))

    code, body = _get(f"{be}/api/sales/payment-status")
    check("Backend GET /api/sales/payment-status", code == 200, str(code))
    if code == 200:
        try:
            pay = json.loads(body)
            configured = bool(pay.get("configured"))
            detail = f"configured={configured} sandbox={pay.get('sandbox')}"
            if configured:
                check("Stripe payment ready", True, detail)
            else:
                print(f"  [WARN] Stripe payment ready — {detail} (set keys on Railway)")
        except json.JSONDecodeError:
            pass

    # Same-origin proxy path (Vercel rewrite) — required after frontend redeploy
    code, body = _get(f"{fe}/api/sales/packages")
    proxy_ok = code == 200
    check("Frontend proxy GET /api/sales/packages", proxy_ok, str(code))
    if not proxy_ok:
        print("  [INFO] Redeploy Vercel after next.config sales rewrite merge")

    code, html = _get(f"{fe}/site")
    check("Frontend GET /site", code == 200, str(code))
    guided_markers = False
    if code == 200:
        guided_markers = (
            "цифровой сотрудник" in html
            or "Показать черновик" in html
            or "VectorCommerceSteps" in html
        )
        if not guided_markers:
            chunks = re.findall(r"/_next/static/chunks/[^\"']+\.js", html)
            for c in chunks[:32]:
                try:
                    c_code, js = _get(f"{fe}{c}", timeout=15)
                    if c_code != 200:
                        continue
                    if any(
                        s in js
                        for s in (
                            "цифровой сотрудник",
                            "Показать черновик",
                            "VectorCommerceSteps",
                            "GuidedFactoryProductPreview",
                        )
                    ):
                        guided_markers = True
                        break
                except OSError:
                    continue
        check("Vector-first /site bundle", guided_markers)
        if not guided_markers:
            print("  [INFO] Redeploy Vercel genesis-beta from cursor/mission1-genesis-brain-public-layer")
        check("No localhost API leak in HTML", "localhost:8000" not in html)

    print(f"\nResult: {passed}/{total} checks passed")
    if failures:
        print("Failed:", ", ".join(failures))
        print("\nFix checklist:")
        print("  1. Railway: renewed-reprieve / genesis-beta — Root Directory = repo root, Dockerfile")
        print("  2. Vercel: NEXT_PUBLIC_API_URL = Railway backend URL (for SSR rewrites)")
        print("  3. Redeploy frontend after merge (sales API uses same-origin /api/sales proxy)")
        print("  4. GENESIS_CORS_ORIGINS includes beta domain on Railway")
        return 1

    print("\nP-001 ready for external Blind:")
    print(f"  Share: {fe}/site")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
