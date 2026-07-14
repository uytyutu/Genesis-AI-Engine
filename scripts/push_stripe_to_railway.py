#!/usr/bin/env python3
"""Push Stripe test keys to Railway beta backend (CEO runs once).

Reads secrets from environment — never from argv (avoids shell history leaks).

  $env:STRIPE_SECRET_KEY="sk_test_..."
  $env:STRIPE_PUBLISHABLE_KEY="pk_test_..."
  py scripts/push_stripe_to_railway.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from shutil import which

BETA_BACKEND = os.getenv(
    "BETA_BACKEND_URL",
    "https://renewed-reprieve-production.up.railway.app",
).rstrip("/")
SERVICE = os.getenv("RAILWAY_BETA_SERVICE", "renewed-reprieve")
CORS = os.getenv("GENESIS_CORS_ORIGINS", "https://beta.genesis-ai-engine.com")


def _railway_cmd(*args: str) -> list[str]:
    if which("railway"):
        return ["railway", *args]
    npx = which("npx")
    if npx:
        return [npx, "--yes", "@railway/cli", *args]
    return ["npx", "--yes", "@railway/cli", *args]


def _set(name: str, value: str) -> int:
    cmd = _railway_cmd("variables", "--set", f"{name}={value}", "--service", SERVICE)
    print(f"> set {name}")
    return subprocess.call(cmd, shell=os.name == "nt")


def _payment_status() -> dict:
    with urllib.request.urlopen(f"{BETA_BACKEND}/api/sales/payment-status", timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    sk = os.getenv("STRIPE_SECRET_KEY", "").strip()
    pk = os.getenv("STRIPE_PUBLISHABLE_KEY", "").strip()
    wh = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()

    if not sk.startswith("sk_test_") and not sk.startswith("sk_live_"):
        print("ERROR: set STRIPE_SECRET_KEY env (sk_test_... or sk_live_...)")
        return 1
    if pk and not pk.startswith("pk_test_") and not pk.startswith("pk_live_"):
        print("ERROR: STRIPE_PUBLISHABLE_KEY must be pk_test_... or pk_live_...")
        return 1

    if not which("railway") and not which("npx"):
        print("ERROR: Railway CLI not found. Run: npx @railway/cli login")
        return 1

    for name, value in (
        ("STRIPE_SECRET_KEY", sk),
        ("STRIPE_PUBLISHABLE_KEY", pk),
        ("GENESIS_CORS_ORIGINS", CORS),
    ):
        if not value:
            continue
        if _set(name, value) != 0:
            print(f"FAILED setting {name}. Run: railway login && railway link")
            return 2

    if wh:
        if _set("STRIPE_WEBHOOK_SECRET", wh) != 0:
            print("WARN: STRIPE_WEBHOOK_SECRET not set on Railway")

    print("Waiting 90s for redeploy...")
    time.sleep(90)

    try:
        pay = _payment_status()
    except Exception as exc:
        print(f"payment-status check failed: {exc}")
        return 3

    print(json.dumps(pay, indent=2, ensure_ascii=False))
    if pay.get("configured"):
        print("OK — Stripe configured on Railway")
        return 0
    print("Still configured=false — check Railway redeploy")
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
