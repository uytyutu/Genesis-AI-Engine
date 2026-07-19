"""Sync research 3D niche slots 1:1 with Factory known_niche_ids()."""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Default hero scene name per Path A niche (one preset each).
_SCENE_FOR_NICHE: dict[str, str] = {
    "auto": "workshop_hero",
    "appliance": "appliance_hero",
    "beauty": "salon_hero",
    "computer": "device_hero",
    "dental": "clinic_hero",
    "energy": "solar_hero",
    "generic": "storefront_hero",
    "green": "garden_hero",
    "handwerk": "craft_hero",
    "law": "office_hero",
}

_RESEARCH_SCENES = Path(__file__).resolve().parents[3] / "_research_3d" / "scenes"


def _scene_status(niche_id: str) -> str:
    root = _RESEARCH_SCENES / niche_id
    examples = root / "examples"
    glbs = sorted(examples.glob("*.glb")) if examples.is_dir() else []
    has_hero = (root / "hero.glb").is_file() or (root / "hero.gltf").is_file()
    has_lic = any(
        (root / n).is_file()
        for n in ("LICENSE.txt", "LICENSE", "license.txt", "MODEL_LICENSE.txt")
    )
    has_credits = (root / "CREDITS.txt").is_file()
    if len(glbs) >= 5 and has_hero and has_lic and has_credits:
        return "ready"
    if glbs or has_hero or has_lic or has_credits:
        return "partial"
    return "empty"


def list_niche_slots() -> list[dict[str, Any]]:
    from app.factory.niche_profiles import known_niche_ids

    out: list[dict[str, Any]] = []
    for niche_id in known_niche_ids():
        scene = _SCENE_FOR_NICHE.get(niche_id, f"{niche_id}_hero")
        out.append(
            {
                "niche_id": niche_id,
                "scene": scene,
                "status": _scene_status(niche_id),
                "asset_dir": f"scenes/{niche_id}",
            }
        )
    return out


def list_market_slots() -> list[str]:
    from app.factory.market_delivery import PATH_A_DELIVERY_MARKETS

    return list(PATH_A_DELIVERY_MARKETS)


def niche_coverage() -> dict[str, Any]:
    slots = list_niche_slots()
    filled = sum(1 for n in slots if n.get("status") == "ready")
    markets = list_market_slots()
    return {
        "niches_total": len(slots),
        "niches_ready": filled,
        "markets_total": len(markets),
        "note": (
            "Scene mesh is niche-scoped and aligned with Factory known_niche_ids(); "
            "market only changes copy/legal via Path A packs."
        ),
        "reference_niche": "dental",
        "examples_per_niche": 5,
        "runtime": "runtime/scene_engine.html",
        "slots": slots,
    }
