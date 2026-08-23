"""Experience Replay — explain why the site looks the way it does."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.factory.visual_intelligence.studio.board import StudioPlan

ENGINE_ID = "experience_replay_v1"


def build_experience_replay(
    plan: StudioPlan | dict[str, Any],
    *,
    design_director: dict[str, Any] | None = None,
    design_memory: dict[str, Any] | None = None,
    experience: dict[str, Any] | None = None,
    commercial_readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Panel payload: «Почему получился именно такой сайт?»"""
    if isinstance(plan, StudioPlan):
        rows = plan.replay_rows()
        package_id = plan.package_id
        niche = plan.niche
        luxury = plan.luxury_mode
        plan_dict = plan.as_dict()
    else:
        rows = []
        for d in plan.get("directors") or []:
            if isinstance(d, dict):
                rows.append(
                    {
                        "director": str(d.get("role") or ""),
                        "choice": str(d.get("choice") or ""),
                        "reason": str(d.get("reason_ru") or d.get("why_ru") or ""),
                    }
                )
        package_id = str(plan.get("package_id") or "")
        niche = str(plan.get("niche") or "")
        luxury = bool(plan.get("luxury_mode"))
        plan_dict = plan

    if experience:
        rows.append(
            {
                "director": "Experience Director",
                "choice": str(experience.get("choice") or ""),
                "reason": str(experience.get("why_ru") or experience.get("reason_ru") or ""),
            }
        )

    crs = commercial_readiness or {}
    if crs:
        scores = crs.get("scores") or {}
        rows.append(
            {
                "director": "Commercial Readiness",
                "choice": f"Overall Commercial {crs.get('overall_commercial', '—')}",
                "reason": (
                    f"Visual {scores.get('visual')} · Trust {scores.get('trust')} · "
                    f"Conversion {scores.get('conversion')} · Performance {scores.get('performance')} · "
                    f"Mobile {scores.get('mobile')} · A11y {scores.get('accessibility')} → "
                    f"{crs.get('label')}"
                ),
            }
        )
        conv = (crs.get("conversion_detail") or {}).get("recommendations") or []
        if conv:
            rows.append(
                {
                    "director": "Conversion Director",
                    "choice": f"CTA {(crs.get('conversion_detail') or {}).get('scores', {}).get('cta', '—')}",
                    "reason": str(conv[0]),
                }
            )

    title_ru = "Почему получился именно такой сайт?"
    return {
        "engine": ENGINE_ID,
        "title_ru": title_ru,
        "title_en": "Why does this site look like this?",
        "package_id": package_id,
        "niche": niche,
        "luxury_mode": luxury,
        "decisions": rows,
        "design_director": design_director or {},
        "design_memory": design_memory or {},
        "commercial_readiness": crs,
        "studio": {
            "engine": plan_dict.get("engine"),
            "apply_keys": sorted((plan_dict.get("apply") or {}).keys()),
        },
        "ssot_ru": (
            "Virtus Core объясняет дизайнерские и коммерческие решения — "
            "Digital Creative Studio, не чёрный ящик."
        ),
    }


def write_experience_replay(product_dir: Path, payload: dict[str, Any]) -> Path:
    path = Path(product_dir) / "experience_replay.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
