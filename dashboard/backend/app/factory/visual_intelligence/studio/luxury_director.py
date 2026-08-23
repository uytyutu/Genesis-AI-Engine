"""Luxury Director — Luxury Mode that changes composition tokens + CSS."""

from __future__ import annotations

from typing import Any

ENGINE_ID = "luxury_director_v1"


def decide_luxury(*, package_id: str, niche: str | None = None) -> dict[str, Any]:
    pid = (package_id or "basic").strip().lower()
    enabled = pid == "premium"
    niche_key = (niche or "generic").strip().lower()

    # Hero pick label for Experience Replay (maps to cinematic pool B/D/F)
    hero_pick = {
        "dental": ("Hero №18 · Cinematic Clinical", "B"),
        "beauty": ("Hero №22 · Soft Luxury Split", "D"),
        "law": ("Hero №11 · Authority Editorial", "F"),
        "restaurant": ("Hero №9 · Atmosphere Full-bleed", "D"),
        "auto": ("Hero №14 · Precision Media", "B"),
        "psychology": ("Hero №31 · Therapy Trust Immersive", "D"),
    }.get(niche_key, ("Hero №7 · Cinematic Default", "B"))

    if not enabled:
        return {
            "engine": ENGINE_ID,
            "role": "Luxury Director",
            "choice": "Off",
            "luxury_mode": False,
            "reason_ru": "Luxury Mode только для Premium — клиент купил эмоцию дорогого бренда.",
            "reason_en": "Luxury Mode is Premium-only — emotion of a high-end brand.",
            "apply": {"luxury_mode": False, "data_luxury": "0"},
        }

    return {
        "engine": ENGINE_ID,
        "role": "Luxury Director",
        "choice": hero_pick[0],
        "hero_layout_prefer": hero_pick[1],
        "luxury_mode": True,
        "reason_ru": f"Лучше подходит нише «{niche_key}» — кинематографичный Hero и богатая композиция.",
        "reason_en": f"Best fit for niche «{niche_key}» — cinematic hero and rich composition.",
        "apply": {
            "luxury_mode": True,
            "data_luxury": "1",
            "density": "cinematic",
            "hero_class_extra": "hero-luxury vie-cinematic",
            "section_gap_scale": 1.35,
            "cta_style": "premium_glow",
        },
    }


def luxury_director_css(*, enabled: bool) -> str:
    """CSS that actually ships in the landing — not meta."""
    if not enabled:
        return """
/* Luxury Director — off */
body[data-luxury="0"] .hero { --lux-space: 1; }
"""
    return """
/* Luxury Director — Luxury Mode (ships in HTML) */
body[data-luxury="1"] {
  --lux-space: 1.35;
  --lux-display-tracking: -0.035em;
  --lux-hero-min: min(90vh, 920px);
}
body[data-luxury="1"] .hero {
  min-height: var(--lux-hero-min);
  padding-top: calc(4.5rem * var(--lux-space));
  padding-bottom: calc(4.5rem * var(--lux-space));
}
body[data-luxury="1"] .hero.has-photo,
body[data-luxury="1"] .hero.has-hero-image {
  position: relative;
}
body[data-luxury="1"] .hero.has-photo::before,
body[data-luxury="1"] .hero.has-hero-image::before {
  content: "";
  pointer-events: none;
  position: absolute;
  inset: 0;
  z-index: 0;
  background: linear-gradient(105deg, rgba(8,6,4,0.58) 0%, rgba(8,6,4,0.32) 45%, rgba(8,6,4,0.16) 100%);
}
body[data-luxury="1"] .hero.has-photo > *,
body[data-luxury="1"] .hero.has-hero-image > * {
  position: relative;
  z-index: 1;
}
body[data-luxury="1"] .hero.has-hero-image {
  min-height: min(92vh, 960px);
}
body[data-luxury="1"] .hero h1,
body[data-luxury="1"] .hero .hero-title {
  font-size: clamp(2.4rem, 5.5vw, 4.1rem);
  letter-spacing: var(--lux-display-tracking);
  line-height: 1.05;
  font-weight: 650;
}
body[data-luxury="1"] .hero p,
body[data-luxury="1"] .hero .hero-sub {
  font-size: clamp(1.05rem, 1.6vw, 1.25rem);
  line-height: 1.55;
  max-width: 36rem;
  opacity: 0.92;
}
body[data-luxury="1"] .section {
  padding-top: calc(4.75rem * var(--lux-space));
  padding-bottom: calc(4.75rem * var(--lux-space));
}
body[data-luxury="1"] .section h2 {
  font-size: clamp(1.75rem, 3vw, 2.35rem);
  letter-spacing: -0.03em;
}
body[data-luxury="1"] .service-card,
body[data-luxury="1"] .benefit-card,
body[data-luxury="1"] [class*="card"] {
  border-radius: 1.15rem;
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.55);
}
body[data-luxury="1"] .btn,
body[data-luxury="1"] .topbar-cta,
body[data-luxury="1"] a.btn {
  letter-spacing: 0.045em;
  text-transform: none;
  padding: 0.95rem 1.65rem;
  border-radius: 999px;
  color: #1a1410;
  background: linear-gradient(145deg, #f0e0c4 0%, #d4b07a 48%, #b8894f 100%);
  border: 1px solid rgba(240, 224, 196, 0.75);
  box-shadow: 0 12px 32px rgba(168, 132, 74, 0.32), inset 0 1px 0 rgba(255,255,255,0.35);
  transition: transform 0.35s ease, box-shadow 0.35s ease, filter 0.35s ease;
}
body[data-luxury="1"] .btn:hover,
body[data-luxury="1"] .topbar-cta:hover {
  transform: translateY(-2px);
  filter: brightness(1.04);
  box-shadow: 0 18px 40px rgba(168, 132, 74, 0.4), inset 0 1px 0 rgba(255,255,255,0.4);
}
body[data-luxury="1"].vie-motion-premium .hero::after {
  content: "";
  pointer-events: none;
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, rgba(0,0,0,0.42), rgba(0,0,0,0.12) 55%, transparent 78%);
  mix-blend-mode: soft-light;
}
@media (max-width: 720px) {
  body[data-luxury="1"] .hero { min-height: auto; padding-top: 3.25rem; }
  body[data-luxury="1"] .hero h1 { font-size: clamp(1.85rem, 8vw, 2.4rem); }
}
"""
