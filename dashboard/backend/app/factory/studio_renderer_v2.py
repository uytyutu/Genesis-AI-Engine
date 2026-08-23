"""Studio Renderer 2.0 — Digital Experience layer for Premium Factory sites.

Not \"add 3D\". Full business presentation: media coverage, niche-fit WebGL,
studio motion. 3D amplifies when it sells; otherwise cinematic image + motion.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

HeroMedia = Literal["image", "video", "webgl"]
BgKind = Literal["image", "illustration", "webgl", "gradient_art", "particles"]

# Premium experience rhythm (eyes, not page templates)
EXPERIENCE_FLOW: tuple[str, ...] = (
    "hero",
    "story",
    "photo_band",
    "interactive_cards",
    "gallery",
    "video",
    "team",
    "process",
    "contact",
)

# Heavy WebGL ONLY when it answers: "Why does this help sell?"
# Mapping: niche → sell reason (empty → forbidden)
_WEBGL_SELL_REASONS: dict[str, str] = {
    "auto": "Customer sees the car on a lift — trust in workshop craft before booking.",
    "car_dealership": "Showroom car + light + reflection sells the handover fantasy.",
    "detailing": "Mirror gloss under studio light sells the finish quality.",
    "auto_detailing": "Mirror gloss under studio light sells the finish quality.",
    "energy": "Panels catching sky make the energy product tangible.",
    "solar": "Panels catching sky make the energy product tangible.",
    "architecture": "Building volume + camera fly sells space before a visit.",
    "immobilien": "Building volume helps buyers feel the property scale.",
    "furniture": "Calm living volumes sell the piece in a room, not as a SKU photo.",
    "jewelry": "Light on the ring sells precious material better than flat photos.",
}

# Never heavy WebGL — cinematic stills + soft motion
_WEBGL_FORBID = frozenset(
    {
        "psychology",
        "family_psychology",
        "therapie",
        "coaching",
        "beratung",
    }
)

# Decorative glass / float only — no spinning product gimmicks
_WEBGL_SOFT = frozenset(
    {
        "nail",
        "nail_studio",
        "beauty",
        "kosmetik",
        "spa",
        "massage",
    }
)

# Unique gallery stories per niche — uniqueness > count
_GALLERY_STORIES: dict[str, tuple[str, ...]] = {
    "car_dealership": (
        "evening showroom with polished floor reflection",
        "wet asphalt and headlights at dusk",
        "key handover close-up on leather",
        "workshop bay with lift and tools",
        "chrome grille and headlight detail",
        "family beside vehicle outside dealership",
        "service advisor at reception desk",
        "cabin interior steering wheel light",
        "EV charging column at night",
        "clean paperwork and digital tablet",
        "advisor team portrait in showroom",
        "facade of Autohaus at blue hour",
    ),
    "auto": (
        "car on hydraulic lift",
        "mechanic hands with torque wrench",
        "diagnostic screen glow",
        "engine bay clean detail",
        "waiting lounge coffee",
        "tyre and brake close-up",
        "oil change bay",
        "finished car washed exterior",
        "parts shelf organized",
        "before after dent detail",
        "team in workwear",
        "shop front dusk",
    ),
    "beauty": (
        "hero cinematic manicure warm lamp space for headline",
        "reception desk soft champagne light",
        "manicure hands gel polish close-up",
        "pedicure spa bowl rose petals",
        "eyebrow shaping at vanity mirror",
        "lash extension detail professional",
        "massage room linen candles oil",
        "cosmetics bottles shelf branded glass",
        "nail workstation tools organized",
        "beauty team portrait warm studio",
        "certificates framed on blush wall",
        "happy client after manicure smile",
        "salon interior wide soft daylight",
        "professional products display table",
        "process applying cuticle oil",
        "before after brows soft comparison",
        "waiting lounge velvet chair flowers",
        "detail rose quartz and glass bottle",
    ),
    "nail_studio": (
        "hero cinematic manicure warm lamp space for headline",
        "reception desk soft champagne light",
        "manicure hands gel polish close-up",
        "pedicure spa bowl rose petals",
        "eyebrow shaping at vanity mirror",
        "lash extension detail professional",
        "massage room linen candles oil",
        "cosmetics bottles shelf branded glass",
        "nail workstation tools organized",
        "beauty team portrait warm studio",
        "certificates framed on blush wall",
        "happy client after manicure smile",
        "salon interior wide soft daylight",
        "professional products display table",
        "process applying cuticle oil",
        "before after brows soft comparison",
        "waiting lounge velvet chair flowers",
        "detail rose quartz and glass bottle",
    ),
}

def gallery_story_for(niche_id: str | None, index: int) -> str:
    """1-based gallery index → unique story label for that niche."""
    niche = _norm_niche(niche_id)
    stories = _GALLERY_STORIES.get(niche)
    if not stories and any(x in niche for x in ("nail", "beauty", "spa")):
        stories = _GALLERY_STORIES.get("beauty")
    if not stories:
        return f"scene {index} for {niche}"
    return stories[(max(1, index) - 1) % len(stories)]


# Section media plate filenames (Premium)
_SECTION_PLATES = (
    ("section_story.jpg", "banner"),
    ("section_services.jpg", "banner"),
    ("section_team.jpg", "banner"),
    ("section_process.jpg", "banner"),
    ("section_contact.jpg", "banner"),
    ("team.jpg", "gallery"),
    ("process.jpg", "gallery"),
    ("before.jpg", "gallery"),
    ("after.jpg", "gallery"),
    ("equipment.jpg", "product"),
    ("illustration_1.jpg", "product"),
    ("illustration_2.jpg", "product"),
    ("illustration_3.jpg", "product"),
)


@dataclass(frozen=True)
class StudioWebGLDecision:
    enabled: bool
    mode: Literal["amplify", "soft", "cinematic", "off"]
    reason: str
    hero_media: HeroMedia
    sell_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StudioExperiencePlan:
    package_id: str
    niche_id: str
    flow: tuple[str, ...]
    webgl: StudioWebGLDecision
    gallery_min: int
    media_slots: tuple[str, ...]
    motion: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["director"] = "studio_renderer_v2"
        d["webgl"] = self.webgl.as_dict()
        return d


def _norm_niche(niche_id: str | None) -> str:
    return (niche_id or "generic").strip().lower().replace("-", "_")


def decide_webgl(niche_id: str | None, package_id: str | None = None) -> StudioWebGLDecision:
    """3D only if it answers: why does this help sell? Otherwise forbidden."""
    niche = _norm_niche(niche_id)
    pkg = (package_id or "").strip().lower()
    if pkg in ("basic", "business", "standalone"):
        return StudioWebGLDecision(
            False, "off", "tier_below_premium", "image", sell_reason=""
        )
    if niche in _WEBGL_FORBID or any(n in niche for n in ("psych", "therap", "coach")):
        return StudioWebGLDecision(
            False,
            "cinematic",
            "no_sell_reason_psychology",
            "image",
            sell_reason="",
        )
    if niche in _WEBGL_SOFT or any(n in niche for n in ("nail", "beauty", "spa", "kosmetik")):
        sell = (
            "Light glass / float motion supports calm premium atmosphere — "
            "not a spinning polish bottle gimmick."
        )
        return StudioWebGLDecision(
            True,
            "soft",
            "soft_atmosphere_only",
            "webgl",
            sell_reason=sell,
        )
    sell = _WEBGL_SELL_REASONS.get(niche, "")
    if not sell and niche.startswith("auto"):
        sell = _WEBGL_SELL_REASONS["auto"]
    if not sell and "solar" in niche:
        sell = _WEBGL_SELL_REASONS["solar"]
    if sell:
        return StudioWebGLDecision(
            True,
            "amplify",
            "sells_the_offer",
            "webgl",
            sell_reason=sell,
        )
    return StudioWebGLDecision(
        False,
        "cinematic",
        "no_sell_reason",
        "image",
        sell_reason="",
    )


def premium_media_slot_names(*, package_id: str = "premium") -> tuple[str, ...]:
    """Mandatory media filenames for Premium digital presentation."""
    pkg = (package_id or "").strip().lower()
    base = ["hero.jpg", "background.jpg", "illustration.jpg", "gallery.jpg"]
    if pkg not in ("premium", "connected"):
        return tuple(base + [f"gallery_{i}.jpg" for i in range(1, 4)])
    gallery = [f"gallery_{i}.jpg" for i in range(1, 19)]
    sections = [name for name, _ in _SECTION_PLATES]
    return tuple(base + gallery + sections)


def plan_studio_experience(
    *,
    niche_id: str,
    package_id: str = "premium",
) -> StudioExperiencePlan:
    pkg = (package_id or "premium").strip().lower()
    webgl = decide_webgl(niche_id, pkg)
    gallery_min = 18 if pkg in ("premium", "connected") else 3
    motion = (
        ("lenis", "gsap_scroll", "magnetic", "mouse_light", "glass", "reveal")
        if pkg in ("premium", "connected")
        else ("reveal", "magnetic")
    )
    if webgl.enabled and webgl.mode == "amplify":
        motion = motion + ("webgl_scroll_camera",)
    if webgl.enabled and webgl.mode == "soft":
        motion = motion + ("soft_glass_float",)
    return StudioExperiencePlan(
        package_id=pkg,
        niche_id=_norm_niche(niche_id),
        flow=EXPERIENCE_FLOW,
        webgl=webgl,
        gallery_min=gallery_min,
        media_slots=premium_media_slot_names(package_id=pkg),
        motion=motion,
    )


def ensure_studio_media_floor(
    assets_dir: Path,
    *,
    niche_id: str,
    business_name: str = "",
    package_id: str = "premium",
    metaphor: str = "",
    accent_hex: str | None = None,
) -> list[str]:
    """Write all Premium media slots via niche scene plates (fill gaps only if missing)."""
    from app.factory.niche_scene_media import write_niche_scene

    pkg = (package_id or "premium").strip().lower()
    if pkg not in ("premium", "connected"):
        return []

    assets_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    role_map = {
        "hero.jpg": ("hero", (1600, 900)),
        "background.jpg": ("banner", (1920, 1080)),
        "illustration.jpg": ("product", (1000, 1000)),
        "gallery.jpg": ("gallery", (1200, 800)),
    }
    for i in range(1, 19):
        role_map[f"gallery_{i}.jpg"] = ("gallery", (1200, 800))
    for name, role in _SECTION_PLATES:
        size = (1400, 900) if role == "banner" else (1200, 800)
        role_map[name] = (role, size)

    for name, (role, size) in role_map.items():
        dest = assets_dir / name
        if dest.is_file() and dest.stat().st_size >= 4_000:
            continue
        slot_metaphor = metaphor
        if name.startswith("gallery_") and name[8:-4].isdigit():
            slot_metaphor = gallery_story_for(niche_id, int(name[8:-4]))
        write_niche_scene(
            dest,
            niche_id=niche_id,
            seed=f"studio-v2|{name}|{business_name}|{pkg}|{slot_metaphor}",
            role=role,  # type: ignore[arg-type]
            size=size,
            metaphor=slot_metaphor or metaphor,
            accent_hex=accent_hex,
        )
        written.append(name)
    return written


def studio_section_media_css(assets_dir: Path | None = None) -> str:
    """CSS: every major band gets a photographic plate — no empty gray slabs."""

    def _url(name: str) -> str:
        if assets_dir is not None and (assets_dir / name).is_file():
            return f"url('assets/{name}')"
        # Prefer section plate; fall back to background / gallery rhythm
        return f"url('assets/{name}')"

    return f"""/* Virtus Core Studio Renderer 2.0 — section media */
