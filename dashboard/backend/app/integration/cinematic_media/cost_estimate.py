"""Conservative media cost estimates — dry-run only, never a live provider quote."""

from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

_RATES_PATH = Path(__file__).with_name("cost_rates.json")


@lru_cache(maxsize=1)
def _rates() -> dict[str, Any]:
    data = json.loads(_RATES_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def reload_rates() -> None:
    _rates.cache_clear()


def estimate_scene_cost(
    scene: dict[str, Any],
    *,
    provider_id: str | None = None,
) -> dict[str, Any]:
    """
    Build a dry-run cost plan from scene beats/shots.
    Does NOT call KIE/Kling. quote_certainty stays estimate_only.
    """
    cfg = _rates()
    defaults = dict(cfg.get("defaults") or {})
    pid = (provider_id or str(defaults.get("provider_id") or "kie")).strip().lower()
    providers = cfg.get("providers") or {}
    prow = providers.get(pid) or providers.get("kie") or {}
    rates = dict(prow.get("rates_eur") or {})

    clip_seconds = int(defaults.get("clip_seconds") or 5)
    attempts = max(1, int(defaults.get("max_attempts_per_job") or 2))
    include_images = bool(defaults.get("include_keyframe_images", True))
    safety = float(defaults.get("safety_margin_eur") or 0)

    shots = list(scene.get("shots") or [])
    beats = list(scene.get("beats") or [])
    n_shots = len(shots) or len(beats) or 1

    # Preferred plan: 1 keyframe still + 1 scroll-length I2V clip (not N separate films)
    video_key = f"IMAGE_TO_VIDEO_{clip_seconds}S"
    if video_key not in rates:
        video_key = "IMAGE_TO_VIDEO_5S"
    image_rate = float(rates.get("IMAGE_GENERATION") or 0)
    video_rate = float(rates.get(video_key) or rates.get("TEXT_TO_VIDEO_5S") or 0)

    if image_rate <= 0 or video_rate <= 0:
        return {
            "ok": False,
            "quote_certainty": "unknown",
            "estimated_cost_eur": None,
            "error": "rate_missing",
            "detail": "Cannot estimate — update cost_rates.json after measuring KIE logs",
            "live_quote_available": False,
            "network_called": False,
        }

    keyframe_count = 1 if include_images else 0
    # Optional extra stills for product CTA end-card (shop)
    if str(scene.get("scene_type") or "") in ("product_reveal", "barbershop", "restaurant"):
        keyframe_count = max(keyframe_count, min(3, max(1, n_shots // 3)))

    video_jobs = 1  # one cinematic scroll film
    image_cost = keyframe_count * image_rate * attempts
    video_cost = video_jobs * video_rate * attempts
    subtotal = image_cost + video_cost
    total = round(subtotal + safety, 4)

    line_items = [
        {
            "item": "keyframe_images",
            "count": keyframe_count,
            "unit_eur": image_rate,
            "attempts": attempts,
            "subtotal_eur": round(image_cost, 4),
        },
        {
            "item": "image_to_video_clip",
            "count": video_jobs,
            "clip_seconds": clip_seconds,
            "unit_eur": video_rate,
            "attempts": attempts,
            "subtotal_eur": round(video_cost, 4),
        },
        {
            "item": "safety_margin",
            "subtotal_eur": round(safety, 4),
        },
    ]

    return {
        "ok": True,
        "provider_id": pid,
        "capability": "IMAGE_TO_VIDEO",
        "clip_seconds": clip_seconds,
        "shots_planned": n_shots,
        "video_jobs": video_jobs,
        "keyframe_images": keyframe_count,
        "attempts_budgeted": attempts,
        "line_items": line_items,
        "estimated_cost_eur": total,
        "quote_certainty": str(cfg.get("quote_certainty") or "estimate_only"),
        "live_quote_available": bool(cfg.get("live_quote_available")),
        "network_called": False,
        "note": cfg.get("note"),
        "rates_snapshot": deepcopy(rates),
    }
