"""AI Creative Director convenes the board and issues the final StudioPlan."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.factory.visual_intelligence.ai_creative_director import decide_experience
from app.factory.visual_intelligence.studio.industry_director import decide_industry
from app.factory.visual_intelligence.studio.luxury_director import (
    decide_luxury,
    luxury_director_css,
)
from app.factory.visual_intelligence.studio.motion_director import decide_motion
from app.factory.visual_intelligence.studio.typography_director import (
    decide_typography,
    typography_director_css,
)
from app.factory.visual_intelligence.studio.conversion_director import (
    conversion_director_css,
    decide_conversion,
)
from app.factory.visual_intelligence.studio.trust_director import (
    decide_trust,
    trust_director_css,
)
from app.factory.visual_intelligence.studio.performance_director import (
    decide_performance,
    performance_director_css,
)
from app.factory.visual_intelligence.studio.accessibility_director import (
    accessibility_director_css,
    decide_accessibility,
)
from app.factory.visual_intelligence.studio.localization_director import (
    decide_localization,
    localization_director_css,
)
from app.factory.visual_intelligence.store_director import decide_store_experience

STUDIO_ENGINE_ID = "digital_creative_studio_v2"
POSITIONING_RU = "Virtus Core проектирует цифровой опыт вашего бизнеса."


@dataclass
class StudioPlan:
    """Final creative plan — must be applied to HTML/CSS."""

    package_id: str
    niche: str
    market_code: str
    luxury_mode: bool
    creative: dict[str, Any]
    directors: list[dict[str, Any]] = field(default_factory=list)
    apply: dict[str, Any] = field(default_factory=dict)
    css: str = ""
    surface: str = "website"

    def as_dict(self) -> dict[str, Any]:
        apply = dict(self.apply or {})
        fp = apply.get("font_pack")
        if fp is not None and hasattr(fp, "label"):
            apply = {
                **apply,
                "font_pack": {
                    "label": getattr(fp, "label", ""),
                    "body": getattr(fp, "body", ""),
                    "display": getattr(fp, "display", ""),
                },
            }
        directors_out: list[dict[str, Any]] = []
        for d in self.directors:
            row = {k: v for k, v in d.items() if k not in ("font_pack", "raw")}
            if "font_pack" in d and hasattr(d["font_pack"], "label"):
                fp2 = d["font_pack"]
                row["font_pack"] = {
                    "label": fp2.label,
                    "body": fp2.body,
                    "display": fp2.display,
                }
            directors_out.append(row)
        return {
            "engine": STUDIO_ENGINE_ID,
            "product": "Digital Creative Studio",
            "role": "AI Creative Director",
            "mission_ru": "Создай лучший цифровой опыт для этой ниши и этого бюджета.",
            "positioning_ru": POSITIONING_RU,
            "surface": self.surface,
            "package_id": self.package_id,
            "niche": self.niche,
            "market_code": self.market_code,
            "luxury_mode": self.luxury_mode,
            "creative_director": self.creative,
            "directors": directors_out,
            "apply": apply,
            "css_bytes": len(self.css.encode("utf-8")),
        }

    def replay_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for d in self.directors:
            rows.append(
                {
                    "director": str(d.get("role") or d.get("engine") or ""),
                    "choice": str(d.get("choice") or ""),
                    "reason": str(d.get("reason_ru") or d.get("why_ru") or ""),
                }
            )
        return rows

    def director(self, role_substr: str) -> dict[str, Any] | None:
        key = role_substr.lower()
        for d in self.directors:
            if key in str(d.get("role") or "").lower():
                return d
        return None


def convene_board(
    *,
    package_id: str,
    niche: str | None = None,
    market_code: str = "DE",
    goal: str | None = None,
    surface: str = "website",
    catalog_size: int | None = None,
    category: str | None = None,
) -> StudioPlan:
    """Board meeting: directors advise → Creative Director finalizes."""
    creative = decide_experience(
        package_id=package_id,
        niche=niche,
        market_code=market_code,
        goal=goal,
    )
    pid = creative["package_id"]
    niche_key = creative["niche"]
    market = (market_code or "DE").upper()

    industry = decide_industry(niche=niche_key, package_id=pid)
    luxury = decide_luxury(package_id=pid, niche=niche_key)
    typo = decide_typography(
        package_id=pid,
        niche=niche_key,
        typography_key=str((creative.get("decisions") or {}).get("typography") or ""),
        diversity_salt=f"{niche_key}|{pid}|{market}|{goal or ''}",
    )
    motion = decide_motion(package_id=pid, niche=niche_key)
    conversion = decide_conversion(package_id=pid, niche=niche_key)
    trust = decide_trust(package_id=pid, niche=niche_key)
    performance = decide_performance(
        package_id=pid,
        luxury_mode=bool(luxury.get("luxury_mode")),
        allow_video=(creative.get("decisions") or {}).get("heavy_video"),
    )
    a11y = decide_accessibility(package_id=pid)
    localization = decide_localization(market_code=market, package_id=pid)

    directors = [
        industry,
        luxury,
        typo,
        motion,
        conversion,
        trust,
        performance,
        a11y,
        localization,
    ]

    store: dict[str, Any] | None = None
    if surface == "store":
        store = decide_store_experience(
            package_id=pid,
            category=category or niche_key,
            catalog_size=catalog_size,
        )
        directors.append(
            {
                "engine": store.get("engine"),
                "role": "Store Director",
                "choice": str((store.get("decisions") or {}).get("card_style") or "store"),
                "reason_ru": store.get("mission_ru")
                or "Полноценный современный e-commerce.",
                "reason_en": "Full modern e-commerce experience.",
                "apply": store.get("decisions") or {},
                "customer_auth": store.get("customer_auth"),
                "raw": store,
            }
        )

    # Creative Director final merge — business directors included
    apply: dict[str, Any] = {
        **(industry.get("apply") or {}),
        **(luxury.get("apply") or {}),
        **(typo.get("apply") or {}),
        **(motion.get("apply") or {}),
        **(conversion.get("apply") or {}),
        **(trust.get("apply") or {}),
        **(performance.get("apply") or {}),
        **(a11y.get("apply") or {}),
        **(localization.get("apply") or {}),
        "luxury_mode": bool(luxury.get("luxury_mode")),
        "data_luxury": "1" if luxury.get("luxury_mode") else "0",
        "data_studio": STUDIO_ENGINE_ID,
        "hero_layout_prefer": luxury.get("hero_layout_prefer"),
        "font_pack": typo.get("font_pack"),
        "conversion": conversion,
        "trust": trust,
        "performance": performance,
        "accessibility": a11y,
        "localization": localization,
    }
    if store:
        apply["store"] = store

    # Performance may veto heavy motion/video for Starter or when prefer_static
    if apply.get("prefer_static_hero") and apply.get("luxury_mode"):
        apply["hero_class_extra"] = str(apply.get("hero_class_extra") or "").replace(
            "hero-video", "hero-still"
        )

    css = "\n".join(
        [
            typography_director_css(typo),
            luxury_director_css(enabled=bool(luxury.get("luxury_mode"))),
            conversion_director_css(),
            trust_director_css(trust),
            performance_director_css(),
            accessibility_director_css(),
            localization_director_css(localization),
        ]
    )

    return StudioPlan(
        package_id=pid,
        niche=niche_key,
        market_code=market,
        luxury_mode=bool(luxury.get("luxury_mode")),
        creative=creative,
        directors=directors,
        apply=apply,
        css=css,
        surface=surface,
    )
