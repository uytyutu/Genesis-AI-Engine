"""Goal B — Digital Experience quality floor.

Living atmosphere (niche palette, not Virtus purple clone) + section rhythm
paint + micro-interactions. Hard layout safety: never clip off-screen.
"""

from __future__ import annotations

from app.factory.design_dna.dna import DesignDNA, Treatment
from app.factory.design_dna.rhythm import validate_no_light_ladder


def atmosphere_html(dna: DesignDNA) -> str:
    """Fixed living background — Virtus-grade depth, niche palette (never purple clone)."""
    pid = dna.package_id
    n = 18 if pid == "basic" else 28 if pid == "business" else 40
    particles = []
    for i in range(n):
        sx = 3 + ((i * 17) % 92)
        sy = 4 + ((i * 23) % 88)
        dur = 10 + (i % 9) * 1.4
        delay = (i % 11) * -1.0
        size = 2 + (i % 4)
        particles.append(
            f'<span class="dna-atm__particle" style="--sx:{sx}%;--sy:{sy}%;'
            f'--dur:{dur}s;--delay:{delay}s;--size:{size}px"></span>'
        )
    joined = "\n        ".join(particles)
    mode = _atm_mode(dna)
    # Premium: extra layers (grid + aurora-c + orb-d + soft illustration) — Virtus depth, niche hue
    premium_layers = ""
    if pid == "premium":
        premium_layers = """
    <div class="dna-atm__aurora dna-atm__aurora--c"></div>
    <div class="dna-atm__grid"></div>
    <div class="dna-atm__orb dna-atm__orb--d"></div>
    <div class="dna-atm__illu" aria-hidden="true"></div>
"""
    elif pid == "business":
        premium_layers = """
    <div class="dna-atm__aurora dna-atm__aurora--c"></div>
    <div class="dna-atm__grid dna-atm__grid--soft"></div>
"""
    return f"""
  <div class="dna-atm" aria-hidden="true" data-dna-atmosphere="1" data-atm-mode="{mode}" data-atm-tier="{pid}">
    <div class="dna-atm__base"></div>
    <div class="dna-atm__mesh"></div>
    <div class="dna-atm__aurora dna-atm__aurora--a"></div>
    <div class="dna-atm__aurora dna-atm__aurora--b"></div>
    {premium_layers}
    <div class="dna-atm__orb dna-atm__orb--a"></div>
    <div class="dna-atm__orb dna-atm__orb--b"></div>
    <div class="dna-atm__orb dna-atm__orb--c"></div>
    <div class="dna-atm__particles">
        {joined}
    </div>
    <div class="dna-atm__vignette"></div>
  </div>
"""


def experience_js(dna: DesignDNA) -> str:
    """Sticky glass nav + soft scroll depth — lives with the page, not just the hero."""
    return f"""
<script data-dna-experience="1">
(function(){{
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var bar = document.querySelector('.topbar');
  var onScroll = function(){{
    var y = window.scrollY || 0;
    if (bar) bar.classList.toggle('is-scrolled', y > 24);
    document.documentElement.style.setProperty('--scroll-y', Math.min(y, 800) + 'px');
  }};
  onScroll();
  window.addEventListener('scroll', onScroll, {{passive:true}});
}})();
</script>
"""


