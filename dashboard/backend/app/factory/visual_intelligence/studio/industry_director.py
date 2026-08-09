"""Industry Director — niche audience expectations."""

from __future__ import annotations

from typing import Any

from app.factory.visual_intelligence.ai_design_director import NICHE_IDENTITY

ENGINE_ID = "industry_director_v1"


def decide_industry(*, niche: str, package_id: str) -> dict[str, Any]:
    niche_key = (niche or "generic").strip().lower() or "generic"
    identity = NICHE_IDENTITY.get(niche_key) or {
        "theme": "modern_default",
        "feel_ru": "современный нейтральный",
        "hero_bias": "photo",
    }
    pid = (package_id or "basic").strip().lower()
    label = {
        "dental": "Premium Medical" if pid == "premium" else "Medical Clean",
        "psychology": "Therapy Trust" if pid == "premium" else "Calm Clinical",
        "beauty": "Calm Luxury" if pid == "premium" else "Beauty Studio",
        "law": "Authority Trust",
        "restaurant": "Culinary Atmosphere",
        "auto": "Precision Automotive",
    }.get(niche_key, identity.get("theme", "Modern Default"))

    return {
        "engine": ENGINE_ID,
        "role": "Industry Director",
        "choice": label,
        "niche": niche_key,
        "identity": identity,
        "reason_ru": f"Соответствует ожиданиям аудитории ({identity.get('feel_ru', label)}).",
        "reason_en": f"Matches audience expectations ({label}).",
        "apply": {
            "industry_theme": label,
            "hero_bias": identity.get("hero_bias", "photo"),
        },
    }
