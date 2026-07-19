"""Switch dashboard/backend/.env.local Stripe keys between live and test (from Stripe CLI).

Usage (repo root):
  py -3.12 scripts/switch_stripe_mode.py test
  py -3.12 scripts/switch_stripe_mode.py live
  py -3.12 scripts/switch_stripe_mode.py status

Does not print secret values. Restart Genesis after switch.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / "dashboard" / "backend" / ".env.local"


def _stripe_config() -> dict[str, str]:
    try:
        out = subprocess.check_output(
            ["stripe", "config", "--list"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=30,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"stripe CLI unavailable: {exc}") from exc
    cfg: dict[str, str] = {}
    for line in out.splitlines():
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        cfg[key] = val
    return cfg


def _read_env(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _upsert(lines: list[str], key: str, value: str) -> list[str]:
    out: list[str] = []
    found = False
    for line in lines:
        if re.match(rf"^\s*{re.escape(key)}\s*=", line):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{key}={value}")
    return out


def _get(lines: list[str], key: str) -> str | None:
    for line in lines:
        if re.match(rf"^\s*{re.escape(key)}\s*=", line):
            return line.split("=", 1)[1].strip().strip("'").strip('"')
    return None


def _mode_of(secret: str | None) -> str:
    if not secret:
        return "missing"
    if secret.startswith("sk_test_"):
        return "test"
    if secret.startswith("sk_live_"):
        return "live"
    return "other"


def status() -> None:
    lines = _read_env(ENV_PATH)
    sk = _get(lines, "STRIPE_SECRET_KEY")
    pk = _get(lines, "STRIPE_PUBLISHABLE_KEY")
    print(f"env_file={ENV_PATH}")
    print(f"STRIPE_SECRET_KEY mode={_mode_of(sk)}")
    print(
        "STRIPE_PUBLISHABLE_KEY mode="
        + (
            "test"
            if (pk or "").startswith("pk_test_")
            else "live"
            if (pk or "").startswith("pk_live_")
            else "missing_or_other"
        )
    )


def switch(target: str) -> None:
    cfg = _stripe_config()
    lines = _read_env(ENV_PATH)
    current = _get(lines, "STRIPE_SECRET_KEY")

    if target == "test":
        sk = cfg.get("test_mode_api_key") or ""
        pk = cfg.get("test_mode_pub_key") or ""
        if not sk.startswith("sk_test_") or not pk.startswith("pk_test_"):
            raise SystemExit("Stripe CLI has no test_mode_api_key / test_mode_pub_key")
        # Preserve live keys for restore
        if current and current.startswith("sk_live_"):
            lines = _upsert(lines, "STRIPE_SECRET_KEY_LIVE", current)
            live_pk = _get(lines, "STRIPE_PUBLISHABLE_KEY")
            if live_pk and live_pk.startswith("pk_live_"):
                lines = _upsert(lines, "STRIPE_PUBLISHABLE_KEY_LIVE", live_pk)
        lines = _upsert(lines, "STRIPE_SECRET_KEY", sk)
        lines = _upsert(lines, "STRIPE_PUBLISHABLE_KEY", pk)
        lines = _upsert(lines, "GENESIS_PAYMENT_SANDBOX", "0")
    elif target == "live":
        sk = _get(lines, "STRIPE_SECRET_KEY_LIVE") or cfg.get("live_mode_api_key") or ""
        pk = _get(lines, "STRIPE_PUBLISHABLE_KEY_LIVE") or cfg.get("live_mode_pub_key") or ""
        # Stripe CLI may store restricted live key as rk_live_ — prefer saved sk_live_
        if not sk.startswith("sk_live_"):
            raise SystemExit(
                "No sk_live_ available to restore (STRIPE_SECRET_KEY_LIVE missing). "
                "Paste live secret back manually."
            )
        if not pk.startswith("pk_live_"):
            raise SystemExit("No pk_live_ available to restore")
        lines = _upsert(lines, "STRIPE_SECRET_KEY", sk)
        lines = _upsert(lines, "STRIPE_PUBLISHABLE_KEY", pk)
    else:
        raise SystemExit("usage: switch_stripe_mode.py [test|live|status]")

    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK switched .env.local → {target}")
    print("Restart Genesis.exe (Stop → Start) so backend reloads keys.")
    status()


def main() -> None:
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "status").strip().lower()
    if cmd == "status":
        status()
    elif cmd in ("test", "live"):
        switch(cmd)
    else:
        raise SystemExit("usage: switch_stripe_mode.py [test|live|status]")


if __name__ == "__main__":
    main()