html.studio-v2 {{
  scroll-behavior: auto;
}}
.studio-v2 body {{
  background: #0a0a0b;
}}
.studio-band {{
  position: relative;
  isolation: isolate;
  overflow: hidden;
}}
.studio-band::before {{
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  background-image: var(--studio-bg, {_url('background.jpg')});
  background-size: cover;
  background-position: center;
  opacity: var(--studio-bg-opacity, 0.22);
  transform: scale(1.04);
  pointer-events: none;
}}
.studio-band > * {{
  position: relative;
  z-index: 1;
}}
.studio-band--story {{ --studio-bg: {_url('section_story.jpg')}; --studio-bg-opacity: 0.28; }}
.studio-band--services {{ --studio-bg: {_url('section_services.jpg')}; --studio-bg-opacity: 0.18; }}
.studio-band--gallery {{ --studio-bg: {_url('background.jpg')}; --studio-bg-opacity: 0.12; }}
.studio-band--team {{ --studio-bg: {_url('section_team.jpg')}; --studio-bg-opacity: 0.26; }}
.studio-band--process {{ --studio-bg: {_url('section_process.jpg')}; --studio-bg-opacity: 0.2; }}
.studio-band--contact {{ --studio-bg: {_url('section_contact.jpg')}; --studio-bg-opacity: 0.3; }}
.studio-band--reviews {{ --studio-bg: {_url('gallery_8.jpg')}; --studio-bg-opacity: 0.16; }}
.studio-mouse-light {{
  position: fixed;
  width: 42vmax;
  height: 42vmax;
  margin: -21vmax 0 0 -21vmax;
  border-radius: 50%;
  pointer-events: none;
  z-index: 3;
  background: radial-gradient(circle, color-mix(in srgb, var(--acc, #c5a572) 22%, transparent) 0%, transparent 68%);
  opacity: 0.55;
  mix-blend-mode: soft-light;
  transition: opacity .35s ease;
}}
.studio-gallery-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 220px), 1fr));
  gap: 0.75rem;
}}
.studio-gallery-grid img {{
  width: 100%;
  aspect-ratio: 4/3;
  object-fit: cover;
  border-radius: 10px;
  display: block;
}}
@media (prefers-reduced-motion: reduce) {{
  .studio-mouse-light {{ display: none !important; }}
}}
"""


def studio_cdn_tags() -> str:
    """Lenis + GSAP from CDN (static HTML export — not React)."""
    return """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lenis@1.1.18/dist/lenis.css">
