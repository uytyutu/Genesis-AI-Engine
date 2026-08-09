"""Atmosphere Pack — Brand Book becomes the page director (Sprint 2).

Atmosphere ≠ background.
Atmosphere = first impression: hero media language, lighting, motion, depth,
texture, glass, CTA feeling, section-as-scene.

Scene Layers (every page):
  1. Content   — text, cards, forms
  2. Atmosphere — sky, light, particles, cinematic media
  3. Motion    — reveal, parallax, hover, CTA life
  4. Depth     — glass, shadow, volume
  5. Identity  — niche-locked cues (roof ≠ café)

Acceptance: remove the logo → character still readable from atmosphere alone.
FAIL if atmosphere is interchangeable across niches.
"""

from __future__ import annotations

import hashlib
import html as html_lib
from dataclasses import asdict, dataclass, field
from typing import Any

from app.factory.design_dna.brand_book import BrandBook
from app.factory.design_dna.dna import DesignDNA


@dataclass(frozen=True)
class MediaBrief:
    """Instruction for Pillow / Image Provider / video — never generic stock."""

    role: str  # hero | background | gallery | team | equipment | …
    concept: str
    must_include: tuple[str, ...]
    must_forbid: tuple[str, ...]
    seed: str
    size: tuple[int, int] = (1600, 900)
    image_prompt: str = ""

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["must_include"] = list(self.must_include)
        d["must_forbid"] = list(self.must_forbid)
        d["size"] = list(self.size)
        return d

    def to_image_prompt(self, *, brand_name: str = "", niche_id: str = "") -> str:
        if self.image_prompt.strip():
            return self.image_prompt.strip()
        include = ", ".join(self.must_include[:6])
        forbid = ", ".join(self.must_forbid[:6]) or "stock café, salon, SaaS cliché"
        return (
            f"Premium brand visual for {brand_name or 'company'} ({niche_id}). "
            f"Role={self.role}. Concept={self.concept}. Include: {include}. "
            f"Forbidden: {forbid}. Unique European studio quality."
        )


@dataclass(frozen=True)
class AtmospherePack:
    """Living experience recipe directed by Brand Book."""

    brand_name: str
    niche_id: str
    package_id: str
    metaphor: str
    core_emotion: str
    atmosphere_mode: str
    scene_language: tuple[str, ...]
    texture_language: tuple[str, ...]
    motion_language: str
    camera_feeling: str
    scroll_feeling: str
    cta_feeling: str
    sound_mood: str
    illustration_style: str
    glass_level: str
    shadow_language: str
    icon_language: str
    lighting: str
    layers: tuple[str, ...]
    media_briefs: tuple[MediaBrief, ...]
    fingerprint: str
    html_nodes: str = ""
    css_layers: str = ""
    js_motion: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "brand_name": self.brand_name,
            "niche_id": self.niche_id,
            "package_id": self.package_id,
            "metaphor": self.metaphor,
            "core_emotion": self.core_emotion,
            "atmosphere_mode": self.atmosphere_mode,
            "scene_language": list(self.scene_language),
            "texture_language": list(self.texture_language),
            "motion_language": self.motion_language,
            "camera_feeling": self.camera_feeling,
            "scroll_feeling": self.scroll_feeling,
            "cta_feeling": self.cta_feeling,
            "sound_mood": self.sound_mood,
            "illustration_style": self.illustration_style,
            "glass_level": self.glass_level,
            "shadow_language": self.shadow_language,
            "icon_language": self.icon_language,
            "lighting": self.lighting,
            "layers": list(self.layers),
            "media_briefs": [b.as_dict() for b in self.media_briefs],
            "fingerprint": self.fingerprint,
            "director": "brand_book",
            "acceptance": (
                "Without logo, niche character must remain readable from atmosphere alone."
            ),
        }


_LAYERS = (
    "content",
    "atmosphere",
    "motion",
    "depth",
    "identity",
)

