"""Niche → interactive showcase intent (research / future Premium).

Factory Path A does not import this at checkout. Sold demos + future Premium
pick a thematic showcase from niche_showcase.json — never a random mesh.

Lab UI under dashboard/backend/_research_3d/ (tier switch, Virtus eyebrow, Demo)
must stay research-only — never ship into client ZIP / Path A index.html.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[3] / "_research_3d"
_SHOWCASE_PATH = _ROOT / "niches" / "niche_showcase.json"


def load_niche_showcase() -> dict[str, Any]:
    if not _SHOWCASE_PATH.is_file():
        return {"version": 0, "niches": {}, "tiers": {}}
    return json.loads(_SHOWCASE_PATH.read_text(encoding="utf-8"))


def showcase_for_niche(niche_id: str | None) -> dict[str, Any] | None:
    data = load_niche_showcase()
    niches = data.get("niches") or {}
    key = str(niche_id or "").strip().lower()
    row = niches.get(key)
    if not isinstance(row, dict):
        return None
    return {
        **row,
        "niche_id": key,
        "lazy_load": bool(data.get("lazy_load", True)),
        "loading_copy": data.get("loading_copy") or {},
        "tiers": data.get("tiers") or {},
    }


def resolve_package_visual_tier(package_id: str | None) -> str:
    """Map Path A package ids → visual tier (research contract)."""
    pid = str(package_id or "basic").strip().lower()
    if pid == "premium":
        return "premium"
    if pid == "business":
        return "business"
    return "basic"
