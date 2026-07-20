"""Copy dashboard/backend/.env.local → repo root .env (UTF-8, no comments, no empty keys).

Genesis.exe lives at repo root; env_loader reads both paths.
Never commit the generated .env — it is gitignored.
"""

from __future__ import annotations

import sys
from pathlib import Path

PRIORITY = (
    "TOLOKA_API_TOKEN",
    "FARM_EXECUTION_MODE",
    "FARM_LIVE_MODE",
    "FARM_PAYOUT_THRESHOLD_USD",
    "SCALE_API_KEY",
    "FARM_WORKER_POOL_URL",
    "FARM_WORKER_POOL_TOKEN",
    "TOLOKA_API_BASE_URL",
)


def _parse_env_lines(text: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    order: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, _, value = s.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key or not value:
            continue
        if key not in pairs:
            order.append(key)
        pairs[key] = value
    head = [k for k in PRIORITY if k in pairs]
    tail = [k for k in order if k not in PRIORITY]
    return {k: pairs[k] for k in head + tail}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    src = root / "dashboard" / "backend" / ".env.local"
    dst = root / ".env"
    if not src.is_file():
        print(f"Missing source: {src}", file=sys.stderr)
        return 1
    pairs = _parse_env_lines(src.read_text(encoding="utf-8-sig"))
    if not pairs:
        print("No key=value lines in .env.local", file=sys.stderr)
        return 1
    body = "\n".join(f"{k}={v}" for k, v in pairs.items()) + "\n"
    dst.write_text(body, encoding="utf-8")
    print(f"Synced {len(pairs)} keys -> {dst}")
    print(f"  farm: {pairs.get('FARM_LIVE_MODE')} / {pairs.get('FARM_EXECUTION_MODE')}")
    print(f"  toloka: {'yes' if pairs.get('TOLOKA_API_TOKEN') else 'no'}")
    print(f"  scale: {'yes' if pairs.get('SCALE_API_KEY') else 'skip'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