def quality_floor_css(dna: DesignDNA) -> str:
    """Digital Experience CSS — niche living canvas + scene rhythm + interactions."""
    pid = dna.package_id
    accent = dna.accent_hex
    surface = dna.surface_hex
    ink = dna.ink_hex
    ar, ag, ab = _hex_rgb(accent)
    sr, sg, sb = _hex_rgb(surface)
    ir, ig, ib = _hex_rgb(ink)
    mode = _atm_mode(dna)
    glass_blur = {"low": "10px", "medium": "16px", "high": "22px"}.get(dna.glass, "14px")
    hero_min = {"basic": "86vh", "business": "94vh", "premium": "100vh"}.get(pid, "90vh")
    dark = mode in ("cinematic", "dusk", "velvet")
    treat_css = _treatment_css(dna, dark=dark)
    radius = max(4, min(24, int(getattr(dna, "border_radius_px", 12) or 12)))
    brand_tokens = f"""
/* Brand Book tokens (from DesignDNA) */
:root {{
  --brand-accent: {accent};
  --brand-surface: {surface};
  --brand-ink: {ink};
  --brand-radius: {radius}px;
}}
body[data-brand-book] {{
  --card-radius: var(--brand-radius);
  --btn-radius: var(--brand-radius);
}}
"""

    # Canvas: niche-colored atmosphere (not only black, never flat white paper)
    if mode == "cinematic":
        body_bg = f"rgb({max(8,ir//8)},{max(8,ig//8)},{max(10,ib//7)})"
    elif mode == "dusk":
        body_bg = f"rgb({max(18, ar//3)},{max(12, ag//4)},{max(8, ab//5)})"
    elif mode == "velvet":
        body_bg = f"rgb({max(16, ar//2)},{max(10, ag//5)},{max(18, ab//3)})"
    elif mode == "mist":
        body_bg = f"rgb({min(230, sr)},{min(232, sg)},{min(226, sb)})"
    elif mode == "atelier":
        body_bg = f"rgb({min(245, max(sr, 220))},{min(240, max(sg, 210))},{min(230, max(sb, 195))})"
    else:
        body_bg = f"rgb({sr},{sg},{sb})"
    text = "#fafaf9" if dark else ink
    muted = "rgba(250,250,249,0.9)" if dark else f"rgba({ir},{ig},{ib},0.82)"
    blend = "multiply" if not dark else "screen"
    particle = (
        f"rgba({ar},{ag},{ab},0.55)" if not dark else "rgba(255,255,255,0.9)"
    )
    # Atmosphere opacity: Business/Starter get Premium-grade depth (Owner request)
    atm_opacity = "0.96" if pid == "premium" else "0.92" if pid == "business" else "0.88"
    craft = (dna.niche_id or "").lower() in (
        "dachreinigung",
        "zaunbau",
        "gartenpflege",
        "handwerk",
        "cleaning",
        "green",
    )
    # Illustrated craft canvas — photo/scene behind content (never flat white)
    craft_bg_css = ""
    if craft:
        craft_bg_css = f"""
body[data-dna-style="{dna.style}"] .dna-atm__base {{
  background:
    linear-gradient(165deg, rgba(12,10,8,0.72) 0%, rgba(18,14,10,0.55) 45%, rgba(12,10,8,0.78) 100%),
    url("assets/background.jpg"),
    url("assets/hero.jpg"),
    linear-gradient(165deg, {body_bg}, color-mix(in srgb, {accent} 12%, {body_bg})) !important;
  background-size: cover, cover, cover, auto !important;
  background-position: center !important;
}}
body[data-dna-style="{dna.style}"] .section,
body[data-dna-style="{dna.style}"] .service-card,
body[data-dna-style="{dna.style}"] .svc-card,
body[data-dna-style="{dna.style}"] .testimonial-card,
body[data-dna-style="{dna.style}"] .faq-item,
body[data-dna-style="{dna.style}"] .account-panel {{
  background: rgba(18,14,12,0.72) !important;
  color: #fafaf9 !important;
  border-color: rgba({ar},{ag},{ab},0.28) !important;
  backdrop-filter: blur(12px);
}}
body[data-dna-style="{dna.style}"] .section h2,
body[data-dna-style="{dna.style}"] .service-card h3,
body[data-dna-style="{dna.style}"] .svc-card h3,
body[data-dna-style="{dna.style}"] p,
body[data-dna-style="{dna.style}"] li,
body[data-dna-style="{dna.style}"] .muted,
body[data-dna-style="{dna.style}"] .service-desc {{
  color: #fafaf9 !important;
}}
body[data-dna-style="{dna.style}"] .muted,
body[data-dna-style="{dna.style}"] .service-desc {{
  color: rgba(250,250,249,0.88) !important;
}}
body[data-dna-style="{dna.style}"] .about,
body[data-dna-style="{dna.style}"] .testimonials,
body[data-dna-style="{dna.style}"] .calculator {{
  background: rgba(12,10,8,0.55) !important;
}}
"""

    return brand_tokens + f"""
/* Goal B · Digital Experience · {dna.style} · {mode} */
html {{ overflow-x: clip; scroll-behavior: smooth; }}
body[data-dna-style="{dna.style}"] {{
  --dna-accent: {accent};
  --dna-surface: {surface};
  --dna-ink: {ink};
  --dna-ar: {ar}; --dna-ag: {ag}; --dna-ab: {ab};
  --dna-glass-blur: {glass_blur};
  --dna-content: 72rem;
  --ink: {text};
  --muted: {muted};
  color: {text};
  background: {body_bg} !important;
  min-height: 100vh;
  overflow-x: clip;
  position: relative;
  font-weight: 500;
  letter-spacing: 0.005em;
}}
body[data-dna-style="{dna.style}"] h1,
body[data-dna-style="{dna.style}"] h2,
body[data-dna-style="{dna.style}"] .brand-word,
body[data-dna-style="{dna.style}"] .logo-fallback {{
  font-weight: 700;
  letter-spacing: -0.02em;
}}
body[data-dna-style="{dna.style}"] p,
body[data-dna-style="{dna.style}"] li,
body[data-dna-style="{dna.style}"] .lead {{
  font-weight: 500;
  line-height: 1.65;
}}
body[data-dna-style="{dna.style}"] .brand-lockup {{
  display: inline-flex; align-items: center; gap: 0.55rem; text-decoration: none;
  color: inherit; max-width: min(16rem, 48vw);
}}
body[data-dna-style="{dna.style}"] .brand-mark-wrap {{ display: inline-flex; line-height: 0; }}
body[data-dna-style="{dna.style}"] .brand-word {{
  font-family: var(--font-display, Georgia, serif);
  font-size: 1.05rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
body[data-dna-style="{dna.style}"] .brand-logo-img {{
  max-height: 2.4rem; max-width: 7rem; width: auto; object-fit: contain;
}}
body[data-dna-style="{dna.style}"] .svc-ico {{
  width: 2.25rem; height: 2.25rem; border-radius: 0.65rem;
  display: grid; place-items: center;
  background: rgba({ar},{ag},{ab},{"0.22" if dark else "0.14"});
  color: {accent}; font-size: 1.05rem; margin-bottom: 0.65rem;
}}
body[data-dna-style="{dna.style}"] .section,
body[data-dna-style="{dna.style}"] .service-card,
body[data-dna-style="{dna.style}"] .svc-card {{
  animation: dnaReveal 0.7s ease both;
}}
@keyframes dnaReveal {{
  from {{ opacity: 0; transform: translateY(14px); }}
  to {{ opacity: 1; transform: none; }}
}}
@media (prefers-reduced-motion: reduce) {{
  html {{ scroll-behavior: auto; }}
  body[data-dna-style="{dna.style}"] .section,
  body[data-dna-style="{dna.style}"] .service-card {{ animation: none; }}
}}
.dna-atm {{
  pointer-events: none; position: fixed; inset: 0; z-index: -1; overflow: hidden;
  opacity: {atm_opacity};
}}
.dna-atm__base {{
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse 85% 55% at 50% -8%, rgba({ar},{ag},{ab},{"0.22" if not dark else "0.4"}), transparent 58%),
    linear-gradient(165deg, {body_bg} 0%, color-mix(in srgb, {accent} {"10%" if not dark else "18%"}, {body_bg}) 45%, {body_bg} 100%);
}}
.dna-atm__mesh {{
  position: absolute; inset: -22%;
  background:
    radial-gradient(ellipse 48% 36% at 14% 20%, rgba({ar},{ag},{ab},{"0.28" if not dark else "0.45"}), transparent 58%),
    radial-gradient(ellipse 40% 30% at 86% 24%, rgba({ar},{ag},{ab},0.18), transparent 55%),
    radial-gradient(ellipse 44% 34% at 50% 90%, rgba({ar},{ag},{ab},0.14), transparent 55%);
  animation: dnaMeshDrift 22s ease-in-out infinite alternate;
}}
.dna-atm__aurora {{
  position: absolute; width: 50vmax; height: 50vmax; border-radius: 42%;
  filter: blur(72px); opacity: {"0.28" if not dark else "0.4"}; mix-blend-mode: {blend};
}}
.dna-atm__aurora--a {{
  left: -16%; top: -12%;
  background: conic-gradient(from 110deg, rgba({ar},{ag},{ab},0.55), transparent 55%, rgba({ar},{ag},{ab},0.25));
  animation: dnaAuroraSpin 32s linear infinite;
}}
.dna-atm__aurora--b {{
  right: -20%; top: 28%; opacity: 0.22;
  background: conic-gradient(from 250deg, rgba({ar},{ag},{ab},0.4), transparent 50%, rgba(201,184,166,0.35));
  animation: dnaAuroraSpin 40s linear infinite reverse;
}}
.dna-atm__aurora--c {{
  left: 18%; bottom: -28%; width: 68vmax; height: 38vmax;
  background: radial-gradient(ellipse at center, rgba({ar},{ag},{ab},{"0.32" if not dark else "0.4"}), transparent 65%);
  animation: dnaAuroraDrift 26s ease-in-out infinite alternate;
  opacity: {"0.45" if pid == "premium" else "0.32"};
  filter: blur(64px); mix-blend-mode: {blend};
}}
.dna-atm__grid {{
  position: absolute; inset: 0; opacity: {"0.22" if pid == "premium" else "0.14"};
  background-image:
    linear-gradient(rgba({ir},{ig},{ib},{"0.06" if not dark else "0.07"}) 1px, transparent 1px),
    linear-gradient(90deg, rgba({ir},{ig},{ib},{"0.06" if not dark else "0.07"}) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: radial-gradient(ellipse 75% 65% at 50% 28%, black, transparent 78%);
  animation: dnaGridDrift 42s linear infinite;
}}
.dna-atm__grid--soft {{ opacity: 0.1; background-size: 64px 64px; }}
.dna-atm__illu {{
  position: absolute; inset: -10%;
  opacity: {"0.55" if pid == "premium" else "0.4" if pid == "business" else "0.3"};
  background:
    radial-gradient(ellipse 28% 22% at 78% 18%, rgba({ar},{ag},{ab},0.2), transparent 70%),
    radial-gradient(ellipse 22% 30% at 12% 72%, rgba(201,184,166,0.18), transparent 68%),
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120'%3E%3Ccircle cx='60' cy='60' r='48' fill='none' stroke='%235b7c6e' stroke-opacity='0.07' stroke-width='1'/%3E%3Cpath d='M20 80 Q60 20 100 80' fill='none' stroke='%23a68a6d' stroke-opacity='0.08' stroke-width='1.2'/%3E%3C/svg%3E");
  background-size: auto, auto, 180px 180px;
  background-repeat: no-repeat, no-repeat, repeat;
  animation: dnaIlluDrift 48s ease-in-out infinite alternate;
  mix-blend-mode: {blend};
}}
.dna-atm__orb {{
  position: absolute; border-radius: 9999px; filter: blur(56px); opacity: {"0.45" if not dark else "0.6"};
  animation: dnaOrbFloat 18s ease-in-out infinite;
}}
.dna-atm__orb--a {{ width: 20rem; height: 20rem; left: -7%; top: 8%; background: rgba({ar},{ag},{ab},0.4); }}
.dna-atm__orb--b {{ width: 16rem; height: 16rem; right: -5%; top: 42%; background: rgba(201,184,166,0.32); animation-delay: -6s; }}
.dna-atm__orb--c {{ width: 14rem; height: 14rem; left: 38%; bottom: 4%; background: rgba({ar},{ag},{ab},0.25); animation-delay: -11s; }}
.dna-atm__orb--d {{
  width: 22rem; height: 22rem; right: 18%; bottom: -6%;
  background: rgba({ar},{ag},{ab},0.22); animation-delay: -14s; opacity: {"0.55" if pid == "premium" else "0.4" if pid == "business" else "0.32"};
}}
.dna-atm__particles {{ position: absolute; inset: 0; }}
.dna-atm__particle {{
  position: absolute; left: var(--sx); top: var(--sy);
  width: var(--size); height: var(--size); border-radius: 9999px;
  background: {particle};
  box-shadow: 0 0 10px rgba({ar},{ag},{ab},0.45);
  animation: dnaParticle var(--dur) ease-in-out infinite;
  animation-delay: var(--delay); opacity: 0.45;
}}
.dna-atm__vignette {{
  position: absolute; inset: 0;
  background: radial-gradient(ellipse 75% 60% at 50% 35%, transparent 40%, {"rgba("+str(sr)+","+str(sg)+","+str(sb)+",0.45)" if not dark else "rgba(8,10,12,0.5)"} 100%);
}}
@keyframes dnaMeshDrift {{
  0% {{ transform: translate(0,0) scale(1); }}
  100% {{ transform: translate(-2%,1.8%) scale(1.05); }}
}}
@keyframes dnaAuroraSpin {{
  from {{ transform: rotate(0deg) scale(1); }}
  to {{ transform: rotate(360deg) scale(1.06); }}
}}
@keyframes dnaAuroraDrift {{
  0% {{ transform: translate(0,0) scale(1); }}
  100% {{ transform: translate(3%,-2%) scale(1.08); }}
}}
@keyframes dnaGridDrift {{
  0% {{ transform: translateY(0); }}
  100% {{ transform: translateY(28px); }}
}}
@keyframes dnaIlluDrift {{
  0% {{ transform: translate(0,0) rotate(0deg); }}
  100% {{ transform: translate(-1.5%,1%) rotate(2deg); }}
}}
@keyframes dnaOrbFloat {{
  0%, 100% {{ transform: translate(0,0); }}
  50% {{ transform: translate(14px,-18px); }}
}}
@keyframes dnaParticle {{
  0%, 100% {{ transform: translate(0,0) scale(1); opacity: 0.25; }}
  50% {{ transform: translate(8px,-22px) scale(1.35); opacity: 0.85; }}
}}
@keyframes dnaPanelShine {{
  0% {{ background-position: 0% 50%; }}
  100% {{ background-position: 100% 50%; }}
}}
@keyframes dnaCardLift {{
  from {{ transform: translateY(0); }}
  to {{ transform: translateY(-6px); }}
}}
@media (prefers-reduced-motion: reduce) {{
  .dna-atm__mesh, .dna-atm__aurora, .dna-atm__orb, .dna-atm__particle {{ animation: none !important; }}
}}

/* Scene stack — content above atmosphere, never off-screen */
body[data-dna-style="{dna.style}"] .topbar,
body[data-dna-style="{dna.style}"] .hero,
body[data-dna-style="{dna.style}"] .section,
body[data-dna-style="{dna.style}"] footer,
body[data-dna-style="{dna.style}"] .premium-signature,
body[data-dna-style="{dna.style}"] .info-bar,
body[data-dna-style="{dna.style}"] .mid-cta,
body[data-dna-style="{dna.style}"] .stats {{
  position: relative; z-index: 1; box-sizing: border-box; max-width: 100%;
}}
body[data-dna-style="{dna.style}"] .section,
body[data-dna-style="{dna.style}"] .mid-cta,
body[data-dna-style="{dna.style}"] .stats,
body[data-dna-style="{dna.style}"] .premium-signature {{
  width: 100%; max-width: none; margin-inline: 0;
  padding-inline: max(1.25rem, calc(50vw - 36rem));
  box-sizing: border-box;
}}
body[data-dna-style="{dna.style}"] .section > *,
body[data-dna-style="{dna.style}"] .mid-cta > *,
body[data-dna-style="{dna.style}"] .premium-signature-copy {{
  max-width: var(--dna-content); width: 100%; margin-inline: auto; box-sizing: border-box;
}}

/* Navigation — glass, sticky, reacts to scroll */
body[data-dna-style="{dna.style}"] .topbar {{
  position: sticky; top: 0; z-index: 40;
  width: 100%; max-width: none; margin-inline: 0;
  padding-inline: max(1rem, calc(50vw - 36rem));
  box-sizing: border-box;
  background: {"rgba(255,255,255,0.55)" if not dark else "rgba(8,10,12,0.45)"} !important;
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid {"rgba("+str(ar)+","+str(ag)+","+str(ab)+",0.12)" if not dark else "rgba(255,255,255,0.08)"};
  transition: background 0.35s ease, box-shadow 0.35s ease, border-color 0.35s ease;
}}
body[data-dna-style="{dna.style}"] .topbar.is-scrolled {{
  background: {"rgba(255,255,255,0.82)" if not dark else "rgba(8,10,12,0.78)"} !important;
  box-shadow: 0 12px 40px rgba(0,0,0,{"0.08" if not dark else "0.35"});
}}
body[data-dna-style="{dna.style}"] .topbar a {{
  transition: color 0.25s ease, opacity 0.25s ease;
}}
body[data-dna-style="{dna.style}"] .topbar a:hover {{
  color: {accent} !important;
}}
/* Light glass nav must never inherit photo-hero white text */
body[data-dna-style="{dna.style}"] .topbar,
body[data-dna-style="{dna.style}"] .topbar .brand,
body[data-dna-style="{dna.style}"] .topbar .logo-fallback,
body[data-dna-style="{dna.style}"] .topbar a:not(.btn):not(.cta-button) {{
  color: {"#fafaf9" if dark else ink} !important;
}}
body[data-dna-style="{dna.style}"] .topbar .btn,
body[data-dna-style="{dna.style}"] .topbar .cta-button {{
  background: {accent} !important;
  color: #fafaf9 !important;
  border-color: transparent !important;
}}

/* Hero — impression first */
body[data-dna-style="{dna.style}"] .hero {{
  width: 100%; max-width: none; margin-inline: 0;
  padding-inline: max(1.25rem, calc(50vw - 36rem));
  box-sizing: border-box; overflow: hidden; isolation: isolate;
  min-height: {hero_min}; min-height: {hero_min.replace("vh", "dvh")};
  display: flex; flex-direction: column; justify-content: center; align-items: flex-start; gap: 1.25rem;
}}
/* Heroes A/C/E: dark ink on light canvas; light ink on cinematic canvas */
body[data-dna-style="{dna.style}"] .hero.hero-layout-A,
body[data-dna-style="{dna.style}"] .hero.hero-layout-C,
body[data-dna-style="{dna.style}"] .hero.hero-layout-E {{
  color: {"#fafaf9" if dark else ink} !important;
  background-color: transparent !important;
}}
body[data-dna-style="{dna.style}"] .hero.hero-layout-A h1,
body[data-dna-style="{dna.style}"] .hero.hero-layout-A .lead,
body[data-dna-style="{dna.style}"] .hero.hero-layout-A p,
body[data-dna-style="{dna.style}"] .hero.hero-layout-C h1,
body[data-dna-style="{dna.style}"] .hero.hero-layout-C .lead,
body[data-dna-style="{dna.style}"] .hero.hero-layout-C p,
body[data-dna-style="{dna.style}"] .hero.hero-layout-E h1,
body[data-dna-style="{dna.style}"] .hero.hero-layout-E .lead,
body[data-dna-style="{dna.style}"] .hero.hero-layout-E p {{
  color: {"#fafaf9" if dark else ink} !important;
  text-shadow: {"0 2px 28px rgba(0,0,0,0.4)" if dark else "none"} !important;
}}
body[data-dna-style="{dna.style}"] .hero.hero-layout-A .btn,
body[data-dna-style="{dna.style}"] .hero.hero-layout-C .btn,
body[data-dna-style="{dna.style}"] .hero.hero-layout-E .btn {{
  background: {accent} !important;
  color: #fafaf9 !important;
  border-color: transparent !important;
  box-shadow: 0 10px 28px rgba({ar},{ag},{ab},0.28) !important;
}}
/* Primary CTA wins over Component Composer .btn-outline ghosts */
body[data-dna-style="{dna.style}"] .hero.hero-layout-A a.btn.cta-button:not(.btn-wa),
body[data-dna-style="{dna.style}"] .hero.hero-layout-C a.btn.cta-button:not(.btn-wa),
body[data-dna-style="{dna.style}"] .hero.hero-layout-E a.btn.cta-button:not(.btn-wa) {{
  background: {accent} !important;
  color: #fafaf9 !important;
  border: none !important;
}}
body[data-dna-style="{dna.style}"] .hero.hero-layout-A .btn-outline.btn-wa,
body[data-dna-style="{dna.style}"] .hero.hero-layout-C .btn-outline.btn-wa,
body[data-dna-style="{dna.style}"] .hero.hero-layout-E .btn-outline.btn-wa,
body[data-dna-style="{dna.style}"] .hero.hero-layout-A .btn-wa,
body[data-dna-style="{dna.style}"] .hero.hero-layout-C .btn-wa,
body[data-dna-style="{dna.style}"] .hero.hero-layout-E .btn-wa {{
  background: #25d366 !important;
  color: #052e16 !important;
  border-color: transparent !important;
  box-shadow: none !important;
}}
body[data-dna-style="{dna.style}"] .hero.hero-layout-A .btn-reviews:not(.btn-wa),
body[data-dna-style="{dna.style}"] .hero.hero-layout-C .btn-reviews:not(.btn-wa),
body[data-dna-style="{dna.style}"] .hero.hero-layout-E .btn-reviews:not(.btn-wa) {{
  color: {ink} !important;
  border: 2px solid rgba({ir},{ig},{ib},0.4) !important;
  background: rgba(255,255,255,0.72) !important;
  box-shadow: none !important;
}}
/* Immersive heroes: solid primary CTA (ghost white outline fails on busy photos) */
body[data-dna-style="{dna.style}"] .hero.hero-layout-B .btn:not(.btn-wa),
body[data-dna-style="{dna.style}"] .hero.hero-layout-D .btn:not(.btn-wa),
body[data-dna-style="{dna.style}"] .hero.hero-layout-F .btn:not(.btn-wa),
body[data-dna-style="{dna.style}"] .hero.hero-layout-B a.btn.cta-button:not(.btn-wa),
body[data-dna-style="{dna.style}"] .hero.hero-layout-D a.btn.cta-button:not(.btn-wa),
body[data-dna-style="{dna.style}"] .hero.hero-layout-F a.btn.cta-button:not(.btn-wa) {{
  background: {accent} !important;
  color: #fafaf9 !important;
  border-color: transparent !important;
}}
body[data-dna-style="{dna.style}"] .hero.hero-layout-B .btn-wa,
body[data-dna-style="{dna.style}"] .hero.hero-layout-D .btn-wa,
body[data-dna-style="{dna.style}"] .hero.hero-layout-F .btn-wa {{
  background: #25d366 !important;
  color: #052e16 !important;
  border-color: transparent !important;
}}
body[data-dna-style="{dna.style}"] .hero.hero-layout-B h1,
body[data-dna-style="{dna.style}"] .hero.hero-layout-D h1,
body[data-dna-style="{dna.style}"] .hero.hero-layout-F h1,
body[data-dna-style="{dna.style}"] .hero.hero-layout-B .lead,
body[data-dna-style="{dna.style}"] .hero.hero-layout-D .lead,
body[data-dna-style="{dna.style}"] .hero.hero-layout-F .lead {{
  color: #fafaf9 !important;
  text-shadow: 0 2px 24px rgba(0,0,0,0.35);
}}
body[data-dna-style="{dna.style}"] .hero-D-panel {{
  max-width: min(40rem, 100%) !important; margin-left: 0 !important;
  background:
    linear-gradient(135deg, {"rgba(255,255,255,0.55)" if not dark else "rgba(255,255,255,0.12)"}, {"rgba(247,244,239,0.82)" if not dark else "rgba(8,10,12,0.2)"} 45%, rgba({ar},{ag},{ab},{"0.12" if not dark else "0.22"})),
    {"rgba(247,244,239,0.88)" if not dark else "rgba(8,10,12,0.55)"} !important;
  border: 1px solid {"rgba("+str(ir)+","+str(ig)+","+str(ib)+",0.12)" if not dark else "rgba(255,255,255,0.28)"} !important;
  box-shadow: 0 28px 80px rgba(0,0,0,{"0.14" if not dark else "0.45"}), inset 0 1px 0 rgba(255,255,255,0.5) !important;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  overflow: hidden; position: relative;
  color: {"#1c1917" if not dark else "#fafaf9"} !important;
}}
body[data-dna-style="{dna.style}"] .hero-D-panel h1,
body[data-dna-style="{dna.style}"] .hero-D-panel .lead,
body[data-dna-style="{dna.style}"] .hero-D-panel p {{
  color: {"#1c1917" if not dark else "#fafaf9"} !important;
  text-shadow: {"none" if not dark else "0 2px 24px rgba(0,0,0,0.35)"} !important;
}}
body[data-dna-style="{dna.style}"] .hero.hero-layout-D .hero-D-panel h1,
body[data-dna-style="{dna.style}"] .hero.hero-layout-D .hero-D-panel .lead,
body[data-dna-style="{dna.style}"] .hero.hero-layout-D .hero-D-panel p {{
  color: {"#1c1917" if not dark else "#fafaf9"} !important;
  text-shadow: {"none" if not dark else "0 2px 24px rgba(0,0,0,0.35)"} !important;
}}
body[data-dna-style="{dna.style}"] .hero-D-panel::before {{
  content: ""; position: absolute; inset: 0; border-radius: inherit; pointer-events: none; z-index: 1;
  background: linear-gradient(105deg, transparent 38%, rgba(255,255,255,0.35) 50%, transparent 62%);
  background-size: 220% 100%; animation: dnaPanelShine 5s ease-in-out infinite; opacity: {"0.45" if not dark else "0.85"};
}}
body[data-dna-style="{dna.style}"] .hero-D-panel > * {{ position: relative; z-index: 2; }}
/* Premium wow — first 3 seconds: full-bleed emotion, not corporate card */
body[data-tier="premium"][data-dna-style="{dna.style}"] .hero.hero-layout-D {{
  min-height: 100vh !important; min-height: 100dvh !important;
}}
body[data-tier="premium"][data-dna-style="{dna.style}"] .hero.hero-layout-D.has-photo {{
  background-image:
    linear-gradient(115deg, rgba(8,10,12,0.78) 0%, rgba(8,10,12,0.35) 42%, rgba({ar},{ag},{ab},0.28) 100%),
    url("assets/hero.jpg") !important;
  background-size: cover !important;
  background-position: center !important;
}}
body[data-tier="premium"][data-dna-style="{dna.style}"] .hero-D-panel {{
  max-width: min(36rem, 92vw) !important;
  margin-left: max(1.25rem, 10vw) !important;
  padding: 2.75rem 2.4rem !important;
  border-radius: 28px !important;
  /* Near-opaque: frosted blur over bright photos must not wash text to white-on-white */
  background: {"rgba(247,243,238,0.94)" if not dark else "rgba(14,12,10,0.90)"} !important;
  border: 1px solid {"rgba(28,25,23,0.12)" if not dark else "rgba(255,255,255,0.22)"} !important;
  box-shadow: 0 40px 100px rgba(0,0,0,0.45) !important;
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  color: {"#1c1917" if not dark else "#fafaf9"} !important;
}}
body[data-tier="premium"][data-dna-style="{dna.style}"] .hero-D-panel::before {{
  opacity: {"0.35" if not dark else "0.15"} !important;
}}
body[data-tier="premium"][data-dna-style="{dna.style}"] .hero-D-panel h1 {{
  font-size: clamp(2.4rem, 5.8vw, 3.85rem) !important;
  line-height: 1.05 !important;
  letter-spacing: -0.03em !important;
  color: {"#1c1917" if not dark else "#fafaf9"} !important;
  text-shadow: {"none" if not dark else "0 4px 40px rgba(0,0,0,0.45)"} !important;
  max-width: 14ch;
}}
body[data-tier="premium"][data-dna-style="{dna.style}"] .hero-D-panel .lead,
body[data-tier="premium"][data-dna-style="{dna.style}"] .hero-D-panel p {{
  color: {"rgba(28,25,23,0.88)" if not dark else "rgba(250,250,249,0.92)"} !important;
  font-size: 1.12rem !important;
  max-width: 34ch;
}}
body[data-dna-style="{dna.style}"] .hero-D-float {{
  position: static !important; inset: auto !important;
  width: min(40rem, 100%) !important; max-width: 100% !important;
  display: grid !important; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.75rem;
}}
body[data-dna-style="{dna.style}"] .hero-D-float .hero-kpi {{
  background: rgba(255,255,255,0.88); color: #1c1917;
  border: 1px solid rgba(255,255,255,0.6);
  box-shadow: 0 12px 32px rgba(0,0,0,0.12); text-align: center;
  transition: transform 0.35s ease, box-shadow 0.35s ease;
}}
body[data-dna-style="{dna.style}"] .hero-D-float .hero-kpi:hover {{
  transform: translateY(-4px); box-shadow: 0 18px 40px rgba({ar},{ag},{ab},0.25);
}}

/* Cards live — hover lift + glow */
body[data-dna-style="{dna.style}"] .service-card,
body[data-dna-style="{dna.style}"] .svc-card,
body[data-dna-style="{dna.style}"] .svc-glass,
body[data-dna-style="{dna.style}"] .process-card,
body[data-dna-style="{dna.style}"] .faq-item,
body[data-dna-style="{dna.style}"] .faq-bubble,
body[data-dna-style="{dna.style}"] .faq-panel,
body[data-dna-style="{dna.style}"] .faq-acc,
body[data-dna-style="{dna.style}"] .testimonial-card,
body[data-dna-style="{dna.style}"] .services-block li,
body[data-dna-style="{dna.style}"] .benefits li {{
  background: {"rgba(255,255,255,0.88)" if not dark else "rgba(18,22,20,0.82)"} !important;
  border: 1px solid rgba({ar},{ag},{ab},{"0.22" if not dark else "0.32"}) !important;
  backdrop-filter: blur(var(--dna-glass-blur));
  -webkit-backdrop-filter: blur(var(--dna-glass-blur));
  box-shadow: 0 14px 40px rgba(28,25,23,{"0.08" if not dark else "0.35"}), inset 0 1px 0 rgba(255,255,255,{"0.55" if not dark else "0.1"});
  border-radius: 1.1rem;
  color: {"#1c1917" if not dark else "#fafaf9"} !important;
  transition: transform 0.4s cubic-bezier(0.16,1,0.3,1), box-shadow 0.4s ease, border-color 0.35s ease;
}}
body[data-dna-style="{dna.style}"] .service-card h3,
body[data-dna-style="{dna.style}"] .svc-card h3,
body[data-dna-style="{dna.style}"] .faq-bubble h3,
body[data-dna-style="{dna.style}"] .faq-panel h3,
body[data-dna-style="{dna.style}"] .faq-acc summary,
body[data-dna-style="{dna.style}"] .testimonial-card p,
body[data-dna-style="{dna.style}"] .service-card p,
body[data-dna-style="{dna.style}"] .svc-card p,
body[data-dna-style="{dna.style}"] .faq-bubble p,
body[data-dna-style="{dna.style}"] .faq-panel p,
body[data-dna-style="{dna.style}"] .faq-acc p,
body[data-dna-style="{dna.style}"] .services-block li,
body[data-dna-style="{dna.style}"] .benefits li {{
  color: {"#1c1917" if not dark else "#fafaf9"} !important;
}}
body[data-dna-style="{dna.style}"] .section h2,
body[data-dna-style="{dna.style}"] .section .muted,
body[data-dna-style="{dna.style}"] .about p,
body[data-dna-style="{dna.style}"] .about h2,
body[data-dna-style="{dna.style}"] footer,
body[data-dna-style="{dna.style}"] footer a,
body[data-dna-style="{dna.style}"] .contact label,
body[data-dna-style="{dna.style}"] .contact p {{
  color: {"inherit" if not dark else "#fafaf9"} !important;
}}
body[data-dna-style="{dna.style}"] .section .muted,
body[data-dna-style="{dna.style}"] .muted {{
  color: {"rgba("+str(ir)+","+str(ig)+","+str(ib)+",0.78)" if not dark else "rgba(250,250,249,0.82)"} !important;
}}
body[data-dna-style="{dna.style}"] .section {{
  background: {"transparent" if not dark else "rgba(8,10,12,0.22)"} !important;
}}
body[data-dna-style="{dna.style}"] .section.section-alt,
body[data-dna-style="{dna.style}"] .section-alt {{
  background: {"rgba(255,255,255,0.35)" if not dark else "rgba(255,255,255,0.04)"} !important;
}}
body[data-dna-style="{dna.style}"] .contact-form input,
body[data-dna-style="{dna.style}"] .contact-form textarea,
body[data-dna-style="{dna.style}"] input,
body[data-dna-style="{dna.style}"] textarea {{
  background: {"#fff" if not dark else "rgba(255,255,255,0.08)"} !important;
  color: {"#1c1917" if not dark else "#fafaf9"} !important;
  border: 1px solid {"rgba(28,25,23,0.18)" if not dark else "rgba(255,255,255,0.22)"} !important;
}}
body[data-dna-style="{dna.style}"] .contact-form input::placeholder,
body[data-dna-style="{dna.style}"] .contact-form textarea::placeholder {{
  color: {"rgba(28,25,23,0.45)" if not dark else "rgba(250,250,249,0.45)"} !important;
}}
body[data-dna-style="{dna.style}"] .hero-D-float .hero-kpi {{
  background: {"rgba(255,255,255,0.92)" if not dark else "rgba(8,10,12,0.72)"} !important;
  color: {"#1c1917" if not dark else "#fafaf9"} !important;
  border: 1px solid {"rgba(255,255,255,0.6)" if not dark else "rgba(255,255,255,0.22)"} !important;
}}
body[data-dna-style="{dna.style}"] .hero-D-float .hero-kpi strong,
body[data-dna-style="{dna.style}"] .hero-D-float .hero-kpi span {{
  color: inherit !important;
}}
/* Enable Premium atmosphere layers for Business/Starter too */
.dna-atm__illu {{
  opacity: {"0.55" if pid == "premium" else "0.38" if pid == "business" else "0.28"} !important;
}}
.dna-atm__orb--c {{
  opacity: {"0.5" if pid != "basic" else "0.35"} !important;
}}
body[data-dna-style="{dna.style}"] .service-card:hover,
body[data-dna-style="{dna.style}"] .svc-card:hover,
body[data-dna-style="{dna.style}"] .faq-item:hover,
body[data-dna-style="{dna.style}"] .services-block li:hover,
body[data-dna-style="{dna.style}"] .benefits li:hover {{
  transform: translateY(-6px);
  border-color: rgba({ar},{ag},{ab},0.45) !important;
  box-shadow: 0 22px 56px rgba({ar},{ag},{ab},0.22), inset 0 1px 0 rgba(255,255,255,0.55);
}}
body[data-dna-style="{dna.style}"] .btn {{
  background: {accent}; color: #fafaf9;
  box-shadow: 0 12px 28px rgba({ar},{ag},{ab},0.35);
  transition: transform 0.3s ease, filter 0.3s ease, box-shadow 0.3s ease;
}}
body[data-dna-style="{dna.style}"] .btn:hover {{
  filter: brightness(1.06); transform: translateY(-2px);
  box-shadow: 0 16px 36px rgba({ar},{ag},{ab},0.45);
}}

/* Readable cards on dark/photo scenes — NEVER white text on white cards */
body[data-dna-style="{dna.style}"] .sec-treat-photo_band .service-card,
body[data-dna-style="{dna.style}"] .sec-treat-photo_band .svc-card,
body[data-dna-style="{dna.style}"] .sec-treat-photo_band .svc-glass,
body[data-dna-style="{dna.style}"] .sec-treat-photo_band li.svc-card,
body[data-dna-style="{dna.style}"] .sec-treat-ink .service-card,
body[data-dna-style="{dna.style}"] .sec-treat-ink .svc-card,
body[data-dna-style="{dna.style}"] .sec-treat-ink .svc-glass,
body[data-dna-style="{dna.style}"] .sec-treat-ink li.svc-card,
body[data-dna-style="{dna.style}"] .sec-treat-photo_band .faq-item,
body[data-dna-style="{dna.style}"] .sec-treat-ink .faq-item {{
  background: {"rgba(18,14,12,0.88)" if dark else "rgba(255,255,255,0.94)"} !important;
  color: {"#fafaf9" if dark else "#1c1917"} !important;
  border-color: {"rgba(255,255,255,0.14)" if dark else "rgba(255,255,255,0.7)"} !important;
}}
body[data-dna-style="{dna.style}"] .sec-treat-photo_band .svc-card h3,
body[data-dna-style="{dna.style}"] .sec-treat-photo_band .svc-glass h3,
body[data-dna-style="{dna.style}"] .sec-treat-photo_band .service-card h3,
body[data-dna-style="{dna.style}"] .sec-treat-photo_band .service-desc,
body[data-dna-style="{dna.style}"] .sec-treat-photo_band .svc-card p,
body[data-dna-style="{dna.style}"] .sec-treat-photo_band li,
body[data-dna-style="{dna.style}"] .sec-treat-ink .svc-card h3,
body[data-dna-style="{dna.style}"] .sec-treat-ink .svc-glass h3,
body[data-dna-style="{dna.style}"] .sec-treat-ink .service-card h3,
body[data-dna-style="{dna.style}"] .sec-treat-ink .service-desc,
body[data-dna-style="{dna.style}"] .sec-treat-ink .svc-card p,
body[data-dna-style="{dna.style}"] .sec-treat-ink li {{
  color: {"#fafaf9" if dark else "#1c1917"} !important;
}}
body[data-dna-style="{dna.style}"] .sec-treat-photo_band > h2,
body[data-dna-style="{dna.style}"] .sec-treat-ink > h2 {{
  color: #fafaf9 !important;
}}

/* Composition modes — Digital Creative Studio library */
body[data-dna-composition="magazine"] .services-block ul,
body[data-dna-composition="magazine"] .services-block .svc-grid,
body[data-dna-composition="editorial"] .services-block ul,
body[data-dna-composition="folio"] .services-block ul {{
  display: grid !important; grid-template-columns: 1.15fr 0.85fr; gap: 1.25rem; align-items: stretch;
}}
body[data-dna-composition="magazine"] .services-block li:first-child,
body[data-dna-composition="editorial"] .services-block li:first-child {{
  grid-row: span 2; min-height: 16rem;
}}
body[data-dna-composition="organic"] .benefits ul,
body[data-dna-composition="organic"] .benefits ol,
body[data-dna-composition="garden"] .benefits ul,
body[data-dna-composition="sanctuary"] .benefits ul {{
  display: grid !important; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: 1rem;
}}
body[data-dna-composition="immersive"] .about,
body[data-dna-composition="cinematic"] .about,
body[data-dna-composition="horizon"] .about,
body[data-dna-composition="whisper"] .about {{
  display: grid; grid-template-columns: 1fr 1.1fr; gap: 2rem; align-items: center;
}}
body[data-dna-composition="split"] .about,
body[data-dna-composition="dialogue"] .about,
body[data-dna-composition="chamber"] .about {{
  display: grid; grid-template-columns: 0.95fr 1.05fr; gap: 2.5rem; align-items: start;
}}
body[data-dna-composition="asymmetrical"] .services-block ul,
body[data-dna-composition="atelier"] .services-block ul,
body[data-dna-composition="boutique"] .services-block ul {{
  display: grid !important;
  grid-template-columns: 1.3fr 0.7fr 1fr;
  gap: 1rem;
}}
body[data-dna-composition="storytelling"] .process,
body[data-dna-composition="timeline"] .process,
body[data-dna-composition="ritual"] .process {{
  max-width: none !important;
}}
body[data-dna-composition="storytelling"] .process ol,
body[data-dna-composition="timeline"] .process ol,
body[data-dna-composition="ritual"] .process ol {{
  display: grid !important; grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr)); gap: 1.25rem;
  counter-reset: studio-step;
}}
body[data-dna-composition="gallery"] .gallery,
body[data-dna-composition="folio"] .gallery,
body[data-dna-composition="atelier"] .gallery {{
  padding-block: 4.5rem !important;
}}
body[data-dna-composition="trust_cascade"] .trust,
body[data-dna-composition="chamber"] .trust {{
  padding-block: 4rem !important;
}}
body[data-dna-composition="manifesto"] .about,
body[data-dna-composition="whisper"] .about {{
  font-size: 1.08em;
}}
body[data-dna-composition="pulse"] .stats {{
  display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem;
}}
body[data-dna-composition="overture"] .showcase,
body[data-dna-composition="cinematic"] .showcase {{
  min-height: 42vh;
}}
@media (max-width: 820px) {{
  body[data-dna-composition="magazine"] .services-block ul,
  body[data-dna-composition="magazine"] .services-block .svc-grid,
  body[data-dna-composition="editorial"] .services-block ul,
  body[data-dna-composition="immersive"] .about,
  body[data-dna-composition="cinematic"] .about,
  body[data-dna-composition="horizon"] .about,
  body[data-dna-composition="whisper"] .about,
  body[data-dna-composition="split"] .about,
  body[data-dna-composition="dialogue"] .about,
  body[data-dna-composition="chamber"] .about,
  body[data-dna-composition="asymmetrical"] .services-block ul,
  body[data-dna-composition="atelier"] .services-block ul,
  body[data-dna-composition="boutique"] .services-block ul {{
    grid-template-columns: 1fr !important;
  }}
  body[data-dna-composition="magazine"] .services-block li:first-child,
  body[data-dna-composition="editorial"] .services-block li:first-child {{ grid-row: auto; }}
  body[data-dna-composition="pulse"] .stats {{ grid-template-columns: 1fr; }}
}}

body[data-dna-style="{dna.style}"] footer {{
  width: 100%; max-width: none; margin-inline: 0;
  padding-inline: max(1rem, calc(50vw - 36rem));
  box-sizing: border-box;
  background: {"rgba("+str(ir)+","+str(ig)+","+str(ib)+",0.92)" if not dark else "rgba(0,0,0,0.45)"} !important;
  color: #e7e5e4 !important;
}}
{craft_bg_css}
{treat_css}

/* CONTRAST LOCK (last) — never light text on light panels / dark text on dark panels */
body[data-dna-style="{dna.style}"] .svc-card,
body[data-dna-style="{dna.style}"] .svc-glass,
body[data-dna-style="{dna.style}"] .svc-solid,
body[data-dna-style="{dna.style}"] .svc-minimal,
body[data-dna-style="{dna.style}"] .service-card,
body[data-dna-style="{dna.style}"] .testimonial-card,
body[data-dna-style="{dna.style}"] .faq-item,
body[data-dna-style="{dna.style}"] .faq-bubble,
body[data-dna-style="{dna.style}"] .faq-panel,
body[data-dna-style="{dna.style}"] .account-panel,
body[data-dna-style="{dna.style}"] .product-card,
body[data-dna-style="{dna.style}"] .trust-card,
body[data-dna-style="{dna.style}"] .process-step,
body[data-dna-style="{dna.style}"] .process-card,
body[data-dna-style="{dna.style}"] .services-block li,
body[data-dna-style="{dna.style}"] .hero-D-panel {{
  background: {"#1a1612" if dark else "#f7f3ee"} !important;
  color: {"#fafaf9" if dark else "#1c1917"} !important;
  border: 1px solid {"rgba(255,255,255,0.14)" if dark else "rgba(28,25,23,0.12)"} !important;
}}
body[data-dna-style="{dna.style}"] .svc-card h3,
body[data-dna-style="{dna.style}"] .svc-glass h3,
body[data-dna-style="{dna.style}"] .svc-solid h3,
body[data-dna-style="{dna.style}"] .svc-minimal h3,
body[data-dna-style="{dna.style}"] .service-card h3,
body[data-dna-style="{dna.style}"] .process-card h3,
body[data-dna-style="{dna.style}"] .process-card p,
body[data-dna-style="{dna.style}"] .process-grid h3,
body[data-dna-style="{dna.style}"] .trust-composer h3,
body[data-dna-style="{dna.style}"] .svc-card p,
body[data-dna-style="{dna.style}"] .svc-glass p,
body[data-dna-style="{dna.style}"] .service-desc,
body[data-dna-style="{dna.style}"] .faq-item h3,
body[data-dna-style="{dna.style}"] .faq-item p,
body[data-dna-style="{dna.style}"] .faq-bubble h3,
body[data-dna-style="{dna.style}"] .faq-panel h3,
body[data-dna-style="{dna.style}"] .faq-acc summary,
body[data-dna-style="{dna.style}"] .testimonial-card p,
body[data-dna-style="{dna.style}"] .testimonial-card cite,
body[data-dna-style="{dna.style}"] .account-panel,
body[data-dna-style="{dna.style}"] .account-panel h3,
body[data-dna-style="{dna.style}"] .account-panel label,
body[data-dna-style="{dna.style}"] .account-panel .muted,
body[data-dna-style="{dna.style}"] .section > h2,
body[data-dna-style="{dna.style}"] .section > h3,
body[data-dna-style="{dna.style}"] .about p,
body[data-dna-style="{dna.style}"] .benefits li,
body[data-dna-style="{dna.style}"] .hero-D-panel,
body[data-dna-style="{dna.style}"] .hero-D-panel h1,
body[data-dna-style="{dna.style}"] .hero-D-panel .lead,
body[data-dna-style="{dna.style}"] .hero-D-panel p {{
  color: {"#fafaf9" if dark else "#1c1917"} !important;
}}
body[data-dna-style="{dna.style}"] .svc-card .service-desc,
body[data-dna-style="{dna.style}"] .svc-glass .service-desc,
body[data-dna-style="{dna.style}"] .muted {{
  color: {"rgba(250,250,249,0.88)" if dark else "rgba(28,25,23,0.78)"} !important;
}}
body[data-dna-style="{dna.style}"] .account-panel input {{
  background: {"rgba(0,0,0,0.35)" if dark else "#fff"} !important;
  color: {"#fafaf9" if dark else "#1c1917"} !important;
  border: 1px solid {"rgba(255,255,255,0.2)" if dark else "rgba(28,25,23,0.18)"} !important;
}}
/* Primary buttons: never dark ink on dark panel / never white on pale CTA */
body[data-dna-style="{dna.style}"] a.btn:not(.btn-wa),
body[data-dna-style="{dna.style}"] button.btn:not(.btn-wa),
body[data-dna-style="{dna.style}"] .cta-button:not(.btn-wa),
body[data-dna-style="{dna.style}"] .account-panel .btn,
body[data-dna-style="{dna.style}"] .mid-cta .btn:not(.btn-wa),
body[data-dna-style="{dna.style}"] .conversion-mid-cta .btn:not(.btn-wa) {{
  background: rgb({ar},{ag},{ab}) !important;
  color: #fafaf9 !important;
  border-color: transparent !important;
}}
body[data-dna-style="{dna.style}"] .btn-wa {{
  background: #25d366 !important;
  color: #052e16 !important;
}}
body[data-dna-style="{dna.style}"] .mid-cta-inner,
body[data-dna-style="{dna.style}"] .mid-cta-glass .mid-cta-inner {{
  background: {"rgba(14,12,10,0.88)" if dark else "rgba(247,243,238,0.94)"} !important;
  color: {"#fafaf9" if dark else "#1c1917"} !important;
}}
body[data-dna-style="{dna.style}"] .mid-cta h2,
body[data-dna-style="{dna.style}"] .mid-cta-inner h2 {{
  color: {"#fafaf9" if dark else "#1c1917"} !important;
}}
"""


