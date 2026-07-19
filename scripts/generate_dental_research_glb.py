#!/usr/bin/env python3
"""Compat wrapper — dental preset now lives in generate_research_3d_presets.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_research_3d_presets import generate_niche  # noqa: E402

if __name__ == "__main__":
    r = generate_niche("dental")
    print(f"wrote dental hero.glb ({r['bytes']} bytes, {r['material']})")
