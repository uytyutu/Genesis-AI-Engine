"""Motion Engine — Basic / Business / Premium (CSS-first for client deliverables).

Premium on client sites = richer CSS (parallax, glass, reveal, section transitions).
Lottie / Rive / Spline / 3D Hero stay platform-showcase or waitlist — never forced
into client ZIP (Quality Gate performance contract).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

MotionTier = Literal["basic", "business", "premium"]

_TIER_FEATURES: dict[str, tuple[str, ...]] = {
    "basic": ("fade", "hover", "micro"),
    "business": ("fade", "hover", "micro", "parallax", "glass", "reveal", "section_transition"),
    "premium": (
        "fade",
        "hover",
        "micro",
        "parallax",
        "glass",
        "reveal",
        "section_transition",
        "cinematic_hero",
        "interactive_cta",
        # Platform-only markers (not injected into client HTML as heavy libs)
        "platform_lottie_slot",
        "platform_3d_slot",
    ),
}


@dataclass(frozen=True)
class MotionPlan:
    tier: MotionTier
    features: tuple[str, ...]
    css_class: str
    allow_heavy_libs: bool  # True only for surface=platform
    legacy_motion_level: str  # maps to motion_brief: none | css | 3d_premium

    def as_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "features": list(self.features),
            "css_class": self.css_class,
            "allow_heavy_libs": self.allow_heavy_libs,
            "legacy_motion_level": self.legacy_motion_level,
        }


def resolve_motion_tier(
    *,
    requested: str | None = None,
    style_default: str | None = None,
    package_id: str | None = None,
    surface: str = "website",
) -> MotionPlan:
    raw = (requested or style_default or "").strip().lower()
    if not raw:
        pkg = (package_id or "basic").strip().lower()
        raw = {"basic": "basic", "business": "business", "premium": "premium"}.get(
            pkg, "business" if surface == "platform" else "basic"
        )
    aliases = {
        "none": "basic",
        "css": "business",
        "3d_premium": "premium",
        "3d": "premium",
    }
    tier: MotionTier = aliases.get(raw, raw)  # type: ignore[assignment]
    if tier not in _TIER_FEATURES:
        tier = "basic"
    # Client surfaces never enable heavy libs even at premium
    allow_heavy = surface == "platform" and tier == "premium"
    legacy = "css" if tier in {"basic", "business", "premium"} else "none"
    if surface == "platform" and tier == "premium":
        legacy = "css"  # still CSS on marketing; 3d_premium remains waitlist
    return MotionPlan(
        tier=tier,
        features=_TIER_FEATURES[tier],
        css_class=f"vie-motion-{tier}",
        allow_heavy_libs=allow_heavy,
        legacy_motion_level=legacy,
    )


def emit_motion_css(tier: MotionTier | str, *, surface: str = "website") -> str:
    """Extra CSS layered on motion_kit — tier-aware, reduced-motion safe."""
    t = (tier or "basic").strip().lower()
    if t not in _TIER_FEATURES:
        t = "basic"
    bits = [
        f"/* Visual Intelligence · Motion Engine · {t} · surface={surface} */",
        f"body.vie-motion-{t} {{ --vie-motion-tier: '{t}'; }}",
    ]
    if t == "basic":
        bits.append(
            """
body.vie-motion-basic .reveal { transition: opacity .45s ease, transform .45s ease; }
body.vie-motion-basic .svc-card:hover,
body.vie-motion-basic .service-card:hover,
body.vie-motion-basic .product-card:hover { transform: translateY(-2px); }
"""
        )
    if t in {"business", "premium"}:
        bits.append(
            """
body.vie-motion-business .hero,
body.vie-motion-premium .hero {
  position: relative;
}
body.vie-motion-business .hero-glass,
body.vie-motion-premium .hero-glass,
body.vie-motion-business .vie-glass,
body.vie-motion-premium .vie-glass {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  background: color-mix(in srgb, var(--surface, #fff) 72%, transparent);
}
body.vie-motion-business .section,
body.vie-motion-premium .section {
  transition: opacity .55s ease, transform .55s ease;
}
body.vie-motion-business [data-vie-section],
body.vie-motion-premium [data-vie-section] {
  view-timeline-name: --vie-section;
}
"""
        )
    if t == "premium":
        bits.append(
            """
body.vie-motion-premium .hero {
  isolation: isolate;
}
body.vie-motion-premium .hero::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(ellipse at 30% 20%, color-mix(in srgb, var(--acc, #94a3b8) 18%, transparent), transparent 55%);
  opacity: .85;
  z-index: 0;
}
body.vie-motion-premium .cta-button,
body.vie-motion-premium .btn-primary {
  transition: transform .25s ease, box-shadow .25s ease, filter .25s ease;
}
body.vie-motion-premium .cta-button:hover,
body.vie-motion-premium .btn-primary:hover {
  transform: translateY(-2px) scale(1.01);
  filter: brightness(1.04);
}
body.vie-motion-premium .vie-cinematic {
  animation: vieCinematic 1.1s ease both;
}
@keyframes vieCinematic {
  from { opacity: 0; transform: translateY(18px) scale(.985); filter: blur(2px); }
  to { opacity: 1; transform: none; filter: none; }
}
@media (prefers-reduced-motion: reduce) {
  body.vie-motion-premium .vie-cinematic { animation: none !important; }
  body.vie-motion-premium .hero::after { opacity: .4; }
}
"""
        )
    if surface == "platform" and t == "premium":
        bits.append(
            """
/* Platform showcase slots — CSS placeholders; heavy libs optional via React */
body[data-vie-surface="platform"].vie-motion-premium .vie-platform-slot {
  min-height: 12rem;
  border-radius: 1.25rem;
  border: 1px solid color-mix(in srgb, var(--line, #e2e8f0) 80%, transparent);
}
"""
        )
    return "\n".join(bits)
