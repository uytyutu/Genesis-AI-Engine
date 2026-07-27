#!/usr/bin/env python3
"""P0 — anon probe for public beta CEO shell exposure.

Exit 0 only if owner/client routes redirect (or return gate/login HTML),
never CEO chrome markers without auth.
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request

CEO_MARKERS = (
    "Цифровая ферма",
    "Финансы и налоги",
    "Поиск лидов",
    "data-surface=\"ceo\"",
    'data-surface="ceo"',
)

GATE_MARKERS = (
    "Доступ только для владельца",
    "Ключ владельца",
    "owner-gate",
    "Sign in required",
    "Sign in",
)

CEO_PATHS = (
    "/",
    "/business",
    "/finance",
    "/opportunities",
    "/acquisition",
    "/settings",
    "/revenue",
)

CLIENT_PATHS = ("/client", "/projects")
PUBLIC_OK = ("/site", "/owner-gate")


def fetch(url: str, *, follow: bool = False) -> tuple[int, str, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "virtus-beta-owner-gate-probe/1.0",
            "Accept": "text/html",
        },
        method="GET",
    )
    try:
        opener = urllib.request.build_opener(
            urllib.request.HTTPRedirectHandler()
            if follow
            else _NoRedirect()
        )
        with opener.open(req, timeout=25) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            loc = resp.headers.get("Location") or ""
            return int(resp.status), loc, body
    except urllib.error.HTTPError as e:
        loc = e.headers.get("Location") or "" if e.headers else ""
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return int(e.code), loc, body


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base",
        default="https://beta.genesis-ai-engine.com",
        help="Public frontend base URL",
    )
    args = ap.parse_args()
    base = args.base.rstrip("/")
    failed: list[str] = []

    for path in CEO_PATHS:
        code, loc, body = fetch(f"{base}{path}", follow=False)
        if code in (301, 302, 303, 307, 308) and "owner-gate" in (loc or ""):
            print(f"OK  {path} -> {code} Location={loc}")
            continue
        if code == 200 and any(m in body for m in GATE_MARKERS) and not any(
            m in body for m in CEO_MARKERS
        ):
            print(f"OK  {path} -> 200 gate HTML (no CEO chrome)")
            continue
        if any(m in body for m in CEO_MARKERS):
            failed.append(f"FAIL {path} -> {code} CEO_SHELL_VISIBLE Loc={loc}")
        else:
            failed.append(f"FAIL {path} -> {code} expected owner-gate Loc={loc}")

    for path in CLIENT_PATHS:
        code, loc, body = fetch(f"{base}{path}", follow=False)
        if code in (301, 302, 303, 307, 308) and "login" in (loc or ""):
            print(f"OK  {path} -> {code} Location={loc}")
            continue
        if code == 200 and ("Sign in" in body or "login" in body.lower()):
            print(f"OK  {path} -> 200 login HTML")
            continue
        if any(m in body for m in CEO_MARKERS):
            failed.append(f"FAIL {path} -> {code} CEO_SHELL_VISIBLE")
        else:
            failed.append(f"FAIL {path} -> {code} expected client login Loc={loc}")

    for path in PUBLIC_OK:
        code, loc, body = fetch(f"{base}{path}", follow=False)
        if code == 200 and not (
            path != "/owner-gate" and any(m in body for m in CEO_MARKERS)
        ):
            print(f"OK  {path} -> {code} public")
        elif path == "/owner-gate" and code == 200:
            print(f"OK  {path} -> {code}")
        else:
            failed.append(f"FAIL {path} -> {code} unexpected")

    if failed:
        print("\n".join(failed))
        print("RESULT: FAIL — public CEO shell still exposed")
        return 1
    print("RESULT: PASS — anon cannot see CEO shell on public domain")
    return 0


if __name__ == "__main__":
    sys.exit(main())
