"""Motion Director — motion profile that maps to real motion tier / CSS."""

from __future__ import annotations

from typing import Any

ENGINE_ID = "motion_director_v1"


def decide_motion(*, package_id: str, niche: str | None = None) -> dict[str, Any]:
    pid = (package_id or "basic").strip().lower()
    niche_key = (niche or "").strip().lower()

    if pid == "basic":
        choice = "Subtle / none"
        tier = "basic"
        level = "none"
        reason = "Starter: быстрый опыт без тяжёлого motion."
    elif pid == "business":
        choice = "Reveal Medium"
        tier = "business"
        level = "css"
        reason = (
            "Высокая конверсия для медицинской ниши."
            if niche_key in ("dental", "medical", "clinic")
            else "Business motion усиливает Visual Pack без перегруза."
        )
    else:
        choice = "Premium Reveal"
        tier = "premium"
        level = "css"
        reason = "Luxury Mode: premium motion только если усиливает эмоцию."

    return {
        "engine": ENGINE_ID,
        "role": "Motion Director",
        "choice": choice,
        "reason_ru": reason,
        "reason_en": reason,
        "apply": {
            "motion_tier": tier,
            "motion_level": level,
            "reveal": "medium" if pid == "business" else ("premium" if pid == "premium" else "none"),
        },
    }
