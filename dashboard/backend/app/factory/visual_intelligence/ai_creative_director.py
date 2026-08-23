"""AI Creative Director — decides the best experience for niche + budget.

Not: "assemble a site."
Yes: "create the best digital experience for this niche and this package."
"""

from __future__ import annotations

from typing import Any

from app.factory.visual_intelligence.ai_design_director import NICHE_IDENTITY

ENGINE_ID = "ai_creative_director_v1"
POSITIONING_RU = "Virtus Core проектирует цифровой опыт вашего бизнеса."
POSITIONING_EN = "Virtus Core designs the digital experience for your business."
POSITIONING_DE = "Virtus Core gestaltet die digitale Erfahrung Ihres Unternehmens."


def decide_experience(
    *,
    package_id: str,
    niche: str | None = None,
    market_code: str = "DE",
    goal: str | None = None,
) -> dict[str, Any]:
    """Return an automatic creative brief for Factory / Store builds."""
    pid = (package_id or "basic").strip().lower()
    if pid not in ("basic", "business", "premium"):
        pid = "basic"
    niche_key = (niche or "generic").strip().lower()
    identity = NICHE_IDENTITY.get(niche_key) or {
        "theme": "modern_default",
        "feel_ru": "современный нейтральный",
        "hero_bias": "photo",
    }

    budget_eur = {"basic": 199, "business": 399, "premium": 699}[pid]
    luxury_mode = pid == "premium"

    if pid == "basic":
        decisions = {
            "heavy_video": False,
            "webgl": False,
            "lottie_heavy": False,
            "page_density": "light",
            "motion_profile": "subtle_css",
            "hero_media": "photo_or_svg",
            "typography": "clean_system_or_one_font",
            "goal_ru": "быстрый, чистый, современный опыт без перегрузки",
        }
    elif pid == "business":
        decisions = {
            "heavy_video": False,
            "webgl": False,
            "lottie_heavy": False,
            "page_density": "rich",
            "motion_profile": "business_motion",
            "hero_media": "photo_svg_quality_assets",
            "typography": "brand_pair",
            "visual_pack": True,
            "goal_ru": "качественные ассеты, SVG, motion, современные карточки, своя схема",
        }
    else:
        decisions = {
            "heavy_video": "if_niche_helps",
            "webgl": "if_niche_helps",
            "lottie_heavy": "if_niche_helps",
            "page_density": "cinematic",
            "motion_profile": "premium_motion",
            "hero_media": "cinematic_photo_or_video_or_3d",
            "typography": "luxury_pair",
            "visual_pack": True,
            "luxury_mode": True,
            "interactive": "if_improves_experience",
            "goal_ru": "эмоция дорогого бренда (Luxury Mode), не галочка Premium",
        }

    return {
        "engine": ENGINE_ID,
        "role": "AI Creative Director",
        "mission_ru": "Создай лучший цифровой опыт для этой ниши и этого бюджета.",
        "positioning": {
            "ru": POSITIONING_RU,
            "en": POSITIONING_EN,
            "de": POSITIONING_DE,
        },
        "package_id": pid,
        "budget_eur": budget_eur,
        "niche": niche_key,
        "market_code": (market_code or "DE").upper(),
        "goal": goal or "lead",
        "industry": identity,
        "luxury_mode": luxury_mode,
        "decisions": decisions,
        "forbidden_ru": (
            ["тяжёлое видео", "сложный WebGL", "перегруз страницы"]
            if pid == "basic"
            else []
        ),
        "acceptance_5s_ru": (
            "Без ценников за 5 секунд должно быть ясно: Starter / Business / Premium."
        ),
    }