def _atm_mode(dna: DesignDNA) -> str:
    """Atmospheric canvas by niche — deep but not only night-black.

    Modes:
      cinematic — cool deep (auto/tech)
      dusk — warm amber depth (restaurant)
      velvet — plum depth (beauty/fashion)
      mist — soft sage mid, dark ink (nature/psychology)
      atelier — warm sand with depth, dark ink (boutique/basic warmth)
    """
    # Brand Book SSOT wins when present
    book_atm = (getattr(dna, "atmosphere_mode", None) or "").strip().lower()
    if book_atm in ("cinematic", "dusk", "velvet", "mist", "atelier", "organic"):
        return book_atm
    niche = (dna.niche_id or "").lower()
    style = (dna.style or "").lower()
    pid = dna.package_id
    if dna.composition in ("daylight_clear", "paper_editorial") and pid == "basic":
        return "organic"
    if niche in ("restaurant",) or "warm" in style or style == "boutique_warm":
        return "dusk" if pid == "premium" else "atelier"
    if niche in ("beauty", "fashion", "psychology"):
        return "velvet" if pid in ("premium", "business") else "mist"
    if niche in ("auto", "auto_ankauf", "computer", "energy"):
        return "cinematic"
    # Craft / local DE services — warm dusk depth + illustrated canvas (not pale white mist)
    if niche in (
        "handwerk",
        "green",
        "dental",
        "dachreinigung",
        "zaunbau",
        "gartenpflege",
        "cleaning",
        "maler",
        "sanitaer",
        "elektro",
    ):
        return "dusk" if pid == "premium" else "atelier"
    if style in ("cinematic_dark", "magazine_ink"):
        return "cinematic"
    if style in ("scandinavian_calm", "nature_therapy", "organic_premium"):
        return "mist"
    # Default: premium deep only for tech/auto-like; others warm atelier (non-white)
    if pid == "premium" and niche in ("law", "realestate", "it"):
        return "cinematic"
    return "atelier" if pid != "premium" else "mist"


