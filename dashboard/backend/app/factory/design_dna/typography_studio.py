"""Typography Studio — Brand Personality → designed type system.

Not just font-family. Factory picks:
  personality → emotion → TypePair (headline/body) → weights, LH, tracking, scale.

Same niche ≠ same fonts every time (diversity_salt). Ban one-font-for-all.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import Any

from app.factory.design_dna.typography_engine import (
    TYPE_PAIRS,
    TypePair,
    _css2,
    catalog_size,
    resolve_type_pair,
)


# ---------------------------------------------------------------------------
# Scale metrics — designed typography, not defaults
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TypeMetrics:
    """Full typography design for a Brand Personality."""

    h1: str
    h2: str
    body_lh: str
    headline_lh: str
    tracking_display: str
    tracking_body: str
    btn_weight: str
    body_weight: str
    display_weight: str
    mobile_h1: str
    mobile_lh: str

    def as_dict(self) -> dict[str, str]:
        return {
            "h1": self.h1,
            "h2": self.h2,
            "body_lh": self.body_lh,
            "headline_lh": self.headline_lh,
            "tracking_display": self.tracking_display,
            "tracking_body": self.tracking_body,
            "btn_weight": self.btn_weight,
            "body_weight": self.body_weight,
            "display_weight": self.display_weight,
            "mobile_h1": self.mobile_h1,
            "mobile_lh": self.mobile_lh,
        }


_SCALE_METRICS: dict[str, TypeMetrics] = {
    "editorial": TypeMetrics(
        h1="clamp(2.05rem, 4.2vw, 3.15rem)",
        h2="clamp(1.4rem, 2.2vw, 1.9rem)",
        body_lh="1.7",
        headline_lh="1.14",
        tracking_display="-0.02em",
        tracking_body="0.01em",
        btn_weight="600",
        body_weight="400",
        display_weight="600",
        mobile_h1="clamp(1.7rem, 6vw, 2.2rem)",
        mobile_lh="1.55",
    ),
    "luxury": TypeMetrics(
        h1="clamp(2.2rem, 4.5vw, 3.35rem)",
        h2="clamp(1.45rem, 2.3vw, 2rem)",
        body_lh="1.75",
        headline_lh="1.12",
        tracking_display="-0.03em",
        tracking_body="0.015em",
        btn_weight="500",
        body_weight="400",
        display_weight="500",
        mobile_h1="clamp(1.75rem, 6.2vw, 2.3rem)",
        mobile_lh="1.6",
    ),
    "cinematic": TypeMetrics(
        h1="clamp(2.15rem, 4.4vw, 3.25rem)",
        h2="clamp(1.4rem, 2.3vw, 1.95rem)",
        body_lh="1.65",
        headline_lh="1.12",
        tracking_display="-0.025em",
        tracking_body="0.005em",
        btn_weight="600",
        body_weight="400",
        display_weight="600",
        mobile_h1="clamp(1.7rem, 6vw, 2.25rem)",
        mobile_lh="1.5",
    ),
    "compact": TypeMetrics(
        h1="clamp(1.85rem, 3.8vw, 2.65rem)",
        h2="clamp(1.3rem, 2vw, 1.65rem)",
        body_lh="1.55",
        headline_lh="1.15",
        tracking_display="-0.01em",
        tracking_body="0",
        btn_weight="700",
        body_weight="400",
        display_weight="700",
        mobile_h1="clamp(1.6rem, 5.5vw, 2.05rem)",
        mobile_lh="1.45",
    ),
    "calm": TypeMetrics(
        h1="clamp(2rem, 4vw, 3rem)",
        h2="clamp(1.35rem, 2.1vw, 1.85rem)",
        body_lh="1.8",
        headline_lh="1.18",
        tracking_display="0.01em",
        tracking_body="0.02em",
        btn_weight="500",
        body_weight="400",
        display_weight="500",
        mobile_h1="clamp(1.65rem, 5.8vw, 2.15rem)",
        mobile_lh="1.65",
    ),
}


# Niche → default Brand Personality emotion (form brief / AI)
NICHE_PERSONALITY: dict[str, str] = {
    "psychology": "calm",
    "therapy": "calm",
    "dental": "trust",
    "medical": "trust",
    "clinic": "trust",
    "law": "trust",
    "accounting": "corporate",
    "restaurant": "warmth",
    "food": "warmth",
    "beauty": "elegance",
    "fashion": "luxury",
    "jewelry": "luxury",
    "auto": "energy",
    "auto_ankauf": "energy",
    "handwerk": "confidence",
    "dachreinigung": "confidence",
    "zaunbau": "confidence",
    "gartenpflege": "organic",
    "green": "organic",
    "cleaning": "clarity",
    "fitness": "energy",
    "computer": "innovation",
    "it": "innovation",
    "energy": "innovation",
    "realestate": "prestige",
    "photography": "editorial",
}


# Extra curated pairs — owner niches (psych / law / restaurant / auto / medical / luxury / craft)
_STUDIO_EXTRA_PAIRS: tuple[TypePair, ...] = (
    # 🧠 Psychologist — trust / calm / safety (diverse instances)
    TypePair(
        id="lora_manrope_calm",
        display='"Lora", Georgia, serif',
        body='"Manrope", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400",
            "family=Manrope:wght@300;400;500;600;700",
        ),
        niches=("psychology", "therapy", "dental"),
        emotions=("calm", "trust", "safety"),
        scale="calm",
        notes="Psychologist A — quiet trust",
    ),
    TypePair(
        id="cormorant_manrope_calm",
        display='"Cormorant Garamond", Georgia, serif',
        body='"Manrope", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Cormorant+Garamond:wght@400;500;600;700",
            "family=Manrope:wght@300;400;500;600;700",
        ),
        niches=("psychology", "therapy", "beauty"),
        emotions=("calm", "trust", "elegance"),
        scale="calm",
        notes="Psychologist B — soft editorial",
    ),
    TypePair(
        id="instrument_source_calm",
        display='"Instrument Serif", Georgia, serif',
        body='"Source Serif 4", Georgia, serif',
        google_css_url=_css2(
            "family=Instrument+Serif:ital@0;1",
            "family=Source+Serif+4:opsz,wght@8..60,300;8..60,400;8..60,600",
        ),
        niches=("psychology", "law", "photography"),
        emotions=("calm", "editorial", "trust"),
        scale="editorial",
        notes="Psychologist C — literary calm",
    ),
    # ⚖️ Lawyer — strict
    TypePair(
        id="ibm_plex_serif_law",
        display='"IBM Plex Serif", Georgia, serif',
        body='"IBM Plex Sans", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=IBM+Plex+Serif:wght@400;500;600;700",
            "family=IBM+Plex+Sans:wght@400;500;600;700",
        ),
        niches=("law", "accounting"),
        emotions=("trust", "corporate", "clarity"),
        scale="editorial",
        notes="Law A — institutional",
    ),
    TypePair(
        id="spectral_source_law",
        display='"Spectral", Georgia, serif',
        body='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Spectral:wght@400;500;600;700",
            "family=Source+Sans+3:wght@400;500;600;700",
        ),
        niches=("law", "accounting", "realestate"),
        emotions=("trust", "prestige", "corporate"),
        scale="editorial",
        notes="Law B — spectral authority",
    ),
    TypePair(
        id="merriweather_law",
        display='"Merriweather", Georgia, serif',
        body='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Merriweather:wght@300;400;700",
            "family=Source+Sans+3:wght@400;500;600;700",
        ),
        niches=("law", "dental", "accounting"),
        emotions=("trust", "clarity", "corporate"),
        scale="editorial",
        notes="Law C — classic brief",
    ),
    # 🍽️ Restaurant — beautiful
    TypePair(
        id="playfair_figtree_food",
        display='"Playfair Display", Georgia, serif',
        body='"Figtree", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Playfair+Display:wght@500;600;700",
            "family=Figtree:wght@300;400;500;600;700",
        ),
        niches=("restaurant", "food", "beauty"),
        emotions=("warmth", "prestige", "boutique"),
        scale="luxury",
        notes="Restaurant A — gold standard",
    ),
    TypePair(
        id="cormorant_dm_food",
        display='"Cormorant", Georgia, serif',
        body='"DM Sans", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Cormorant:wght@400;500;600;700",
            "family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700",
        ),
        niches=("restaurant", "food", "fashion"),
        emotions=("warmth", "elegance", "boutique"),
        scale="editorial",
        notes="Restaurant B — soft plate",
    ),
    TypePair(
        id="fraunces_manrope_food",
        display='"Fraunces", Georgia, serif',
        body='"Manrope", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700",
            "family=Manrope:wght@400;500;600;700",
        ),
        niches=("restaurant", "food", "gartenpflege"),
        emotions=("warmth", "organic", "energy"),
        scale="editorial",
        notes="Restaurant C — modern table",
    ),
    # 🚗 Auto — energy
    TypePair(
        id="space_sora_auto",
        display='"Space Grotesk", "Segoe UI", system-ui, sans-serif',
        body='"Sora", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Space+Grotesk:wght@500;600;700",
            "family=Sora:wght@300;400;500;600;700",
        ),
        niches=("auto", "auto_ankauf", "computer"),
        emotions=("energy", "innovation", "confidence"),
        scale="compact",
        notes="Auto A — kinetic",
    ),
    TypePair(
        id="exo_rajdhani_auto",
        display='"Exo 2", "Segoe UI", system-ui, sans-serif',
        body='"Rajdhani", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Exo+2:wght@500;600;700;800",
            "family=Rajdhani:wght@400;500;600;700",
        ),
        niches=("auto", "auto_ankauf", "fitness", "energy"),
        emotions=("energy", "confidence", "innovation"),
        scale="compact",
        notes="Auto B — race panel",
    ),
    TypePair(
        id="sora_inter_auto",
        display='"Sora", "Segoe UI", system-ui, sans-serif',
        body='"Inter", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Sora:wght@500;600;700",
            "family=Inter:wght@400;500;600;700",
        ),
        niches=("auto", "computer", "it"),
        emotions=("energy", "clarity", "corporate"),
        scale="compact",
        notes="Auto C — clean garage",
    ),
    # 💎 Luxury
    TypePair(
        id="dm_serif_jakarta_lux",
        display='"DM Serif Display", Georgia, serif',
        body='"Plus Jakarta Sans", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=DM+Serif+Display:ital@0;1",
            "family=Plus+Jakarta+Sans:wght@300;400;500;600;700",
        ),
        niches=("fashion", "beauty", "jewelry", "realestate"),
        emotions=("luxury", "elegance", "prestige"),
        scale="luxury",
        notes="Luxury A — Canela-class",
    ),
    TypePair(
        id="cormorant_outfit_lux",
        display='"Cormorant Garamond", Georgia, serif',
        body='"Outfit", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Cormorant+Garamond:wght@400;500;600;700",
            "family=Outfit:wght@300;400;500;600;700",
        ),
        niches=("fashion", "beauty", "jewelry", "restaurant"),
        emotions=("luxury", "elegance", "boutique"),
        scale="luxury",
        notes="Luxury B — soft couture",
    ),
    # 🏥 Medical — clean
    TypePair(
        id="manrope_medical",
        display='"Manrope", "Segoe UI", system-ui, sans-serif',
        body='"Manrope", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2("family=Manrope:wght@300;400;500;600;700"),
        niches=("dental", "medical", "clinic"),
        emotions=("trust", "clarity", "calm"),
        scale="calm",
        notes="Medical A — single-family clarity (display sizes differ)",
    ),
    TypePair(
        id="jakarta_ibm_medical",
        display='"Plus Jakarta Sans", "Segoe UI", system-ui, sans-serif',
        body='"IBM Plex Sans", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Plus+Jakarta+Sans:wght@400;500;600;700",
            "family=IBM+Plex+Sans:wght@300;400;500;600;700",
        ),
        niches=("dental", "medical", "clinic"),
        emotions=("trust", "clarity", "corporate"),
        scale="editorial",
        notes="Medical B — clinic dual sans",
    ),
    TypePair(
        id="inter_source_medical",
        display='"Inter", "Segoe UI", system-ui, sans-serif',
        body='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Inter:wght@400;500;600;700",
            "family=Source+Sans+3:wght@300;400;500;600;700",
        ),
        niches=("dental", "medical", "clinic", "computer"),
        emotions=("clarity", "trust", "innovation"),
        scale="compact",
        notes="Medical C — technical care",
    ),
    # 🔧 Craft DE — roof / fence / garden (not forced luxury serif)
    TypePair(
        id="manrope_ibm_plex_industrial",
        display='"Manrope", "Segoe UI", system-ui, sans-serif',
        body='"IBM Plex Sans", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Manrope:wght@400;500;600;700;800",
            "family=IBM+Plex+Sans:wght@300;400;500;600;700",
        ),
        niches=("dachreinigung", "handwerk", "zaunbau", "cleaning", "auto"),
        emotions=("confidence", "clarity", "trust", "corporate"),
        scale="editorial",
        notes="Brand Book — German industrial precision (DachKlar)",
    ),
    TypePair(
        id="oswald_figtree_craft",
        display='"Oswald", "Arial Narrow", sans-serif',
        body='"Figtree", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Oswald:wght@500;600;700",
            "family=Figtree:wght@400;500;600;700",
        ),
        niches=("handwerk", "dachreinigung", "zaunbau", "cleaning"),
        emotions=("confidence", "energy", "corporate"),
        scale="compact",
        notes="Craft A — Meister sign",
    ),
    TypePair(
        id="barlow_source_craft",
        display='"Barlow Condensed", "Arial Narrow", sans-serif',
        body='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Barlow+Condensed:wght@500;600;700",
            "family=Source+Sans+3:wght@400;500;600;700",
        ),
        niches=("handwerk", "dachreinigung", "zaunbau", "auto"),
        emotions=("confidence", "energy", "clarity"),
        scale="compact",
        notes="Craft B — workboard",
    ),
    TypePair(
        id="fraunces_source_garden",
        display='"Fraunces", Georgia, serif',
        body='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700",
            "family=Source+Sans+3:wght@400;500;600;700",
        ),
        niches=("gartenpflege", "green", "handwerk"),
        emotions=("organic", "calm", "warmth"),
        scale="editorial",
        notes="Garden — soft landscape",
    ),
)


def all_type_pairs() -> tuple[TypePair, ...]:
    """Base engine pairs + Typography Studio extras (dedupe by id)."""
    seen: set[str] = set()
    out: list[TypePair] = []
    for p in (*TYPE_PAIRS, *_STUDIO_EXTRA_PAIRS):
        if p.id in seen:
            continue
        seen.add(p.id)
        # Map calm scale into metrics table (TypePair.scale may be "calm")
        out.append(p)
    return tuple(out)


def metrics_for_scale(scale: str, *, package_id: str = "business") -> TypeMetrics:
    key = (scale or "editorial").strip().lower()
    if key == "calm":
        base = _SCALE_METRICS["calm"]
    else:
        base = _SCALE_METRICS.get(key) or _SCALE_METRICS["editorial"]
    pid = (package_id or "business").strip().lower()
    # Premium may step up slightly — never to layout-breaking sizes.
    if pid == "premium" and key in ("editorial", "luxury", "cinematic"):
        return replace(
            base,
            h1=base.h1.replace("3.15rem", "3.35rem")
            .replace("3.25rem", "3.4rem")
            .replace("3.35rem", "3.5rem"),
        )
    if pid == "basic":
        return replace(
            base,
            h1="clamp(1.75rem, 3.6vw, 2.35rem)",
            h2="clamp(1.25rem, 2vw, 1.55rem)",
            mobile_h1="clamp(1.5rem, 5.2vw, 1.95rem)",
        )
    return base


def resolve_brand_personality(
    *,
    niche_id: str,
    emotion: str = "",
    diversity_salt: str = "",
) -> str:
    """Brand Personality emotion string for Typography Studio."""
    niche = (niche_id or "generic").strip().lower()
    emo = (emotion or "").strip().lower()
    if emo:
        return emo.split()[0] if emo else NICHE_PERSONALITY.get(niche, "clarity")
    return NICHE_PERSONALITY.get(niche, "clarity")


def resolve_typography_studio(
    *,
    niche_id: str,
    emotion: str = "",
    package_id: str = "business",
    diversity_salt: str = "",
) -> dict[str, Any]:
    """Full Typography Studio decision — AI picks pair + metrics from personality."""
    personality = resolve_brand_personality(
        niche_id=niche_id, emotion=emotion, diversity_salt=diversity_salt
    )
    niche = (niche_id or "generic").strip().lower()
    pid = (package_id or "business").strip().lower()
    salt = (diversity_salt or "").strip()

    pairs = all_type_pairs()
    scored: list[tuple[int, TypePair]] = []
    for pair in pairs:
        score = 1
        if niche in pair.niches:
            score += 14
        if personality and any(e in personality or personality in e for e in pair.emotions):
            score += 10
        if pid == "premium" and pair.scale in ("luxury", "cinematic", "editorial", "calm"):
            score += 3
        if pid == "basic" and pair.scale in ("compact", "calm"):
            score += 3
        # Prefer multi-family for Premium (ban identical display=body unless medical A)
        if pid == "premium" and pair.display == pair.body and "medical" not in pair.notes.lower():
            score -= 6
        scored.append((score, pair))
    scored.sort(key=lambda x: (-x[0], x[1].id))
    # Diversity: niche pool + wider runner-ups so salt actually changes fonts.
    niche_pool = [p for s, p in scored if niche in p.niches and s >= 8]
    near = [p for s, p in scored if s >= scored[0][0] - 8]
    # Merge unique by id — prefer niche hits first, then near scores
    seen: set[str] = set()
    top: list[TypePair] = []
    for p in niche_pool + near + [scored[0][1]]:
        if p.id in seen:
            continue
        seen.add(p.id)
        top.append(p)
        if len(top) >= 10:
            break
    if not top:
        top = [scored[0][1]]
    dig = hashlib.sha256(
        f"{niche}|{personality}|{pid}|studio|{salt}|{len(top)}".encode()
    ).hexdigest()
    idx = int(dig[:10], 16)
    # Second nibble biases away from always picking index 0 when salt is weak
    bias = int(dig[10:14], 16) % max(1, min(len(top), 5))
    pair = top[(idx + bias) % len(top)]
    metrics = metrics_for_scale(pair.scale, package_id=pid)

    return {
        "engine": "typography_studio_v1",
        "brand_personality": personality,
        "typography_style": pair.scale,
        "pair": pair.as_dict(),
        "pair_id": pair.id,
        "headline": pair.display,
        "body": pair.body,
        "buttons_weight": metrics.btn_weight,
        "line_height": metrics.body_lh,
        "letter_spacing": metrics.tracking_body,
        "metrics": metrics.as_dict(),
        "google_css_url": pair.google_css_url,
        "catalog_fonts": catalog_size(),
        "pairs_available": len(pairs),
        "notes": pair.notes,
    }


def emit_typography_studio_css(decision: dict[str, Any]) -> str:
    """CSS for designed typography (weights, LH, tracking, mobile)."""
    m = decision.get("metrics") or {}
    display = decision.get("headline") or "Georgia, serif"
    body = decision.get("body") or "system-ui, sans-serif"
    h1 = m.get("h1", "clamp(2rem, 4vw, 3rem)")
    h2 = m.get("h2", "1.65rem")
    body_lh = m.get("body_lh", "1.65")
    headline_lh = m.get("headline_lh", "1.15")
    track_d = m.get("tracking_display", "-0.02em")
    track_b = m.get("tracking_body", "0.01em")
    btn_w = m.get("btn_weight", "600")
    body_w = m.get("body_weight", "400")
    disp_w = m.get("display_weight", "600")
    mob_h1 = m.get("mobile_h1", "2rem")
    mob_lh = m.get("mobile_lh", "1.5")
    pid = decision.get("pair_id", "")
    personality = decision.get("brand_personality", "")

    return f"""