# Niche-locked camera / sound / lighting — not interchangeable
_NICHE_DIRECTION: dict[str, dict[str, str]] = {
    "dachreinigung": {
        "camera": "drone height · slow orbit over wet tiles · sky dominant",
        "scroll": "soft descent from sky to roof · long breathing reveals",
        "cta": "calm large buttons · generous air · no urgency red",
        "sound": "distant rain clearing · wind on ridge · quiet confidence",
        "illustration": "industrial silhouette · slate geometry · water glints",
        "lighting": "post-storm morning sun · cool sky rim · warm tile specular",
        "shadow": "soft deep under eaves · long cool ground shadow",
    },
    "zaunbau": {
        "camera": "ground-level line along fence · dusk edge light",
        "scroll": "horizontal clarity · measured step reveals",
        "cta": "solid clear buttons · craft spacing",
        "sound": "metal click · evening air · workshop hush",
        "illustration": "posts · rails · iron geometry",
        "lighting": "amber dusk on iron · warm umber fill",
        "shadow": "hard post shadows · soft ground",
    },
    "gartenpflege": {
        "camera": "garden path · morning dew · soft leaf canopy",
        "scroll": "organic float · gentle breathe",
        "cta": "inviting soft buttons · open white space",
        "sound": "birds · soft breeze · clippers distant",
        "illustration": "leaf · hedge · organic line",
        "lighting": "soft dawn through foliage · moss fill",
        "shadow": "dappled soft · lift cards lightly",
    },
    "handwerk": {
        "camera": "workshop bench · tool edge · practical light",
        "scroll": "steady craft pace",
        "cta": "direct buttons · no drama",
        "sound": "workshop · tool set down · focus",
        "illustration": "tool · material · ochre mark",
        "lighting": "warm work lamp · charcoal depth",
        "shadow": "soft deep under tools",
    },
    "psychology": {
        "camera": "still eye-level in a quiet chamber · soft window light",
        "scroll": "very slow breathe · almost no motion",
        "cta": "one calm link · no urgency",
        "sound": "room hush · distant city muted",
        "illustration": "soft chair silhouette · paper · light band",
        "lighting": "morning soft fill · warm paper surfaces",
        "shadow": "barely there · open air",
    },
    "restaurant": {
        "camera": "courtyard evening · table height · candle warmth",
        "scroll": "slow settle into the table",
        "cta": "reservation · warm large",
        "sound": "glasses · low talk · kitchen distant",
        "illustration": "long table · steam · terracotta mark",
        "lighting": "golden evening rim · deep warm fill",
        "shadow": "deep under eaves · soft plate lift",
    },
    "law": {
        "camera": "facade frontal · still · ordered geometry",
        "scroll": "measured · no bounce",
        "cta": "one precise button",
        "sound": "silence · paper · clock distant",
        "illustration": "column · brass line · stone",
        "lighting": "clear daylight · cool stone · brass highlight",
        "shadow": "hard architectural · clean edge",
    },
    "beauty": {
        "camera": "atelier mirror · soft hands · ritual pace",
        "scroll": "soft float · ritual reveal",
        "cta": "termin · calm · clear",
        "sound": "quiet tools · soft music hint",
        "illustration": "mirror arc · product bottle · soft line",
        "lighting": "porcelain daylight · soft rose fill",
        "shadow": "soft lift · no neon glare",
    },
}

_DEFAULT_DIRECTION = {
    "camera": "calm eye-level · clear space",
    "scroll": "steady soft reveals",
    "cta": "clear large buttons · calm spacing",
    "sound": "quiet professional room tone",
    "illustration": "clean geometric mark",
    "lighting": "even daylight · soft fill",
    "shadow": "soft lift",
}


