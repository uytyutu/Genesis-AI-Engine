#!/usr/bin/env python3
"""Compat: regenerate dental niche (5 examples)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_research_3d_presets import generate_niche  # noqa: E402

if __name__ == "__main__":
    rows = generate_niche("dental")
    for r in rows:
        print(f"{r['id']:14s} {r['bytes']:5d} B  {r['title']}")