def _hex_rgb(hex_color: str) -> tuple[int, int, int]:
    h = (hex_color or "#5b7c6e").strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return 91, 124, 110


def _treatment_css(dna: DesignDNA, *, dark: bool = False) -> str:
    bits: list[str] = []
    accent = dna.accent_hex
    ar, ag, ab = _hex_rgb(accent)
    pad = {"premium": "5.5rem", "business": "4.5rem", "basic": "3.75rem"}.get(
        dna.package_id, "4rem"
    )
    for _key, treat in dna.section_treatments:
        bits.append(_treat_rule(treat, accent, ar, ag, ab, pad, dark=dark))
    seen: set[str] = set()
    unique: list[str] = []
    for b in bits:
        if b not in seen:
            seen.add(b)
            unique.append(b)
    return "\n".join(unique)


def _treat_rule(
    treat: Treatment,
    accent: str,
    ar: int,
    ag: int,
    ab: int,
    pad: str,
    *,
    dark: bool = False,
) -> str:
    base = f".sec-treat-{treat}"
    if treat == "ink":
        return f"""
{base} {{
  background: linear-gradient(165deg, #1c1917 0%, rgba({ar},{ag},{ab},0.55) 100%) !important;
  color: #fafaf9 !important;
  padding-block: {pad} !important;
}}
{base} h2, {base} .muted, {base} p, {base} li {{ color: #fafaf9 !important; }}
{base} a {{ color: {accent} !important; }}
"""
    if treat == "tint":
        if dark:
            return f"""
{base} {{
  background: linear-gradient(135deg, rgba({ar},{ag},{ab},0.28), rgba(12,14,13,0.88)) !important;
  color: #fafaf9 !important;
  padding-block: {pad} !important;
}}
{base} h2, {base} .muted, {base} p, {base} li {{ color: #fafaf9 !important; }}
"""
        return f"""
{base} {{
  background: linear-gradient(135deg, rgba({ar},{ag},{ab},0.14), #ebe4d8) !important;
  padding-block: {pad} !important;
}}
"""
    if treat == "glass":
        if dark:
            return f"""
{base} {{
  background: rgba(255,255,255,0.05) !important;
  backdrop-filter: blur(16px);
  border-block: 1px solid rgba(255,255,255,0.12);
  color: #fafaf9 !important;
  padding-block: {pad} !important;
}}
{base} h2, {base} .muted, {base} p, {base} li {{ color: #fafaf9 !important; }}
"""
        return f"""
{base} {{
  background: rgba(255,255,255,0.45) !important;
  backdrop-filter: blur(16px);
  border-block: 1px solid rgba(255,255,255,0.4);
  padding-block: {pad} !important;
}}
"""
    if treat == "gradient":
        if dark:
            return f"""
{base} {{
  background: linear-gradient(160deg, rgba({ar},{ag},{ab},0.35), #0c0e0d 48%, rgba({ar},{ag},{ab},0.18)) !important;
  color: #fafaf9 !important;
  padding-block: {pad} !important;
}}
{base} h2, {base} .muted, {base} p, {base} li {{ color: #fafaf9 !important; }}
"""
        return f"""
{base} {{
  background: linear-gradient(160deg, rgba({ar},{ag},{ab},0.22), #fff8f0 55%, rgba({ar},{ag},{ab},0.12)) !important;
  padding-block: {pad} !important;
}}
"""
    if treat == "photo_band":
        return f"""
{base} {{
  background:
    linear-gradient(180deg, rgba(12,10,9,0.5), rgba(12,10,9,0.72)),
    url("assets/hero.jpg") center/cover no-repeat !important;
  color: #fafaf9 !important;
  padding-block: {pad} !important;
}}
{base} h2, {base} .muted {{ color: #fafaf9 !important; }}
"""
    if treat == "illustration":
        if dark:
            return f"""
{base} {{
  background:
    radial-gradient(circle at 85% 20%, rgba({ar},{ag},{ab},0.38), transparent 42%),
    radial-gradient(circle at 10% 80%, rgba(201,184,166,0.22), transparent 40%),
    linear-gradient(180deg, #121614, rgba({ar},{ag},{ab},0.2)) !important;
  color: #fafaf9 !important;
  padding-block: {pad} !important;
}}
{base} h2, {base} .muted, {base} p, {base} li {{ color: #fafaf9 !important; }}
"""
        return f"""
{base} {{
  background:
    radial-gradient(circle at 85% 20%, rgba({ar},{ag},{ab},0.32), transparent 42%),
    radial-gradient(circle at 10% 80%, rgba(201,184,166,0.35), transparent 40%),
    linear-gradient(180deg, #faf6f1, rgba({ar},{ag},{ab},0.12)) !important;
  padding-block: {pad} !important;
}}
"""
    if dark:
        return f"""
{base} {{
  background: color-mix(in srgb, {accent} 14%, #121614) !important;
  color: #fafaf9 !important;
  padding-block: {pad} !important;
}}
{base} h2, {base} .muted, {base} p, {base} li {{ color: #fafaf9 !important; }}
"""
    return f"""
{base} {{
  background: color-mix(in srgb, {accent} 8%, #faf8f5) !important;
  padding-block: {pad} !important;
}}
"""


