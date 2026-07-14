#!/usr/bin/env python3
"""Switch Mission Control UI layout — e.g. Workshop (Мастерская) with compact sidebar."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUT_PATH = ROOT / "dashboard" / "frontend" / "ui_layout.json"

MODES: dict[str, dict] = {
    "ceo": {
        "mode": "ceo",
        "label": "Mission Control",
        "compact_sidebar": False,
        "sidebar_width_px": 240,
        "hide_link_hints": False,
        "home_label": "Движок",
    },
    "master": {
        "mode": "master",
        "label": "Мастерская",
        "compact_sidebar": True,
        "sidebar_width_px": 180,
        "hide_link_hints": True,
        "home_label": "Цифровая ферма",
    },
}


def apply_layout(*, mode: str, compact_sidebar: bool | None = None) -> dict:
    if mode not in MODES:
        raise SystemExit(f"Unknown mode {mode!r}. Choose: {', '.join(MODES)}")
    data = dict(MODES[mode])
    if compact_sidebar is not None:
        data["compact_sidebar"] = compact_sidebar
        data["sidebar_width_px"] = 180 if compact_sidebar else 240
        data["hide_link_hints"] = compact_sidebar
    LAYOUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAYOUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply Virtus Core UI layout")
    parser.add_argument("--mode", choices=sorted(MODES.keys()), default="ceo")
    parser.add_argument("--compact-sidebar", action="store_true", default=None)
    parser.add_argument("--no-compact-sidebar", action="store_true")
    args = parser.parse_args()
    compact: bool | None = None
    if args.compact_sidebar:
        compact = True
    elif args.no_compact_sidebar:
        compact = False
    data = apply_layout(mode=args.mode, compact_sidebar=compact)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"\nWritten: {LAYOUT_PATH}")
    print("Перезагрузи Mission Control (Genesis.exe) чтобы увидеть новый layout.")


if __name__ == "__main__":
    main()