/* Typography Studio · personality={personality} · pair={pid} · ssot */
:root {{
  --font-display: {display};
  --font-body: {body};
  --font-sans: {body};
  --type-body-lh: {body_lh};
  --type-headline-lh: {headline_lh};
  --type-track-display: {track_d};
  --type-track-body: {track_b};
  --type-btn-weight: {btn_w};
}}
body {{
  font-family: var(--font-body);
  font-weight: {body_w};
  line-height: var(--type-body-lh);
  letter-spacing: var(--type-track-body);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
  overflow-wrap: anywhere;
  word-break: normal;
}}
body .hero h1,
body .hero .hero-title,
body h1,
body .page-title,
body .section h2,
body h2,
body h3 {{
  font-family: var(--font-display);
  max-width: 100%;
  overflow-wrap: anywhere;
  word-break: break-word;
  hyphens: auto;
  white-space: normal;
}}
body .hero h1,
body .hero .hero-title,
body h1,
body .page-title {{
  font-weight: {disp_w};
  font-size: {h1};
  line-height: var(--type-headline-lh);
  letter-spacing: var(--type-track-display);
}}
body .section h2,
body h2 {{
  font-weight: {disp_w};
  font-size: {h2};
  line-height: 1.22;
  letter-spacing: var(--type-track-display);
}}
body .btn,
body button.btn,
body a.btn {{
  font-family: var(--font-body);
  font-weight: var(--type-btn-weight);
  letter-spacing: 0.02em;
  white-space: normal;
  max-width: 100%;
}}
@media (max-width: 720px) {{
  body {{ line-height: {mob_lh}; }}
  body .hero h1,
  body .hero .hero-title,
  body h1 {{
    font-size: {mob_h1};
    letter-spacing: -0.015em;
    max-width: 100%;
  }}
}}
"""


def decision_as_font_pack(decision: dict[str, Any]):
    """Bridge to FontPack for existing font_link_tags() callers."""
    from app.factory.design_engine.fonts import FontPack

    pair = decision.get("pair") or {}
    return FontPack(
        body=str(decision.get("body") or '"Segoe UI", system-ui, sans-serif'),
        display=str(decision.get("headline") or decision.get("body") or "Georgia, serif"),
        google_css_url=str(decision.get("google_css_url") or ""),
        label=str(pair.get("id") or decision.get("pair_id") or "Typography Studio"),
    )


# Keep resolve_type_pair import usable for stores — prefer studio when available
def resolve_type_pair_studio(
    *,
    niche_id: str,
    emotion: str = "",
    package_id: str = "business",
    diversity_salt: str = "",
) -> TypePair:
    """TypePair via Typography Studio pool (back-compat for stores)."""
    decision = resolve_typography_studio(
        niche_id=niche_id,
        emotion=emotion,
        package_id=package_id,
        diversity_salt=diversity_salt,
    )
    pid = decision["pair_id"]
    for p in all_type_pairs():
        if p.id == pid:
            return p
    return resolve_type_pair(
        niche_id=niche_id,
        emotion=emotion,
        package_id=package_id,
        diversity_salt=diversity_salt,
    )


__all__ = [
    "NICHE_PERSONALITY",
    "TypeMetrics",
    "all_type_pairs",
    "decision_as_font_pack",
    "emit_typography_studio_css",
    "metrics_for_scale",
    "resolve_brand_personality",
    "resolve_typography_studio",
    "resolve_type_pair_studio",
]