<script src="https://cdn.jsdelivr.net/npm/lenis@1.1.18/dist/lenis.min.js" defer></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js" defer></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js" defer></script>
"""


def studio_experience_js() -> str:
    """Lenis smooth scroll + GSAP reveals + mouse light (respects reduced motion)."""
    return r"""/* Virtus Core Studio Renderer 2.0 */
(function () {
  document.documentElement.classList.add('studio-v2');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function markBands() {
    var map = [
      ['#about', 'studio-band--story'],
      ['.about', 'studio-band--story'],
      ['#services', 'studio-band--services'],
      ['.services', 'studio-band--services'],
      ['#gallery', 'studio-band--gallery'],
      ['.gallery', 'studio-band--gallery'],
      ['#team', 'studio-band--team'],
      ['.team', 'studio-band--team'],
      ['#process', 'studio-band--process'],
      ['.process', 'studio-band--process'],
      ['#contact', 'studio-band--contact'],
      ['.contact', 'studio-band--contact'],
      ['#reviews', 'studio-band--reviews'],
      ['.reviews', 'studio-band--reviews'],
      ['.testimonials', 'studio-band--reviews']
    ];
    map.forEach(function (pair) {
      document.querySelectorAll(pair[0]).forEach(function (el) {
        if (el.tagName === 'SECTION' || el.classList.contains('section') || el.id) {
          el.classList.add('studio-band', pair[1]);
        }
      });
    });
    document.querySelectorAll('section').forEach(function (sec) {
      if (!sec.classList.contains('hero') && !sec.classList.contains('studio-band')) {
        sec.classList.add('studio-band');
      }
    });
  }

  function mouseLight() {
    if (reduce || !(window.matchMedia && window.matchMedia('(pointer: fine)').matches)) return;
    var el = document.createElement('div');
    el.className = 'studio-mouse-light';
    el.setAttribute('aria-hidden', 'true');
    document.body.appendChild(el);
    window.addEventListener('pointermove', function (e) {
      el.style.transform = 'translate3d(' + e.clientX + 'px,' + e.clientY + 'px,0)';
    }, { passive: true });
  }

  function bootLenisGsap() {
    if (reduce) return;
    var LenisCtor = window.Lenis;
    var gsap = window.gsap;
    var ScrollTrigger = window.ScrollTrigger;
    if (LenisCtor) {
      var lenis = new LenisCtor({ lerp: 0.09, smoothWheel: true });
      function raf(t) { lenis.raf(t); requestAnimationFrame(raf); }
      requestAnimationFrame(raf);
      if (gsap && ScrollTrigger) {
        gsap.registerPlugin(ScrollTrigger);
        lenis.on('scroll', ScrollTrigger.update);
      }
    }
    if (gsap && ScrollTrigger) {
      gsap.registerPlugin(ScrollTrigger);
      gsap.utils.toArray('.studio-band, .svc-card, .exp-reveal, .gallery img, .studio-gallery-grid img').forEach(function (node) {
        gsap.fromTo(node, { autoAlpha: 0, y: 28 }, {
          autoAlpha: 1, y: 0, duration: 0.85, ease: 'power2.out',
          scrollTrigger: { trigger: node, start: 'top 88%', toggleActions: 'play none none none' }
        });
      });
      var hero3d = document.getElementById('virtus-3d-hero');
      if (hero3d) {
        gsap.to(hero3d, {
          yPercent: 12, ease: 'none',
          scrollTrigger: { trigger: hero3d, start: 'top top', end: 'bottom top', scrub: true }
        });
      }
    }
  }

  function expandGallery() {
    var host = document.querySelector('#gallery .gallery-grid, #gallery .grid, .gallery-grid, [data-studio-gallery]');
    if (!host) return;
    var existing = host.querySelectorAll('img').length;
    if (existing >= 8) return;
    host.classList.add('studio-gallery-grid');
    for (var i = existing + 1; i <= 18; i++) {
      var img = document.createElement('img');
      img.src = 'assets/gallery_' + i + '.jpg';
      img.alt = 'Galerie ' + i;
      img.loading = 'lazy';
      img.onerror = function () { this.remove(); };
      host.appendChild(img);
    }
  }

  function boot() {
    markBands();
    mouseLight();
    expandGallery();
    bootLenisGsap();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
  window.addEventListener('load', function () { setTimeout(bootLenisGsap, 80); });
})();
"""


def write_studio_plan(product_dir: Path | str, plan: StudioExperiencePlan) -> Path:
    root = Path(product_dir)
    out = root / "STUDIO_EXPERIENCE_V2.json"
    out.write_text(json.dumps(plan.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def write_studio_assets(
    product_dir: Path | str,
    *,
    niche_id: str,
    package_id: str = "premium",
    business_name: str = "",
    metaphor: str = "",
    accent_hex: str | None = None,
) -> list[str]:
    """Write plan + CSS/JS + fill Premium media floor."""
    root = Path(product_dir)
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    plan = plan_studio_experience(niche_id=niche_id, package_id=package_id)
    written: list[str] = []

    write_studio_plan(root, plan)
    written.append("STUDIO_EXPERIENCE_V2.json")

    css_path = assets / "studio_v2.css"
    css_path.write_text(studio_section_media_css(assets), encoding="utf-8")
    written.append("assets/studio_v2.css")

    js_path = assets / "studio_v2.js"
    js_path.write_text(studio_experience_js(), encoding="utf-8")
    written.append("assets/studio_v2.js")

    filled = ensure_studio_media_floor(
        assets,
        niche_id=niche_id,
        business_name=business_name,
        package_id=package_id,
        metaphor=metaphor,
        accent_hex=accent_hex,
    )
    written.extend(f"assets/{n}" for n in filled)
    return written


def studio_head_inject() -> str:
    return (
        studio_cdn_tags()
        + '\n<link rel="stylesheet" href="assets/studio_v2.css">\n'
    )


def studio_body_scripts() -> str:
    return '\n<script src="assets/studio_v2.js" defer></script>\n'


def inject_studio_html(html: str, *, package_id: str = "premium") -> str:
    """Inject CDN + studio CSS/JS into exported HTML when missing."""
    pkg = (package_id or "").strip().lower()
    if pkg not in ("premium", "connected"):
        return html
    if "studio_v2.css" in html and "studio_v2.js" in html:
        return html
    out = html
    head = studio_head_inject()
    if "</head>" in out and "studio_v2.css" not in out:
        out = out.replace("</head>", head + "</head>", 1)
    scripts = studio_body_scripts()
    if "</body>" in out and "studio_v2.js" not in out:
        out = out.replace("</body>", scripts + "</body>", 1)
    return out


__all__ = [
    "EXPERIENCE_FLOW",
    "StudioExperiencePlan",
    "StudioWebGLDecision",
    "decide_webgl",
    "ensure_studio_media_floor",
    "inject_studio_html",
    "plan_studio_experience",
    "premium_media_slot_names",
    "studio_body_scripts",
    "studio_cdn_tags",
    "studio_experience_js",
    "studio_head_inject",
    "studio_section_media_css",
    "write_studio_assets",
    "write_studio_plan",
]
