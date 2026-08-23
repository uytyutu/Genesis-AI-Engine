"""Scene Director — auto scene from client form (JSON only, no media)."""

from __future__ import annotations

from typing import Any


def _shots_from_beats(beats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    shots: list[dict[str, Any]] = []
    for i, beat in enumerate(beats, start=1):
        shots.append(
            {
                "shot": i,
                "scroll": beat.get("scroll"),
                "action": beat.get("action"),
                "title": str(beat.get("action") or f"shot_{i}").replace("_", " ").title(),
            }
        )
    return shots


def build_scene_spec(
    *,
    niche: str | None = None,
    business_name: str | None = None,
    style: str = "cinematic_realistic",
    product_kind: str = "website",
    city: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    niche_l = (niche or "generic").strip().lower() or "generic"
    desc_l = (description or "").strip().lower()
    blob = f"{niche_l} {desc_l}"
    scene_type = niche_l.replace(" ", "_")
    headline = business_name or "Business"

    if any(k in blob for k in ("barber", "friseur", "haar", "fade", "barbershop")):
        scene_type = "barbershop"
        scene_title = f"Premium barber shop — {headline}"
        if city:
            scene_title += f" ({city})"
        beats = [
            {"scroll": 0.0, "action": "camera_enters_shop"},
            {"scroll": 0.12, "action": "barber_prepares_clippers"},
            {"scroll": 0.25, "action": "haircut_begins"},
            {"scroll": 0.4, "action": "hair_moves_falls"},
            {"scroll": 0.55, "action": "camera_orbits_client"},
            {"scroll": 0.7, "action": "finished_haircut"},
            {"scroll": 0.85, "action": "products_appear"},
            {"scroll": 1.0, "action": "shop_cta"},
        ]
    elif any(k in blob for k in ("restaurant", "gastro", "kitchen", "pasta", "chef")):
        scene_type = "restaurant"
        scene_title = f"Cinematic restaurant — {headline}"
        beats = [
            {"scroll": 0.0, "action": "camera_enters_restaurant"},
            {"scroll": 0.2, "action": "chef_prepares"},
            {"scroll": 0.4, "action": "plating_steam"},
            {"scroll": 0.6, "action": "knife_and_sauce"},
            {"scroll": 0.8, "action": "dish_closeup"},
            {"scroll": 1.0, "action": "menu_booking_cta"},
        ]
    elif product_kind == "shop" or any(k in blob for k in ("shop", "store", "ecom", "product")):
        scene_type = "product_reveal"
        scene_title = f"Product cinematic — {headline}"
        beats = [
            {"scroll": 0.0, "action": "studio_dark"},
            {"scroll": 0.2, "action": "product_enters"},
            {"scroll": 0.4, "action": "detail_orbit"},
            {"scroll": 0.65, "action": "lifestyle_context"},
            {"scroll": 0.85, "action": "catalog_grid"},
            {"scroll": 1.0, "action": "buy_cta"},
        ]
    else:
        scene_title = f"Cinematic site — {headline}"
        beats = [
            {"scroll": 0.0, "action": "establishing_shot"},
            {"scroll": 0.25, "action": "craft_in_progress"},
            {"scroll": 0.5, "action": "human_detail"},
            {"scroll": 0.75, "action": "result_reveal"},
            {"scroll": 1.0, "action": "contact_cta"},
        ]

    shots = _shots_from_beats(beats)
    return {
        "engine": "scene_director_v1",
        "scene_type": scene_type,
        "scene_title": scene_title,
        "business_name": business_name or "",
        "city": city or "",
        "niche": niche or "",
        "style": style,
        "product_kind": product_kind,
        "preferred_capability": "IMAGE_TO_VIDEO",
        "fallback": ["TEXT_TO_VIDEO", "WEBGL_PROCEDURAL"],
        "beats": beats,
        "shots": shots,
        "scroll_binding": "video_progress = scroll_percent",
        "note": "Specification only — no media generated",
    }
