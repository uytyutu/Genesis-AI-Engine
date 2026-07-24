#!/usr/bin/env python3
"""CLI: print Gmail OAuth URL and exchange a pasted redirect for refresh_token.

Usage (backend running optional — this script talks to Google directly):
  cd dashboard/backend
  py -3.12 scripts/gmail_oauth_setup.py

Requires GMAIL_CLIENT_ID + GMAIL_CLIENT_SECRET in .env.local
Register redirect: http://127.0.0.1:8000/api/owner/gmail/oauth/callback
Prefer the browser page: http://127.0.0.1:8000/api/owner/gmail
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.env_loader import load_local_env  # noqa: E402
from app.integration import gmail_mail_service as gmail  # noqa: E402


def main() -> int:
    load_local_env()
    if not gmail.oauth_client_ready():
        print("Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env.local")
        return 1
    redirect = gmail.default_redirect_uri("http://127.0.0.1:8000")
    state = gmail.create_oauth_state()
    url = gmail.authorization_url(redirect_uri=redirect, state=state)
    print("1) Open this URL in the browser:\n")
    print(url)
    print("\n2) After Google redirects (page may error if backend is down),")
    print("   copy the FULL browser address bar URL and paste it here.\n")
    pasted = input("Redirect URL: ").strip()
    if not pasted:
        print("Empty URL")
        return 1
    parsed = urlparse(pasted)
    qs = parse_qs(parsed.query)
    code = (qs.get("code") or [""])[0]
    got_state = (qs.get("state") or [""])[0]
    if got_state != state:
        # Still accept if user used the HTML flow state; try consume if present
        if not gmail.consume_oauth_state(got_state):
            print("State mismatch — start again")
            return 1
    else:
        gmail.consume_oauth_state(state)
    result = gmail.exchange_code(code=code, redirect_uri=redirect)
    if not result.get("ok"):
        print("Exchange failed:", result)
        return 1
    refresh = result.get("refresh_token")
    if not refresh:
        print(result.get("hint") or "No refresh_token — revoke app access and retry")
        return 1
    print("\nAdd to dashboard/backend/.env.local:\n")
    print(f"GMAIL_REFRESH_TOKEN={refresh}")
    print("\nThen restart Genesis. Do not commit this token.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