def store_quality_floor_css(dna: DesignDNA) -> str:
    accent = dna.accent_hex
    surface = dna.surface_hex
    ink = dna.ink_hex
    ar, ag, ab = _hex_rgb(accent)
    ir, ig, ib = _hex_rgb(ink)
    pid = dna.package_id
    hero_min = {"basic": "70vh", "business": "84vh", "premium": "96vh"}.get(pid, "78vh")
    # Owner gold standard: deep canvas + dark cards — NEVER light panel + white ink
    dark = True
    sr, sg, sb = _hex_rgb(surface)
    surface_lum = 0.2126 * sr + 0.7152 * sg + 0.0722 * sb
    if surface_lum < 90:
        body_bg = surface
        card_r, card_g, card_b = max(14, sr), max(16, sg), max(18, sb)
    else:
        # DNA surface is cream/light — do not paint review/product cards with it
        body_bg = f"rgb({max(8, ir // 8)},{max(8, ig // 8)},{max(10, ib // 7)})"
        card_r, card_g, card_b = max(18, ir // 6), max(20, ig // 6), max(22, ib // 6)
    card_bg = f"rgba({card_r},{card_g},{card_b},0.92)"
    card_text = "#fafaf9"
    header_bg = "rgba(8,10,12,0.78)"
    muted_text = "rgba(250,250,249,0.88)"
    premium_brand = ""
    if pid == "premium":
        premium_brand = f"""
/* Premium store — brand stage, not catalog dump */
body[data-dna-style="{dna.style}"] .hero.has-hero-image {{
  position: relative; isolation: isolate;
}}
body[data-dna-style="{dna.style}"] .hero.has-hero-image::after {{
  content: ""; position: absolute; inset: 0; z-index: 0; pointer-events: none;
  background:
    linear-gradient(120deg, rgba({ir},{ig},{ib},0.45), transparent 55%),
    radial-gradient(ellipse 60% 50% at 80% 20%, rgba({ar},{ag},{ab},0.28), transparent 60%);
}}
body[data-dna-style="{dna.style}"] .hero .hero-copy,
body[data-dna-style="{dna.style}"] .hero .hero-inner,
body[data-dna-style="{dna.style}"] .hero h1 {{
  position: relative; z-index: 1;
}}
body[data-dna-style="{dna.style}"] .dna-atm {{ opacity: 0.92; }}
"""
    return f"""
/* Digital Creative Studio · Store Experience — site-parity (no white blocks) */
html {{ overflow-x: clip; }}
body[data-dna-style="{dna.style}"] {{
  --dna-accent: {accent};
  overflow-x: clip;
  background: {body_bg} !important;
  color: {card_text} !important;
}}
body[data-dna-style="{dna.style}"] .dna-atm {{ opacity: 0.94; z-index: -1; }}
body[data-dna-style="{dna.style}"] .hero.has-hero-image {{
  min-height: min({hero_min}, 920px);
}}
body[data-dna-style="{dna.style}"] .card,
body[data-dna-style="{dna.style}"] .product-card--premium,
body[data-dna-style="{dna.style}"] .review-card,
body[data-dna-style="{dna.style}"] .cart-summary,
body[data-dna-style="{dna.style}"] .offer-glass,
body[data-dna-style="{dna.style}"] .card-body {{
  background: {card_bg} !important;
  border: 1px solid rgba({ar},{ag},{ab},0.22) !important;
  color: {card_text} !important;
  backdrop-filter: blur(12px);
  box-shadow: 0 16px 40px rgba(0,0,0,0.32);
}}
body[data-dna-style="{dna.style}"] .review-card p,
body[data-dna-style="{dna.style}"] .review-card cite,
body[data-dna-style="{dna.style}"] .pdp-desc,
body[data-dna-style="{dna.style}"] .card-body p,
body[data-dna-style="{dna.style}"] .card-body h3,
body[data-dna-style="{dna.style}"] .card-body a,
body[data-dna-style="{dna.style}"] .specs,
body[data-dna-style="{dna.style}"] .specs li,
body[data-dna-style="{dna.style}"] .specs span {{
  color: {card_text} !important;
}}
body[data-dna-style="{dna.style}"] .card:hover {{
  transform: translateY(-5px);
  box-shadow: 0 22px 48px rgba({ar},{ag},{ab},0.22);
}}
body[data-dna-style="{dna.style}"] .site-header {{
  background: {header_bg} !important;
  backdrop-filter: blur(14px);
  position: sticky; top: 0; z-index: 30;
}}
body[data-dna-style="{dna.style}"] .brand,
body[data-dna-style="{dna.style}"] .brand-word,
body[data-dna-style="{dna.style}"] .page-title,
body[data-dna-style="{dna.style}"] h1,
body[data-dna-style="{dna.style}"] h2,
body[data-dna-style="{dna.style}"] h3,
body[data-dna-style="{dna.style}"] .card h3 {{
  color: {card_text} !important;
}}
body[data-dna-style="{dna.style}"] .muted,
body[data-dna-style="{dna.style}"] .review-card cite {{
  color: {muted_text} !important;
}}
body[data-dna-style="{dna.style}"] .card-media img {{
  opacity: 1 !important;
  visibility: visible !important;
  z-index: 2 !important;
  display: block !important;
  position: absolute !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  object-fit: cover !important;
}}
body[data-dna-style="{dna.style}"] .wrap {{
  max-width: 72rem; margin-inline: auto; padding-inline: 1.25rem; box-sizing: border-box;
}}
{premium_brand}
""" + _store_atm_css(ar, ag, ab, body_bg, premium=True)


def _store_atm_css(
    ar: int, ag: int, ab: int, surface: str, *, premium: bool = False
) -> str:
    illu = ""
    if premium:
        illu = f"""
.dna-atm__aurora--c {{
  left: 18%; bottom: -28%; width: 68vmax; height: 38vmax;
  background: radial-gradient(ellipse at center, rgba({ar},{ag},{ab},0.32), transparent 65%);
  animation: dnaAuroraDrift 26s ease-in-out infinite alternate;
  opacity: 0.42; filter: blur(64px); mix-blend-mode: multiply;
}}
.dna-atm__grid {{
  position: absolute; inset: 0; opacity: 0.18;
  background-image:
    linear-gradient(rgba(28,25,23,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(28,25,23,0.05) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: radial-gradient(ellipse 75% 65% at 50% 28%, black, transparent 78%);
  animation: dnaGridDrift 42s linear infinite;
}}
.dna-atm__illu {{
  position: absolute; inset: -10%; opacity: 0.48;
  background:
    radial-gradient(ellipse 28% 22% at 78% 18%, rgba({ar},{ag},{ab},0.2), transparent 70%),
    radial-gradient(ellipse 22% 30% at 12% 72%, rgba(201,184,166,0.18), transparent 68%);
  animation: dnaIlluDrift 48s ease-in-out infinite alternate;
  mix-blend-mode: multiply;
}}
.dna-atm__orb--d {{
  width: 20rem; height: 20rem; right: 16%; bottom: -4%;
  background: rgba({ar},{ag},{ab},0.2); animation-delay: -12s; opacity: 0.5;
  position: absolute; border-radius: 9999px; filter: blur(56px);
  animation: dnaOrbFloat 18s ease-in-out infinite;
}}
@keyframes dnaAuroraDrift {{
  0% {{ transform: translate(0,0) scale(1); }}
  100% {{ transform: translate(3%,-2%) scale(1.08); }}
}}
@keyframes dnaGridDrift {{
  0% {{ transform: translateY(0); }}
  100% {{ transform: translateY(28px); }}
}}
@keyframes dnaIlluDrift {{
  0% {{ transform: translate(0,0) rotate(0deg); }}
  100% {{ transform: translate(-1.5%,1%) rotate(2deg); }}
}}
"""
    return f"""
.dna-atm {{ pointer-events: none; position: fixed; inset: 0; z-index: -1; overflow: hidden; }}
.dna-atm__base {{
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba({ar},{ag},{ab},0.22), transparent 55%),
    linear-gradient(165deg, {surface}, color-mix(in srgb, rgb({ar},{ag},{ab}) 8%, {surface}));
}}
.dna-atm__mesh {{
  position: absolute; inset: -20%;
  background:
    radial-gradient(ellipse 45% 35% at 15% 20%, rgba({ar},{ag},{ab},0.28), transparent 60%),
    radial-gradient(ellipse 40% 30% at 88% 22%, rgba({ar},{ag},{ab},0.16), transparent 55%);
  animation: dnaMeshDrift 22s ease-in-out infinite alternate;
}}
.dna-atm__aurora {{
  position: absolute; width: 48vmax; height: 48vmax; border-radius: 40%;
  filter: blur(70px); opacity: 0.26; mix-blend-mode: multiply;
}}
.dna-atm__aurora--a {{
  left: -14%; top: -8%;
  background: conic-gradient(from 90deg, rgba({ar},{ag},{ab},0.45), transparent 60%);
  animation: dnaAuroraSpin 30s linear infinite;
}}
.dna-atm__aurora--b {{ right: -16%; top: 30%; animation: dnaAuroraSpin 38s linear infinite reverse; }}
.dna-atm__orb {{
  position: absolute; border-radius: 9999px; filter: blur(52px); opacity: 0.45;
  animation: dnaOrbFloat 18s ease-in-out infinite;
}}
.dna-atm__orb--a {{ width: 16rem; height: 16rem; left: -5%; top: 10%; background: rgba({ar},{ag},{ab},0.35); }}
.dna-atm__orb--b {{ width: 12rem; height: 12rem; right: -4%; top: 40%; background: rgba(201,184,166,0.3); animation-delay: -5s; }}
.dna-atm__orb--c {{ width: 11rem; height: 11rem; left: 42%; bottom: 6%; background: rgba({ar},{ag},{ab},0.22); animation-delay: -9s; }}
.dna-atm__particles {{ position: absolute; inset: 0; }}
.dna-atm__particle {{
  position: absolute; left: var(--sx); top: var(--sy);
  width: var(--size); height: var(--size); border-radius: 9999px;
  background: rgba({ar},{ag},{ab},0.65); box-shadow: 0 0 8px rgba({ar},{ag},{ab},0.4);
  animation: dnaParticle var(--dur) ease-in-out infinite; animation-delay: var(--delay); opacity: 0.4;
}}
.dna-atm__vignette {{
  position: absolute; inset: 0;
  background: radial-gradient(ellipse 70% 55% at 50% 40%, transparent 40%, rgba(255,255,255,0.2) 100%);
}}
body[data-dna-style] .site-header, body[data-dna-style] main, body[data-dna-style] .site-footer {{
  position: relative; z-index: 1;
}}
@keyframes dnaMeshDrift {{
  0% {{ transform: translate(0,0) scale(1); }}
  100% {{ transform: translate(-2.5%,2%) scale(1.06); }}
}}
@keyframes dnaAuroraSpin {{
  from {{ transform: rotate(0deg) scale(1); }}
  to {{ transform: rotate(360deg) scale(1.08); }}
}}
@keyframes dnaOrbFloat {{
  0%, 100% {{ transform: translate(0,0); }}
  50% {{ transform: translate(18px,-22px); }}
}}
@keyframes dnaParticle {{
  0%, 100% {{ transform: translate(0,0) scale(1); opacity: 0.25; }}
  50% {{ transform: translate(10px,-26px) scale(1.4); opacity: 0.9; }}
}}
@media (prefers-reduced-motion: reduce) {{
  .dna-atm__mesh, .dna-atm__aurora, .dna-atm__orb, .dna-atm__particle, .dna-atm__grid, .dna-atm__illu {{ animation: none !important; }}
}}
{illu}
"""


def validate_quality_floor_html(html: str, dna: DesignDNA | None = None) -> list[str]:
    failures: list[str] = []
    lower = (html or "").lower()
    if "data-dna-style=" not in lower:
        failures.append("missing_dna_style")
    if "data-dna-fp=" not in lower:
        failures.append("missing_dna_fingerprint")
    if 'data-dna-atmosphere="1"' not in lower and "dna-atm" not in lower:
        failures.append("missing_living_atmosphere")
    if dna is not None:
        treats = [t for _k, t in dna.section_treatments]
        failures.extend(validate_no_light_ladder(treats))
    return failures
