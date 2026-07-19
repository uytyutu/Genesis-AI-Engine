"""Niche × market scene slots for future 3D library (stubs only — no Path A wiring)."""

from __future__ import annotations

from typing import Any

# One scene slot per niche — fill with optimized GLB + CREDITS when researching.
NICHE_SCENE_SLOTS: tuple[dict[str, Any], ...] = (
    {"niche_id": "dental", "scene": "clinic_hero", "status": "empty"},
    {"niche_id": "law", "scene": "office_hero", "status": "empty"},
    {"niche_id": "auto", "scene": "workshop_hero", "status": "empty"},
    {"niche_id": "cafe", "scene": "interior_hero", "status": "empty"},
    {"niche_id": "salon", "scene": "studio_hero", "status": "empty"},
    {"niche_id": "clinic", "scene": "medical_hero", "status": "empty"},
    {"niche_id": "it", "scene": "product_hero", "status": "empty"},
    {"niche_id": "local_service", "scene": "generic_hero", "status": "empty"},
)

# Markets reuse the same scene mesh; locale/legal stay Path A Classic/CSS.
MARKET_SLOTS: tuple[str, ...] = (
    "DE",
    "AT",
    "CH",
    "US",
    "GB",
    "IE",
    "CA",
    "AU",
    "NZ",
    "FR",
    "IT",
    "ES",
    "NL",
    "BE",
    "PT",
    "PL",
    "CZ",
    "SK",
    "RO",
    "UA",
    "RU",
)


def list_niche_slots() -> list[dict[str, Any]]:
    return [dict(x) for x in NICHE_SCENE_SLOTS]


def list_market_slots() -> list[str]:
    return list(MARKET_SLOTS)


def niche_coverage() -> dict[str, Any]:
    filled = sum(1 for n in NICHE_SCENE_SLOTS if n.get("status") == "ready")
    return {
        "niches_total": len(NICHE_SCENE_SLOTS),
        "niches_ready": filled,
        "markets_total": len(MARKET_SLOTS),
        "note": "Scene mesh is niche-scoped; market only changes copy/legal via Path A packs.",
    }
