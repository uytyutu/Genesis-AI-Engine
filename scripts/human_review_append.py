#!/usr/bin/env python3
"""Append one Human Review entry — manual notes after a live Genesis conversation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REVIEWS_PATH = (
    Path(__file__).resolve().parent.parent
    / "dashboard"
    / "backend"
    / "app"
    / "memory"
    / "human_review"
    / "reviews.jsonl"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add a Human Review line to reviews.jsonl (Behavior First)."
    )
    parser.add_argument("--user-message", required=True, help="What the user said")
    parser.add_argument("--expected-feeling", default="", help="What should have felt like")
    parser.add_argument("--actual-feeling", default="", help="What it actually felt like")
    parser.add_argument("--reason", default="", help="Why it felt wrong or right")
    parser.add_argument("--fix", default="", help="Which existing component to tune (not a new layer)")
    parser.add_argument(
        "--tag",
        default="",
        help="bot|good|long|repeat|funny|understood|interrupt|natural",
    )
    parser.add_argument("--reply", default="", help="Genesis reply quote")
    args = parser.parse_args()

    entry = {
        "at": datetime.now(timezone.utc).isoformat(),
        "user_message": args.user_message.strip(),
        "expected_feeling": args.expected_feeling.strip(),
        "actual_feeling": args.actual_feeling.strip(),
        "reason": args.reason.strip(),
        "fix": args.fix.strip(),
    }
    if args.tag.strip():
        entry["tag"] = args.tag.strip()
    if args.reply.strip():
        entry["reply"] = args.reply.strip()

    REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REVIEWS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Appended to {REVIEWS_PATH}")


if __name__ == "__main__":
    main()
