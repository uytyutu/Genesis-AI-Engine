#!/usr/bin/env python3
"""Mint a one-time Virtus Core friend gift link.

Usage (from repo root or dashboard/backend):
  py -3.12 scripts/mint_friend_gift.py
  py -3.12 scripts/mint_friend_gift.py --label "Gift for Alex" --site https://virtuscore.com
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.integration.gift_token import mint_token  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Mint one-time Virtus friend gift URL")
    p.add_argument("--label", default="Friend gift")
    p.add_argument("--package", default="standalone")
    p.add_argument("--ttl-days", type=int, default=14)
    p.add_argument(
        "--site",
        default="https://virtuscore.com",
        help="Public site origin for the shareable URL",
    )
    args = p.parse_args()
    minted = mint_token(
        label=args.label,
        package_id=args.package,
        ttl_days=args.ttl_days,
        minted_by="mint_friend_gift_script",
    )
    site = args.site.rstrip("/")
    url = f"{site}{minted['path']}"
    gift_url = f"{site}{minted['gift_path']}"
    print("GIFT TOKEN MINTED")
    print(f"code:     {minted['code']}")
    print(f"expires:  {minted['expires_at']}")
    print(f"package:  {minted['package_id']}")
    print(f"url:      {url}")
    print(f"short:    {gift_url}")
    print("")
    print("Send the friend the SHORT link (Virtus gift form — not payment):")
    print(f"  {gift_url}")
    print("Single use. Friend fills business form -> gets login/password + site + Workspace.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
