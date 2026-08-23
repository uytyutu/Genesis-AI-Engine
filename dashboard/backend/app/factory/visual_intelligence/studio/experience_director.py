"""Experience Director — judges impression, not code; may request rebuild."""

from __future__ import annotations

from typing import Any

ENGINE_ID = "experience_director_v1"

FIRST_IMPRESSION_SOFT = 76
FIRST_IMPRESSION_PREMIUM = 90


def decide_experience_impression(
    *,
    package_id: str,
    first_impression: int | None = None,
    overall: int | None = None,
    luxury_mode: bool = False,
) -> dict[str, Any]:
    """Look at impression scores; propose concrete Factory actions."""
    pid = (package_id or "basic").strip().lower()
    fi = int(first_impression if first_impression is not None else 0)
    actions: list[str] = []
    why = "Первое впечатление в норме для пакета."
    rebuild = False

    threshold = FIRST_IMPRESSION_PREMIUM if pid == "premium" else FIRST_IMPRESSION_SOFT
    if fi and fi < threshold:
        why = "Hero слишком обычный." if fi < FIRST_IMPRESSION_SOFT else "Premium First Impression ниже планки."
        if pid == "premium" or luxury_mode:
            actions.append("use_cinematic_or_video_hero_if_niche_helps")
            actions.append("rebuild_luxury_composition")
        else:
            actions.append("strengthen_hero_layout")
            actions.append("clarify_cta")
        rebuild = pid == "premium" or fi < 70

    return {
        "engine": ENGINE_ID,
        "role": "Experience Director",
        "choice": f"First Impression {fi or '—'}",
        "first_impression": fi,
        "overall": overall,
        "why_ru": why,
        "reason_ru": why,
        "reason_en": why,
        "actions": actions,
        "rebuild_recommended": rebuild,
        "apply": {
            "experience_ok": not rebuild,
            "hero_upgrade": "video_or_cinematic" if "use_cinematic_or_video_hero_if_niche_helps" in actions else "hold",
        },
    }