def _fp(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _hex_rgb(hex_color: str) -> tuple[int, int, int]:
    h = (hex_color or "#64748b").lstrip("#")
    if len(h) < 6:
        return (100, 116, 139)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def build_atmosphere_pack(
    book: BrandBook,
    dna: DesignDNA | None = None,
) -> AtmospherePack:
    """Brand Book → living experience recipe (director, not decoration)."""
    niche = book.niche_id
    pid = book.package_id
    direction = dict(_NICHE_DIRECTION.get(niche) or _DEFAULT_DIRECTION)
    name = book.brand_name
    seed_base = f"{name}|{niche}|{pid}|{book.fingerprint}"

    from app.factory.visual_brand_system import invent_visual_brand

    vb = invent_visual_brand(
        brand_name=name,
        niche_id=niche,
        diversity_salt=book.fingerprint,
        city=book.city_hint,
        base_accent=book.palette.accent_hex,
        forbidden=tuple(book.forbidden),
    )
    briefs_list: list[MediaBrief] = [
        MediaBrief(
            role="hero",
            concept=book.hero_concept or book.visual_metaphor,
            must_include=tuple(book.photography[:5]) or tuple(book.scene_language),
            must_forbid=tuple(book.forbidden),
            seed=f"{seed_base}|hero|{vb.fingerprint}",
            size=(1600, 900),
            image_prompt=vb.prompts.get("hero", ""),
        ),
        MediaBrief(
            role="background",
            concept=f"scene · {' · '.join(book.scene_language[:3])}",
            must_include=tuple(book.scene_language) + tuple(book.texture[:2]),
            must_forbid=tuple(book.forbidden),
            seed=f"{seed_base}|bg|{vb.fingerprint}",
            size=(1920, 1080),
            image_prompt=vb.prompts.get("hero_background", ""),
        ),
    ]
    gal_scenes = list(vb.scene_library.get("gallery") or book.photography[2:8] or book.texture)
    # 6–8 unique gallery briefs (each own seed — never clone hero)
    for i, scene in enumerate(gal_scenes[:8] or ["craft detail"]):
        briefs_list.append(
            MediaBrief(
                role="gallery",
                concept=f"gallery proof · {scene}",
                must_include=(scene,) + tuple(book.texture[:2]),
                must_forbid=tuple(book.forbidden),
                seed=f"{seed_base}|gal{i}|{vb.fingerprint}",
                size=(1400, 1000),
                image_prompt=(
                    vb.prompts.get("gallery", "")
                    + f" Specific frame: {scene}."
                ),
            )
        )
    for role_key, concept in (
        ("before_after", "before / after proof"),
        ("team", "team of this company"),
        ("equipment", "tools & equipment of the trade"),
        ("illustration", vb.illustration_pack),
    ):
        scenes = tuple(vb.scene_library.get(role_key, ())[:3]) or tuple(book.scene_language[:2])
        briefs_list.append(
            MediaBrief(
                role=role_key,
                concept=concept,
                must_include=scenes,
                must_forbid=tuple(book.forbidden),
                seed=f"{seed_base}|{role_key}|{vb.fingerprint}",
                size=(1400, 1000) if role_key != "illustration" else (1200, 1200),
                image_prompt=vb.prompts.get(role_key, ""),
            )
        )
    briefs = tuple(briefs_list)

    html = _emit_html(book, direction)
    css = _emit_css(book, direction, dna)
    js = _emit_js(book, direction)

    return AtmospherePack(
        brand_name=name,
        niche_id=niche,
        package_id=pid,
        metaphor=book.visual_metaphor,
        core_emotion=book.core_emotion,
        atmosphere_mode=book.atmosphere_mode,
        scene_language=book.scene_language,
        texture_language=book.texture,
        motion_language=vb.motion_language or book.motion_language,
        camera_feeling=direction["camera"],
        scroll_feeling=direction["scroll"],
        cta_feeling=direction["cta"] + " · " + book.cta_style,
        sound_mood=direction["sound"],
        illustration_style=vb.illustration_pack or direction["illustration"],
        glass_level=book.glass_level,
        shadow_language=direction["shadow"] + " · " + book.shadow_style,
        icon_language=vb.icon_style or book.icon_style,
        lighting=direction["lighting"],
        layers=_LAYERS,
        media_briefs=briefs,
        fingerprint=_fp(book.fingerprint, book.visual_metaphor, book.atmosphere_mode, vb.fingerprint),
        html_nodes=html,
        css_layers=css,
        js_motion=js,
    )


def _emit_html(book: BrandBook, direction: dict[str, str]) -> str:
    pid = book.package_id
    mode = html_lib.escape(book.atmosphere_mode)
    niche = html_lib.escape(book.niche_id)
    metaphor = html_lib.escape(book.visual_metaphor)
    emotion = html_lib.escape(book.core_emotion)
    n = 22 if pid == "basic" else 32 if pid == "business" else 48
    # Rain / dew / dust particles — niche character via class
    particle_cls = {
        "dachreinigung": "atm-drop",
        "zaunbau": "atm-spark",
        "gartenpflege": "atm-pollen",
        "handwerk": "atm-dust",
    }.get(book.niche_id, "atm-mote")
    particles = []
    for i in range(n):
        sx = 2 + ((i * 19) % 94)
        sy = 3 + ((i * 29) % 90)
        dur = 12 + (i % 10) * 1.6
        delay = (i % 13) * -1.1
        size = 2 + (i % 5)
        particles.append(
            f'<span class="dna-atm__particle {particle_cls}" style="--sx:{sx}%;--sy:{sy}%;'
            f'--dur:{dur}s;--delay:{delay}s;--size:{size}px"></span>'
        )
    joined = "\n        ".join(particles)

    webgl_slot = ""
    try:
        from app.factory.creative_direction import recommends_webgl_3d

        if pid in ("premium", "connected") and recommends_webgl_3d(
            book.niche_id, book.package_id
        ):
            webgl_slot = (
                '<div id="virtus-3d-hero" class="virtus-3d-hero" '
                'data-virtus-3d="1" aria-hidden="true"></div>'
            )
    except Exception:
        webgl_slot = ""

    premium = ""
    if pid == "premium":
        premium = f"""
    <!-- Layer 2–5: animated atmosphere · depth · lighting · motion -->
    <div class="dna-atm__sky" data-scene-layer="atmosphere"></div>
    <div class="dna-atm__clouds" data-scene-layer="motion"></div>
    <div class="dna-atm__light" data-scene-layer="depth"></div>
    <div class="dna-atm__glints" data-scene-layer="identity"></div>
    <div class="dna-atm__aurora dna-atm__aurora--c"></div>
    <div class="dna-atm__grid"></div>
    <div class="dna-atm__orb dna-atm__orb--d"></div>
    <div class="dna-atm__illu" aria-hidden="true"></div>
"""
    elif pid == "business":
        premium = """
    <div class="dna-atm__sky" data-scene-layer="atmosphere"></div>
    <div class="dna-atm__light" data-scene-layer="depth"></div>
    <div class="dna-atm__aurora dna-atm__aurora--c"></div>
    <div class="dna-atm__grid dna-atm__grid--soft"></div>
"""

    return f"""
  <!-- Scene Layers directed by Brand Book — identity locked to niche -->
  <div class="dna-atm dna-atm--directed" aria-hidden="true"
       data-dna-atmosphere="1"
       data-atm-mode="{mode}"
       data-atm-tier="{html_lib.escape(pid)}"
       data-atm-niche="{niche}"
       data-atm-metaphor="{metaphor}"
       data-atm-emotion="{emotion}"
       data-scene-layers="content,atmosphere,motion,depth,identity"
       data-camera="{html_lib.escape(direction['camera'][:80])}">
    <div class="dna-atm__base" data-scene-layer="atmosphere"></div>
    <div class="dna-atm__mesh" data-scene-layer="depth"></div>
    <div class="dna-atm__aurora dna-atm__aurora--a"></div>
    <div class="dna-atm__aurora dna-atm__aurora--b"></div>
    {premium}
    <div class="dna-atm__orb dna-atm__orb--a"></div>
    <div class="dna-atm__orb dna-atm__orb--b"></div>
    <div class="dna-atm__orb dna-atm__orb--c"></div>
    <div class="dna-atm__particles" data-scene-layer="motion">
        {joined}
    </div>
    {webgl_slot}
    <div class="dna-atm__vignette" data-scene-layer="depth"></div>
  </div>
"""


def _emit_css(
    book: BrandBook,
    direction: dict[str, str],
    dna: DesignDNA | None,
) -> str:
    ar, ag, ab = _hex_rgb(book.palette.accent_hex)
    ir, ig, ib = _hex_rgb(book.palette.ink_hex)
    hr, hg, hb = _hex_rgb(book.palette.highlight_hex or book.palette.accent_hex)
    radius = max(4, min(24, book.border_radius_px))
    niche = book.niche_id
    pid = book.package_id
    style = (dna.style if dna else book.dna_style) or "modern_clinical"
    glass = {"low": "10px", "medium": "16px", "high": "22px"}.get(book.glass_level, "16px")
    # Motion tempo from Brand Book
    cloud_dur = "48s" if "Langsam" in book.motion_language or pid == "premium" else "36s"
    reveal = "0.9s" if pid == "premium" else "0.7s"
    parallax = "0.08" if pid == "premium" else "0.12"

    # Niche identity underlay — scene media, not café stock
    scene_underlay = f"""
body[data-brand-book][data-niche="{niche}"] .dna-atm__base {{
  background-image:
    linear-gradient(165deg, rgba({ir},{ig},{ib},0.72) 0%, rgba({ar},{ag},{ab},0.28) 42%, rgba({ir},{ig},{ib},0.55) 100%),
    url("assets/background.jpg"),
    url("assets/hero.jpg") !important;
  background-size: cover, cover, cover !important;
  background-position: center !important;
  background-blend-mode: normal, soft-light, multiply;
}}
body[data-brand-book][data-niche="{niche}"] .hero.has-photo,
body[data-brand-book][data-niche="{niche}"] .hero.hero-layout-D.has-photo {{
  background-image:
    linear-gradient(115deg, rgba({ir},{ig},{ib},0.82) 0%, rgba({ir},{ig},{ib},0.35) 40%, rgba({ar},{ag},{ab},0.32) 100%),
    url("assets/hero.jpg") !important;
  background-size: cover !important;
  background-position: center !important;
}}
"""

    # DachKlar: rain glints + sky drift — unique, not salon/SaaS
    niche_fx = ""
    if niche == "dachreinigung":
        niche_fx = f"""
/* Identity Layer — roof / rain / sky (NOT café) */
body[data-niche="dachreinigung"] .dna-atm__sky {{
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse 90% 55% at 50% -5%, rgba({ar},{ag},{ab},0.45), transparent 60%),
    linear-gradient(180deg, rgba(30,58,95,0.35), transparent 55%);
  animation: atmSkyPulse 22s ease-in-out infinite alternate;
}}
body[data-niche="dachreinigung"] .dna-atm__clouds {{
  position: absolute; inset: -10% -20%;
  background:
    radial-gradient(ellipse 28% 18% at 20% 22%, rgba(248,250,252,0.22), transparent 70%),
    radial-gradient(ellipse 32% 16% at 72% 18%, rgba(226,232,240,0.18), transparent 68%),
    radial-gradient(ellipse 24% 14% at 48% 28%, rgba(255,255,255,0.12), transparent 65%);
  animation: atmCloudDrift {cloud_dur} linear infinite;
  filter: blur(2px);
}}
body[data-niche="dachreinigung"] .dna-atm__light {{
  position: absolute; inset: 0;
  background: linear-gradient(125deg, transparent 40%, rgba({hr},{hg},{hb},0.12) 52%, transparent 64%);
  animation: atmLightSweep 14s ease-in-out infinite;
  mix-blend-mode: soft-light;
}}
body[data-niche="dachreinigung"] .dna-atm__glints {{
  position: absolute; inset: 0;
  background-image:
    radial-gradient(circle at 30% 62%, rgba(255,255,255,0.35) 0 1px, transparent 2px),
    radial-gradient(circle at 48% 55%, rgba(255,255,255,0.28) 0 1px, transparent 2px),
    radial-gradient(circle at 62% 68%, rgba(255,255,255,0.32) 0 1px, transparent 2px),
    radial-gradient(circle at 74% 58%, rgba(255,255,255,0.22) 0 1px, transparent 2px);
  background-size: 100% 100%;
  animation: atmGlint 7s ease-in-out infinite;
  opacity: 0.85;
}}
body[data-niche="dachreinigung"] .dna-atm__particle.atm-drop {{
  border-radius: 40% 40% 55% 55%;
  background: rgba(186, 230, 253, 0.85) !important;
  box-shadow: 0 0 6px rgba(125, 211, 252, 0.55);
  animation-name: atmRainFall;
}}
@keyframes atmSkyPulse {{
  0% {{ opacity: 0.7; }} 100% {{ opacity: 1; }}
}}
@keyframes atmCloudDrift {{
  0% {{ transform: translateX(0) translateY(0); }}
  100% {{ transform: translateX(-4%) translateY(1.5%); }}
}}
@keyframes atmLightSweep {{
  0%, 100% {{ opacity: 0.35; transform: translateX(-2%); }}
  50% {{ opacity: 0.75; transform: translateX(2%); }}
}}
@keyframes atmGlint {{
  0%, 100% {{ opacity: 0.4; }}
  50% {{ opacity: 0.95; }}
}}
@keyframes atmRainFall {{
  0% {{ transform: translateY(0) scale(1); opacity: 0.2; }}
  40% {{ opacity: 0.9; }}
  100% {{ transform: translateY(42px) scale(0.7); opacity: 0; }}
}}
"""
    elif niche == "zaunbau":
        niche_fx = f"""
body[data-niche="zaunbau"] .dna-atm__sky {{
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba({hr},{hg},{hb},0.25), transparent 50%);
}}
body[data-niche="zaunbau"] .dna-atm__particle.atm-spark {{
  background: rgba({hr},{hg},{hb},0.8) !important;
}}
"""
    elif niche == "gartenpflege":
        niche_fx = f"""
body[data-niche="gartenpflege"] .dna-atm__sky {{
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 40% 20%, rgba({ar},{ag},{ab},0.35), transparent 55%);
}}
body[data-niche="gartenpflege"] .dna-atm__particle.atm-pollen {{
  background: rgba(190, 242, 100, 0.75) !important;
}}
"""

    css = f"""
/* ===== Atmosphere Pack — Brand Book director (Sprint 2) ===== */
:root {{
  --atm-parallax: {parallax};
  --atm-reveal: {reveal};
  --atm-cloud-dur: {cloud_dur};
  --brand-radius: {radius}px;
  --dna-glass-blur: {glass};
}}
body[data-brand-book] {{
  --card-radius: var(--brand-radius);
  --btn-radius: var(--brand-radius);
}}
/* Section = film scene, not flat block */
body[data-brand-book] .section,
body[data-brand-book] section.reveal {{
  position: relative;
  isolation: isolate;
}}
body[data-brand-book][data-tier="premium"] .section::before {{
  content: "";
  position: absolute; inset: 0; z-index: -1; pointer-events: none;
  background: linear-gradient(180deg, transparent, rgba({ar},{ag},{ab},0.04), transparent);
  opacity: 0.9;
}}
/* Depth + glass from Brand Book */
body[data-brand-book] .svc-card,
body[data-brand-book] .hero-D-panel,
body[data-brand-book] .process-card {{
  backdrop-filter: blur(var(--dna-glass-blur));
  -webkit-backdrop-filter: blur(var(--dna-glass-blur));
  border-radius: var(--brand-radius) !important;
  box-shadow: 0 28px 64px rgba({ir},{ig},{ib},0.35), inset 0 1px 0 rgba(255,255,255,0.12);
  transition: transform 0.55s cubic-bezier(0.16,1,0.3,1), box-shadow 0.55s ease, border-color 0.4s ease;
}}
body[data-brand-book] .svc-card:hover,
body[data-brand-book] .process-card:hover {{
  transform: translateY(-6px);
  box-shadow: 0 36px 80px rgba({ar},{ag},{ab},0.28), inset 0 1px 0 rgba(255,255,255,0.18);
}}
/* CTA feeling — calm, spacious (Brand Book) */
body[data-brand-book] .btn:not(.btn-wa),
body[data-brand-book] .cta-button:not(.btn-wa) {{
  border-radius: var(--brand-radius) !important;
  letter-spacing: 0.04em;
  padding: 1rem 1.75rem !important;
  transition: transform 0.45s cubic-bezier(0.16,1,0.3,1), box-shadow 0.45s ease, filter 0.35s ease;
}}
body[data-brand-book] .btn:not(.btn-wa):hover,
body[data-brand-book] .cta-button:not(.btn-wa):hover {{
  transform: translateY(-3px);
  filter: brightness(1.06);
  box-shadow: 0 16px 40px rgba({ar},{ag},{ab},0.35);
}}
/* Slow reveal — motion language */
body[data-brand-book] .reveal {{
  transition: opacity var(--atm-reveal) ease, transform var(--atm-reveal) cubic-bezier(0.16,1,0.3,1);
}}
body[data-brand-book] .hero-D-panel {{
  animation: atmHeroIn 1.15s cubic-bezier(0.16,1,0.3,1) both;
}}
@keyframes atmHeroIn {{
  from {{ opacity: 0; transform: translateY(28px) scale(0.98); }}
  to {{ opacity: 1; transform: none; }}
}}
/* Parallax depth via --scroll-y */
body[data-brand-book] .dna-atm__clouds,
body[data-brand-book] .dna-atm__mesh {{
  transform: translate3d(0, calc(var(--scroll-y, 0) * var(--atm-parallax) * -1px), 0);
  will-change: transform;
}}
body[data-brand-book] .dna-atm--directed {{
  z-index: -1;
}}
{scene_underlay}
{niche_fx}
@media (prefers-reduced-motion: reduce) {{
  body[data-brand-book] .dna-atm__clouds,
  body[data-brand-book] .dna-atm__sky,
  body[data-brand-book] .dna-atm__light,
  body[data-brand-book] .dna-atm__glints,
  body[data-brand-book] .dna-atm__particle {{
    animation: none !important;
  }}
  body[data-brand-book] .hero-D-panel {{ animation: none !important; }}
}}
/* Atmosphere Pack fingerprint hook for {style} */
body[data-dna-style="{html_lib.escape(style)}"][data-brand-book] {{
  --atm-accent: rgb({ar},{ag},{ab});
}}
"""

    try:
        from app.factory.experience_language import experience_css

        css = css + "\n" + experience_css(book.atmosphere_mode)
    except Exception:
        pass
    return css

def _emit_js(book: BrandBook, direction: dict[str, str]) -> str:
    pid = book.package_id
    soft = "true" if pid == "premium" or "Langsam" in book.motion_language else "false"
    out = f"""
<script data-dna-experience="1" data-atmosphere-pack="1">
(function(){{
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var soft = {soft};
  var bar = document.querySelector('.topbar');
  var root = document.documentElement;
  var onScroll = function(){{
    var y = window.scrollY || 0;
    root.style.setProperty('--scroll-y', String(Math.min(y, 2400)));
    if (bar) {{
      if (y > 18) bar.classList.add('is-scrolled');
      else bar.classList.remove('is-scrolled');
    }}
  }};
  onScroll();
  window.addEventListener('scroll', onScroll, {{passive:true}});
  /* Soft section scene entrances — Brand Book scroll feeling */
  try {{
    var nodes = document.querySelectorAll('.section, .svc-card, .process-card, .faq-item, .account-panel');
    if ('IntersectionObserver' in window) {{
      var io = new IntersectionObserver(function(entries){{
        entries.forEach(function(en){{
          if (en.isIntersecting) {{
            en.target.classList.add('atm-in-scene');
            if (soft) en.target.style.transitionDelay = (Math.random() * 0.12).toFixed(2) + 's';
          }}
        }});
      }}, {{threshold: 0.12, rootMargin: '0px 0px -8% 0px'}});
      nodes.forEach(function(n){{ n.classList.add('atm-scene-ready'); io.observe(n); }});
    }}
  }} catch (e) {{}}
}})();
</script>
<style data-atmosphere-pack-scene="1">
.atm-scene-ready {{ opacity: 0.01; transform: translateY(18px); }}
.atm-scene-ready.atm-in-scene {{ opacity: 1; transform: none; transition: opacity 0.85s ease, transform 0.85s cubic-bezier(0.16,1,0.3,1); }}
</style>
"""

    try:
        from app.factory.experience_language import experience_js

        exp_j = (experience_js() or "").strip()
        # Never append bare JS — clients would see the source as page text.
        if exp_j.startswith("<script"):
            out = out + "\n" + exp_j
    except Exception:
        pass
    try:
        from app.factory.creative_direction import recommends_webgl_3d

        if recommends_webgl_3d(book.niche_id, book.package_id):
            out = out + '\n<script src="assets/scene_3d.js" defer></script>\n'
    except Exception:
        pass
    return out




def apply_media_briefs(
    product_dir,
    pack: AtmospherePack,
    *,
    niche_id: str,
    business_name: str = "",
    package_id: str = "",
) -> list[str]:
    """Write Brand Book-directed niche scenes; prefer Image Provider when configured."""
    from pathlib import Path
    import json

    from app.factory.creative_direction import (
        invent_creative_brief,
        persist_creative_brief,
        recommends_webgl_3d,
    )
    from app.factory.niche_scene_media import write_niche_scene
    from app.factory.visual_brand_system import (
        invent_visual_brand,
        persist_visual_brand,
        try_provider_image,
    )

    root = Path(product_dir)
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    pkg = (package_id or getattr(pack, "package_id", "") or "").strip().lower()
    brand = business_name or pack.brand_name
    creative = invent_creative_brief(
        brand_name=brand,
        niche_id=niche_id,
        package_id=pkg or pack.package_id,
        diversity_salt=pack.fingerprint,
    )
    persist_creative_brief(root, creative)
    written.append(str(root / "CREATIVE_BRIEF.json"))

    vb = invent_visual_brand(
        brand_name=brand,
        niche_id=niche_id,
        diversity_salt=pack.fingerprint,
        forbidden=tuple(
            next((b.must_forbid for b in pack.media_briefs if b.must_forbid), ())
        ),
    )
    persist_visual_brand(root, vb)
    css_path = assets / "visual_brand.css"
    from app.factory.visual_brand_system import css_variables

    css_path.write_text(css_variables(vb), encoding="utf-8")
    written.append(str(css_path))

    role_file: dict[str, tuple[str, str]] = {
        "hero": ("hero.jpg", "hero"),
        "background": ("background.jpg", "banner"),
        "illustration": ("illustration.jpg", "gallery"),
        "team": ("team.jpg", "gallery"),
        "equipment": ("equipment.jpg", "gallery"),
        "before_after": ("before_after.jpg", "gallery"),
    }
    gal_i = 0
    for brief in pack.media_briefs:
        if brief.role == "gallery":
            fname = f"gallery_{gal_i + 1}.jpg" if gal_i else "gallery.jpg"
            role = "gallery"
            gal_i += 1
        else:
            mapped = role_file.get(brief.role)
            if not mapped:
                continue
            fname, role = mapped
        dest = assets / fname
        brief_prompt = brief.to_image_prompt(brand_name=brand, niche_id=niche_id)
        creative_prompt = creative.to_image_prompt(brand_name=brand, niche_id=niche_id)
        if brief.role == "hero":
            prompt = creative_prompt
            if brief_prompt and brief_prompt not in prompt:
                prompt = f"{creative_prompt} {brief_prompt}"
        else:
            prompt = (
                f"{brief_prompt} | {creative_prompt}" if creative_prompt else brief_prompt
            )
        used_provider = try_provider_image(prompt, dest, size=tuple(brief.size))
        if not used_provider:
            write_niche_scene(
                dest,
                niche_id=niche_id,
                seed=brief.seed or f"{business_name}|{brief.role}|{gal_i}",
                role=role,  # type: ignore[arg-type]
                size=tuple(brief.size),  # type: ignore[arg-type]
                metaphor=pack.metaphor + " — " + (brief.concept or ""),
                accent_hex=vb.color.accent,
                label=(brief.must_include[0] if brief.must_include else brief.role)[:48],
            )
        written.append(str(dest))

    pack_dir = assets / "hero_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    for name, seed_tag, role in (
        ("hero.jpg", "pack-hero", "hero"),
        ("hero_2.jpg", "pack-hero2", "banner"),
        ("gallery.jpg", "pack-gal", "gallery"),
        ("bg.jpg", "pack-bg", "banner"),
    ):
        dest = pack_dir / name
        prompt = vb.prompts.get("hero" if "hero" in seed_tag else "gallery", "")
        if not try_provider_image(prompt, dest, size=(1600, 900)):
            write_niche_scene(
                dest,
                niche_id=niche_id,
                seed=f"{pack.fingerprint}|{seed_tag}|{vb.fingerprint}",
                role=role,  # type: ignore[arg-type]
                size=(1600, 900),
                metaphor=pack.metaphor,
                accent_hex=vb.color.accent,
            )
        written.append(str(dest))

    if pkg in ("premium", "connected"):
        from app.factory.visual_brand_system import (
            last_image_provider,
            resolve_image_provider,
        )

        resolved = resolve_image_provider()
        used = last_image_provider()
        provider_id = str(used.get("provider") or resolved.get("provider") or "studio_offline")
        provider_label = str(
            used.get("label") or resolved.get("label") or "Studio Offline Media"
        )
        offline = provider_id == "studio_offline" or not bool(resolved.get("remote"))
        note = {
            "status": "studio_offline_media" if offline else "provider_media",
            "message": (
                f"{provider_label} — media chain auto-selected"
                + (" (3D/experience still on)" if offline else "")
            ),
            "provider": provider_id,
            "provider_label": provider_label,
            "provider_connected": not offline,
            "studio_offline_media": offline,
            "chain": resolved.get("chain") or [],
            "webgl_3d": bool(
                getattr(creative, "recommends_webgl", False)
                or recommends_webgl_3d(niche_id, pkg)
            ),
            "experience_on": True,
        }
        note_path = root / "PREMIUM_MEDIA_NOTE.json"
        note_path.write_text(
            json.dumps(note, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written.append(str(note_path))
        txt_path = assets / "premium_media_note.txt"
        txt_path.write_text(f"{note['message']}\n", encoding="utf-8")
        written.append(str(txt_path))

    want_3d = bool(
        getattr(creative, "recommends_webgl", False)
        or recommends_webgl_3d(niche_id, pkg)
    )
    if want_3d:
        try:
            from app.factory.scene_3d_engine import (
                write_hero_3d_snippet,
                write_scene_assets,
            )

            accent = getattr(getattr(vb, "color", None), "accent", None) or "#3b82f6"
            written.extend(
                write_scene_assets(
                    root, niche_id=niche_id, accent=accent, brand_name=brand
                )
            )
            snip = write_hero_3d_snippet(
                root, niche_id=niche_id, accent=accent, brand_name=brand
            )
            written.append(str(snip))
        except Exception:
            pass

    if pkg in ("premium", "connected"):
        try:
            from app.factory.studio_renderer_v2 import write_studio_assets

            written.extend(
                write_studio_assets(
                    root,
                    niche_id=niche_id,
                    package_id=pkg,
                    business_name=brand,
                    metaphor=str(getattr(creative, "visual_metaphor", "") or ""),
                    accent_hex=getattr(getattr(vb, "color", None), "accent", None),
                )
            )
        except Exception:
            pass

    return written



__all__ = [
    "AtmospherePack",
    "MediaBrief",
    "apply_media_briefs",
    "build_atmosphere_pack",
]
