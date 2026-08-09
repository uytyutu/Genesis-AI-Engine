"""Experience-language CSS/JS overlays for Factory sites (motion, glass, tilt)."""

from __future__ import annotations

from typing import Any


_MODE_VARS: dict[str, dict[str, str]] = {
    "industrial_craft": {
        "--exp-accent": "#ef4444",
        "--exp-glass": "rgba(15,23,42,0.55)",
        "--exp-tilt": "8deg",
        "--exp-parallax": "18px",
    },
    "showroom_gloss": {
        "--exp-accent": "#d4af37",
        "--exp-glass": "rgba(10,10,14,0.45)",
        "--exp-tilt": "10deg",
        "--exp-parallax": "22px",
    },
    "clinical_clean": {
        "--exp-accent": "#0ea5e9",
        "--exp-glass": "rgba(248,250,252,0.72)",
        "--exp-tilt": "5deg",
        "--exp-parallax": "12px",
    },
    "editorial_soft": {
        "--exp-accent": "#78716c",
        "--exp-glass": "rgba(250,248,244,0.65)",
        "--exp-tilt": "4deg",
        "--exp-parallax": "10px",
    },
    "atelier_warm": {
        "--exp-accent": "#c2410c",
        "--exp-glass": "rgba(41,37,36,0.5)",
        "--exp-tilt": "7deg",
        "--exp-parallax": "16px",
    },
    "glass_3d": {
        "--exp-accent": "#eab308",
        "--exp-glass": "rgba(24,24,27,0.4)",
        "--exp-tilt": "12deg",
        "--exp-parallax": "24px",
    },
    "tech_energy": {
        "--exp-accent": "#fbbf24",
        "--exp-glass": "rgba(6,22,30,0.55)",
        "--exp-tilt": "6deg",
        "--exp-parallax": "20px",
    },
    "cinematic_photo": {
        "--exp-accent": "#34d399",
        "--exp-glass": "rgba(15,23,42,0.5)",
        "--exp-tilt": "6deg",
        "--exp-parallax": "14px",
    },
}


def _resolve_mode(brief_or_media_mode: Any) -> str:
    if brief_or_media_mode is None:
        return "cinematic_photo"
    if isinstance(brief_or_media_mode, str):
        return brief_or_media_mode.strip() or "cinematic_photo"
    mode = getattr(brief_or_media_mode, "media_mode", None)
    if isinstance(mode, str) and mode.strip():
        return mode.strip()
    if isinstance(brief_or_media_mode, dict):
        m = brief_or_media_mode.get("media_mode")
        if isinstance(m, str) and m.strip():
            return m.strip()
    return "cinematic_photo"


def experience_css(brief_or_media_mode: Any = None) -> str:
    """Niche-complementary experience CSS (magnetic CTA, tilt, parallax, glass, reveal)."""
    mode = _resolve_mode(brief_or_media_mode)
    vars_map = _MODE_VARS.get(mode, _MODE_VARS["cinematic_photo"])
    var_block = "\n".join(f"  {k}: {v};" for k, v in vars_map.items())
    return f"""/* Virtus Core experience_language */
:root {{
{var_block}
}}
.glass {{
  background: var(--exp-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.12);
}}
.hero-parallax {{
  will-change: transform;
  transform: translate3d(0, calc(var(--exp-scroll, 0) * var(--exp-parallax)), 0);
}}
.btn, .topbar-cta {{
  transition: transform .25s ease, box-shadow .25s ease;
  transform: translate3d(var(--mx, 0), var(--my, 0), 0);
}}
.btn:hover, .topbar-cta:hover {{
  box-shadow: 0 10px 28px color-mix(in srgb, var(--exp-accent) 35%, transparent);
}}
.svc-card, .process-card {{
  transform-style: preserve-3d;
  transition: transform .35s ease;
  will-change: transform;
}}
.svc-card.is-tilt, .process-card.is-tilt {{
  transform: perspective(900px) rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
}}
.exp-reveal {{
  opacity: 0;
  transform: translateY(18px);
  transition: opacity .55s ease, transform .55s ease;
}}
.exp-reveal.is-in {{
  opacity: 1;
  transform: none;
}}
.exp-cursor {{
  position: fixed;
  width: 18px;
  height: 18px;
  margin: -9px 0 0 -9px;
  border-radius: 50%;
  pointer-events: none;
  z-index: 9999;
  border: 1.5px solid var(--exp-accent);
  opacity: .55;
  mix-blend-mode: difference;
  transition: transform .15s ease;
}}
@media (prefers-reduced-motion: reduce) {{
  .hero-parallax, .btn, .topbar-cta, .svc-card, .process-card, .exp-reveal {{
    transition: none !important;
    transform: none !important;
  }}
  .exp-cursor {{ display: none !important; }}
  .exp-reveal {{ opacity: 1; }}
}}
"""


def experience_js() -> str:
    """Motion JS for demos.

    Disabled: previously returned a bare IIFE without <script>, which rendered
    as visible source text on the client page. Do not re-enable without wrapping
    in a proper <script> tag (and product approval).
    """
    return ""


__all__ = ["experience_css", "experience_js"]