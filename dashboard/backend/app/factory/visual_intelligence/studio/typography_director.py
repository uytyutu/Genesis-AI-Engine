"""Typography Director — thin adapter over Typography Studio.

Ban one-font-for-all. Brand Personality → pair + metrics (LH, tracking, weights).
"""

from __future__ import annotations

from typing import Any

from app.factory.design_dna.typography_studio import (
    decision_as_font_pack,
    emit_typography_studio_css,
    resolve_typography_studio,
)
from app.factory.design_engine.fonts import FontPack

ENGINE_ID = "typography_director_v2"


def decide_typography(
    *,
    package_id: str,
    niche: str | None = None,
    typography_key: str | None = None,
    emotion: str | None = None,
    diversity_salt: str | None = None,
) -> dict[str, Any]:
    """Resolve Typography Studio decision for this niche + package."""
    _ = typography_key  # legacy key ignored — Studio picks from personality
    pid = (package_id or "basic").strip().lower()
    niche_key = (niche or "generic").strip().lower()
    studio = resolve_typography_studio(
        niche_id=niche_key,
        emotion=(emotion or "").strip(),
        package_id=pid,
        diversity_salt=(diversity_salt or f"{niche_key}|{pid}").strip(),
    )
    pack = decision_as_font_pack(studio)
    m = studio.get("metrics") or {}
    scale = {
        "h1": m.get("h1", "2rem"),
        "lh": m.get("body_lh", "1.5"),
        "section_h2": m.get("h2", "1.65rem"),
    }
    personality = studio.get("brand_personality", "")
    reason = (
        f"Typography Studio · {personality} → {studio.get('pair_id')} "
        f"(LH {m.get('body_lh')}, tracking {m.get('tracking_body')})."
    )
    return {
        "engine": ENGINE_ID,
        "role": "Typography Director",
        "choice": pack.label,
        "typography_key": studio.get("pair_id"),
        "reason_ru": reason,
        "reason_en": reason,
        "font_pack": pack,
        "studio": studio,
        "apply": {
            "font_label": pack.label,
            "body_font": pack.body,
            "display_font": pack.display,
            "scale": scale,
            "studio_css": emit_typography_studio_css(studio),
        },
    }


def typography_director_css(decision: dict[str, Any]) -> str:
    apply = decision.get("apply") or {}
    studio_css = apply.get("studio_css")
    if studio_css:
        return str(studio_css)
    # Fallback if older decision shape
    studio = decision.get("studio")
    if isinstance(studio, dict) and studio.get("pair_id"):
        return emit_typography_studio_css(studio)
    scale = apply.get("scale") or {}
    body = apply.get("body_font") or "system-ui, sans-serif"
    display = apply.get("display_font") or body
    h1 = scale.get("h1", "2rem")
    lh = scale.get("lh", "1.4")
    h2 = scale.get("section_h2", "1.65rem")
    return f"""
/* Typography Director (legacy fallback) */
body {{
  font-family: {body};
  line-height: {lh};
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}}
body .hero h1,
body .hero .hero-title,
body h1 {{
  font-family: {display};
  font-size: {h1};
}}
body .section h2 {{
  font-family: {display};
  font-size: {h2};
}}
@media (max-width: 720px) {{
  body {{ line-height: 1.5; }}
  body .hero h1 {{ letter-spacing: -0.02em; }}
}}
"""


__all__ = ["ENGINE_ID", "FontPack", "decide_typography", "typography_director_css"]
