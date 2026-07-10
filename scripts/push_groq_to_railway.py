#!/usr/bin/env python3
"""Copy Groq key from localhost .env.local → Railway genesis-beta (CEO runs once)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENV_CANDIDATES = (
    REPO / "dashboard" / "backend" / ".env.local",
    REPO / "dashboard" / "backend" / ".env",
    REPO / ".env",
)
BETA_BACKEND = os.getenv(
    "BETA_BACKEND_URL",
    "https://renewed-reprieve-production.up.railway.app",
).rstrip("/")
SERVICE = os.getenv("RAILWAY_BETA_SERVICE", "genesis-beta")
KEY_NAMES = ("GENESIS_GROQ_API_KEY", "GENESIS_LLM_API_KEY")


def _read_key() -> tuple[str, str] | None:
    values: dict[str, str] = {}
    for path in ENV_CANDIDATES:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                continue
            name, _, value = stripped.partition("=")
            name = name.strip()
            value = value.strip().strip('"').strip("'")
            if name in KEY_NAMES and value and name not in values:
                values[name] = value
    for preferred in KEY_NAMES:
        if preferred in values:
            return preferred, values[preferred]
    return None


def _railway_bin() -> str | None:
    from shutil import which

    return which("railway") or which("npx")


def _railway_cmd(*args: str) -> list[str]:
    from shutil import which

    if which("railway"):
        return ["railway", *args]
    return ["npx", "--yes", "@railway/cli", *args]


def _status() -> dict:
    with urllib.request.urlopen(f"{BETA_BACKEND}/api/public/genesis-ai/status", timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def _run(cmd: list[str]) -> int:
    print(">", " ".join(cmd[:3]), "...")
    return subprocess.call(cmd)


def main() -> int:
    found = _read_key()
    if not found:
        print("ERROR: No GENESIS_GROQ_API_KEY in dashboard/backend/.env.local")
        return 1

    key_name, key_value = found
    if not re.match(r"^gsk_", key_value) and key_name == "GENESIS_LLM_API_KEY":
        print(f"WARN: {key_name} does not look like Groq (gsk_...). Continuing anyway.")

    railway = _railway_bin()
    if not railway:
        print("Railway CLI not found.")
        print("CEO: Railway → genesis-beta → Variables → GENESIS_GROQ_API_KEY = (из .env.local)")
        return 1

    rc = _run(_railway_cmd("variables", "--set", f"GENESIS_GROQ_API_KEY={key_value}", "--service", SERVICE))
    if rc != 0:
        print("FAILED. Run from repo root after: railway login && railway link")
        return rc

    model = os.getenv("GENESIS_GROQ_MODEL", "llama-3.3-70b-versatile")
    _run(_railway_cmd("variables", "--set", f"GENESIS_GROQ_MODEL={model}", "--service", SERVICE))

    print("Waiting 90s for redeploy...")
    time.sleep(90)

    try:
        st = _status()
    except Exception as exc:
        print(f"Status check failed: {exc}")
        return 1

    llm = st.get("llm_configured")
    cloud = (st.get("workforce") or {}).get("cloud_employees_ready", 0)
    print(f"llm_configured = {llm}")
    print(f"cloud_employees_ready = {cloud}")
    if llm and int(cloud or 0) >= 1:
        print("OK — run: py scripts/prove_beta_parity.py")
        return 0
    print("Still false — check Railway Variables and redeploy manually.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
