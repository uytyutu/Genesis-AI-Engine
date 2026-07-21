"""R2.2a — Hero Composer: composition library, not left/right CSS flips.

Niche restricts the allowlist; seed(business_name|package|niche) picks one layout.
Same inputs → same Hero. Different business → often a different composition.
"""

from __future__ import annotations

import hashlib
import html as html_lib
from dataclasses import dataclass

LAYOUT_IDS = ("A", "B", "C", "D", "E", "F")

# Niche limits the pool; seed chooses inside the pool (not one Hero per niche).
NICHE_LAYOUT_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "dental": ("A", "C", "E"),
    "auto": ("B", "D", "F"),
    "law": ("C", "A", "E"),
    "energy": ("A", "D", "E"),
    "beauty": ("E", "A", "C"),
    "green": ("A", "D", "E"),
    "computer": ("A", "B", "C"),
    "appliance": ("A", "B", "F"),
    "handwerk": ("B", "F", "A"),
    "generic": ("A", "B", "C"),
}


@dataclass(frozen=True)
class HeroComposition:
    layout_id: str
    html: str
    css: str
    embeds_stats: bool


def select_hero_layout(
    *,
    niche_id: str,
    business_name: str,
    package_id: str,
) -> str:
    """Deterministic layout pick from the niche allowlist."""
    niche = (niche_id or "generic").strip().lower() or "generic"
    pool = NICHE_LAYOUT_ALLOWLIST.get(niche) or NICHE_LAYOUT_ALLOWLIST["generic"]
    seed = f"{business_name.strip()}|{package_id.strip().lower()}|{niche}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def compose_hero(
    *,
    layout_id: str,
    business_name: str,
    headline: str,
    subtitle: str,
    cta_label: str,
    trust_points: tuple[str, ...] | list[str],
    benefits: tuple[str, ...] | list[str],
    hero_cta_extra: str,
    h1_class: str,
    hero_p_class: str,
    trust_class: str,
    btn_class: str,
    ui: dict[str, str],
    hero_photo: bool = True,
) -> HeroComposition:
    """Build Hero HTML + layout CSS. Strings must already be HTML-escaped where needed."""
    lid = layout_id if layout_id in LAYOUT_IDS else "A"
    esc = html_lib.escape
    trust_html = "".join(f'<span class="trust-pill">{esc(t)}</span>' for t in trust_points)
    adv = list(benefits)[:3]
    adv_html = "".join(f"<li>{esc(b)}</li>" for b in adv)
    kpi = _kpi_html(ui)
    photo = " has-photo" if hero_photo else ""
    img = (
        f'<img src="assets/hero.jpg" alt="{esc(business_name)}" '
        f'width="960" height="720" decoding="async">'
        if hero_photo
        else ""
    )

    builders = {
        "A": _layout_a,
        "B": _layout_b,
        "C": _layout_c,
        "D": _layout_d,
        "E": _layout_e,
        "F": _layout_f,
    }
    html, embeds_stats = builders[lid](
        photo=photo,
        img=img,
        headline=headline,
        subtitle=subtitle,
        trust_html=trust_html,
        trust_class=trust_class,
        h1_class=h1_class,
        hero_p_class=hero_p_class,
        btn_class=btn_class,
        cta=cta_label,
        hero_cta_extra=hero_cta_extra,
        adv_html=adv_html,
        kpi=kpi,
        business=esc(business_name),
    )
    return HeroComposition(
        layout_id=lid,
        html=html,
        css=_layout_css(lid),
        embeds_stats=embeds_stats,
    )


def _kpi_html(ui: dict[str, str]) -> str:
    esc = html_lib.escape
    return (
        f'<div class="hero-kpi"><strong>{esc(ui.get("stats_v1", "10+"))}</strong>'
        f'<span>{esc(ui.get("stats_n1", ""))}</span></div>'
        f'<div class="hero-kpi"><strong>{esc(ui.get("stats_v2", "24/7"))}</strong>'
        f'<span>{esc(ui.get("stats_n2", ""))}</span></div>'
        f'<div class="hero-kpi"><strong>{esc(ui.get("stats_v3", "100%"))}</strong>'
        f'<span>{esc(ui.get("stats_n3", ""))}</span></div>'
    )


def _layout_a(**kw: str) -> tuple[str, bool]:
    # Split clinical: copy + media column, trust, CTA, short advantages, soft deco.
    html = f"""
  <header class="hero hero-layout-A{kw['photo']}" data-hero-layout="A">
    <div class="hero-A-grid">
      <div class="hero-A-copy">
        <h1{kw['h1_class']}>{kw['headline']}</h1>
        <p{kw['hero_p_class']}>{kw['subtitle']}</p>
        <div{kw['trust_class']}>{kw['trust_html']}</div>
        <div class="hero-ctas">
          <a class="{kw['btn_class']}" href="#contact">{kw['cta']}</a>{kw['hero_cta_extra']}
        </div>
        <ul class="hero-adv">{kw['adv_html']}</ul>
      </div>
      <figure class="hero-A-media">
        <span class="hero-A-deco" aria-hidden="true"></span>
        {kw['img']}
      </figure>
    </div>
  </header>
"""
    return html, False


def _layout_b(**kw: str) -> tuple[str, bool]:
    # Full-bleed industrial: photo wash, strong CTA, floating KPIs, gradient band.
    html = f"""
  <header class="hero hero-layout-B{kw['photo']} hero-bleed" data-hero-layout="B">
    <div class="hero-B-stage">
      <div class="hero-B-copy">
        <h1{kw['h1_class']}>{kw['headline']}</h1>
        <p{kw['hero_p_class']}>{kw['subtitle']}</p>
        <div class="hero-ctas hero-B-ctas">
          <a class="{kw['btn_class']} hero-B-cta" href="#contact">{kw['cta']}</a>{kw['hero_cta_extra']}
        </div>
      </div>
      <aside class="hero-B-kpis" aria-label="stats">{kw['kpi']}</aside>
    </div>
    <div class="hero-B-band" aria-hidden="true"></div>
  </header>
"""
    return html, True


def _layout_c(**kw: str) -> tuple[str, bool]:
    # Airy trust: whitespace, portrait, thin accent rule, minimal chrome.
    html = f"""
  <header class="hero hero-layout-C{kw['photo']}" data-hero-layout="C">
    <div class="hero-C-wrap">
      <div class="hero-C-rule" aria-hidden="true"></div>
      <figure class="hero-C-portrait">{kw['img']}</figure>
      <div class="hero-C-copy">
        <h1{kw['h1_class']}>{kw['headline']}</h1>
        <p{kw['hero_p_class']}>{kw['subtitle']}</p>
        <div{kw['trust_class']}>{kw['trust_html']}</div>
        <div class="hero-ctas">
          <a class="{kw['btn_class']}" href="#contact">{kw['cta']}</a>{kw['hero_cta_extra']}
        </div>
      </div>
    </div>
  </header>
"""
    return html, False


def _layout_d(**kw: str) -> tuple[str, bool]:
    # Immersive background + glass panel + floating KPI cards.
    html = f"""
  <header class="hero hero-layout-D{kw['photo']} hero-bleed" data-hero-layout="D">
    <div class="hero-D-panel">
      <h1{kw['h1_class']}>{kw['headline']}</h1>
      <p{kw['hero_p_class']}>{kw['subtitle']}</p>
      <div{kw['trust_class']}>{kw['trust_html']}</div>
      <div class="hero-ctas">
        <a class="{kw['btn_class']}" href="#contact">{kw['cta']}</a>{kw['hero_cta_extra']}
      </div>
    </div>
    <aside class="hero-D-float" aria-label="stats">{kw['kpi']}</aside>
  </header>
"""
    return html, True


def _layout_e(**kw: str) -> tuple[str, bool]:
    # Soft magazine: large circular media, wash gradient, round chips.
    html = f"""
  <header class="hero hero-layout-E{kw['photo']}" data-hero-layout="E">
    <div class="hero-E-stage">
      <figure class="hero-E-orb">
        <span class="hero-E-ring" aria-hidden="true"></span>
        {kw['img']}
      </figure>
      <div class="hero-E-wash" aria-hidden="true"></div>
      <div class="hero-E-copy">
        <h1{kw['h1_class']}>{kw['headline']}</h1>
        <p{kw['hero_p_class']}>{kw['subtitle']}</p>
        <ul class="hero-E-chips">{kw['adv_html']}</ul>
        <div class="hero-ctas">
          <a class="{kw['btn_class']}" href="#contact">{kw['cta']}</a>{kw['hero_cta_extra']}
        </div>
        <div{kw['trust_class']}>{kw['trust_html']}</div>
      </div>
    </div>
  </header>
"""
    return html, False


def _layout_f(**kw: str) -> tuple[str, bool]:
    # Banner band + overlapping content card + stats rail (not a B overlay).
    html = f"""
  <header class="hero hero-layout-F{kw['photo']}" data-hero-layout="F">
    <div class="hero-F-banner">{kw['img']}</div>
    <div class="hero-F-stack">
      <div class="hero-F-card">
        <h1{kw['h1_class']}>{kw['headline']}</h1>
        <p{kw['hero_p_class']}>{kw['subtitle']}</p>
        <div class="hero-ctas">
          <a class="{kw['btn_class']}" href="#contact">{kw['cta']}</a>{kw['hero_cta_extra']}
        </div>
      </div>
      <div class="hero-F-rail" aria-label="stats">{kw['kpi']}</div>
    </div>
  </header>
"""
    return html, True


def _layout_css(layout_id: str) -> str:
    # Shared reset so tier CSS (center / left padding) cannot collapse compositions.
    shared = """
    /* Hero Composer R2.2a */
    body[data-hero-layout] .hero {
      text-align: left;
      display: block;
      place-items: unset;
      min-height: 0;
      padding: 0;
      background-size: cover;
      background-position: center;
    }
    body[data-hero-layout] .hero h1 { margin-inline: 0; max-width: none; }
    body[data-hero-layout] .hero p.lead { margin-inline: 0; }
    body[data-hero-layout] .trust-row,
    body[data-hero-layout] .hero-ctas { justify-content: flex-start; }
    .hero-kpi strong { display: block; font-size: clamp(1.5rem, 3vw, 2.25rem); letter-spacing: -0.03em; }
    .hero-kpi span { font-size: 0.8rem; opacity: 0.85; }
"""
    mobile = {
        "A": """
    @media (max-width: 820px) {
      .hero-A-grid { grid-template-columns: 1fr !important; }
    }
""",
        "B": """
    @media (max-width: 820px) {
      .hero-B-stage { grid-template-columns: 1fr !important; }
      .hero-B-kpis { position: static !important; display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
    }
""",
        "C": """
    @media (max-width: 820px) {
      .hero-C-wrap { grid-template-columns: 1fr !important; }
    }
""",
        "D": """
    @media (max-width: 820px) {
      .hero-D-float { position: static !important; display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
    }
""",
        "E": """
    @media (max-width: 820px) {
      .hero-E-stage { grid-template-columns: 1fr !important; }
      .hero-E-orb { width: min(72vw, 280px) !important; height: min(72vw, 280px) !important; margin: 0 auto 1.5rem; }
    }
""",
        "F": """
    @media (max-width: 820px) {
      .hero-F-card { margin-top: -2rem !important; }
    }
""",
    }
    sheets = {
        "A": """
    body[data-hero-layout="A"] .hero.hero-layout-A {
      background: var(--surface, #f0f9ff);
      color: var(--ink, #0c4a6e);
      padding: 2.5rem 1.25rem 3rem;
    }
    body[data-hero-layout="A"] .hero.hero-layout-A.has-photo {
      background-image: none;
      background: var(--surface, #f0f9ff);
    }
    .hero-A-grid {
      max-width: 1120px; margin: 0 auto;
      display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 2rem; align-items: center;
    }
    .hero-A-copy .lead { color: var(--muted, #64748b); max-width: 34rem; }
    .hero-A-copy .trust-pill {
      background: #fff; color: var(--pd, #0369a1); border-color: var(--line, #bae6fd);
    }
    .hero-adv {
      list-style: none; display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1.5rem;
    }
    .hero-adv li {
      background: #fff; border: 1px solid var(--line, #e2e8f0); border-radius: 999px;
      padding: 0.4rem 0.85rem; font-size: 0.85rem; font-weight: 600; color: var(--pd);
    }
    .hero-A-media {
      position: relative; margin: 0; border-radius: calc(var(--card-radius, 18px) + 4px);
      overflow: hidden; aspect-ratio: 4 / 5; background: var(--line, #e2e8f0);
      box-shadow: var(--shadow, 0 16px 40px rgba(15,23,42,0.12));
    }
    .hero-A-media img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .hero-A-deco {
      position: absolute; z-index: 0; width: 42%; height: 42%; right: -8%; bottom: -10%;
      border-radius: 50%; background: var(--acc, #e0f2fe); opacity: 0.9;
    }
""",
        "B": """
    body[data-hero-layout="B"] .hero.hero-layout-B {
      min-height: 78vh; color: #fff; position: relative;
      display: flex; flex-direction: column; justify-content: flex-end;
    }
    body[data-hero-layout="B"] .hero.hero-layout-B.has-photo {
      background-image:
        linear-gradient(105deg, rgba(0,0,0,.88) 0%, rgba(0,0,0,.35) 55%, rgba(185,28,28,.45) 100%),
        url("assets/hero.jpg");
    }
    .hero-B-stage {
      position: relative; z-index: 2; max-width: 1180px; width: 100%; margin: 0 auto;
      padding: 4rem 1.5rem 3rem;
      display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 2rem; align-items: end;
    }
    .hero-B-copy h1 { font-size: clamp(2.2rem, 5vw, 3.6rem); text-transform: uppercase; letter-spacing: -0.04em; }
    .hero-B-cta { font-size: 1.05rem; padding: 1rem 2.25rem; border-radius: 6px; }
    .hero-B-kpis {
      display: grid; gap: 0.85rem;
    }
    .hero-B-kpis .hero-kpi {
      background: rgba(0,0,0,.55); border: 1px solid rgba(255,255,255,.18);
      border-left: 4px solid var(--acc, #f87171); padding: 0.85rem 1rem;
    }
    .hero-B-kpis .hero-kpi strong { color: var(--acc, #f87171); }
    .hero-B-band {
      height: 10px; background: linear-gradient(90deg, var(--pd), var(--p), var(--acc));
    }
""",
        "C": """
    body[data-hero-layout="C"] .hero.hero-layout-C {
      background: #fff; color: var(--ink, #0f172a);
      padding: 4.5rem 1.5rem 5.5rem;
    }
    body[data-hero-layout="C"] .hero.hero-layout-C.has-photo {
      background-image: none; background: #fff;
    }
    .hero-C-wrap {
      max-width: 820px; margin: 0 auto;
      display: grid; grid-template-columns: 200px 1fr; gap: 2.75rem; align-items: start;
    }
    .hero-C-rule {
      grid-column: 1 / -1; width: 4rem; height: 2px; background: var(--acc, #c9a227);
    }
    .hero-C-portrait {
      margin: 0; width: 200px; height: 260px; overflow: hidden;
      border-radius: 4px; background: var(--surface, #f8fafc);
      box-shadow: 0 8px 24px rgba(15,23,42,0.08);
    }
    .hero-C-portrait img { width: 100%; height: 100%; object-fit: cover; display: block; filter: grayscale(18%); }
    .hero-C-copy h1 { font-weight: 600; letter-spacing: 0.01em; font-size: clamp(1.85rem, 3.5vw, 2.6rem); }
    .hero-C-copy .lead { max-width: 28rem; color: var(--muted); font-size: 1.05rem; line-height: 1.75; }
    .hero-layout-C .trust-pill {
      background: transparent; color: var(--pd); border: 0; border-bottom: 1px solid var(--acc);
      border-radius: 0; padding: 0.15rem 0;
    }
    body[data-hero-layout="C"] .hero .btn {
      background: var(--pd); color: #fff; border-radius: 4px; box-shadow: none;
    }
""",
        "D": """
    body[data-hero-layout="D"] .hero.hero-layout-D {
      min-height: 82vh; position: relative; color: #fff;
      display: grid; align-items: center; padding: 3.5rem 1.25rem;
    }
    body[data-hero-layout="D"] .hero.hero-layout-D.has-photo {
      background-image:
        linear-gradient(160deg, rgba(20,83,45,.55), rgba(22,163,74,.25) 45%, rgba(0,0,0,.35)),
        url("assets/hero.jpg");
    }
    .hero-D-panel {
      position: relative; z-index: 2; max-width: 28rem;
      margin-left: max(1rem, 8vw);
      padding: 1.75rem 1.5rem;
      border-radius: calc(var(--radius, 18px));
      background: rgba(255,255,255,0.14);
      border: 1px solid rgba(255,255,255,0.28);
      backdrop-filter: blur(10px);
    }
    .hero-D-float {
      position: absolute; right: max(1rem, 6vw); top: 18%;
      z-index: 2; display: grid; gap: 0.75rem; width: min(220px, 40vw);
    }
    .hero-D-float .hero-kpi {
      background: rgba(255,255,255,0.92); color: var(--ink, #14532d);
      border-radius: 16px; padding: 0.9rem 1rem;
      box-shadow: 0 14px 32px rgba(0,0,0,0.18);
    }
    .hero-D-float .hero-kpi strong { color: var(--p, #16a34a); }
""",
        "E": """
    body[data-hero-layout="E"] .hero.hero-layout-E {
      background: linear-gradient(145deg, var(--surface, #fdf2f8), #fff 55%, var(--acc, #fbcfe8));
      color: var(--ink, #500724);
      padding: 3rem 1.25rem 3.5rem;
    }
    body[data-hero-layout="E"] .hero.hero-layout-E.has-photo {
      background-image: none;
      background: linear-gradient(145deg, var(--surface, #fdf2f8), #fff 55%, var(--acc, #fbcfe8));
    }
    .hero-E-stage {
      max-width: 1080px; margin: 0 auto;
      display: grid; grid-template-columns: 0.85fr 1.15fr; gap: 2rem; align-items: center;
      position: relative;
    }
    .hero-E-orb {
      position: relative; margin: 0;
      width: min(100%, 360px); height: min(100vw, 360px);
      border-radius: 50%; overflow: hidden;
      box-shadow: var(--shadow, 0 18px 40px rgba(190,24,93,0.18));
    }
    .hero-E-orb img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .hero-E-ring {
      position: absolute; inset: -14px; border-radius: 50%;
      border: 2px dashed color-mix(in srgb, var(--p) 45%, transparent);
      pointer-events: none;
    }
    .hero-E-wash {
      position: absolute; width: 40%; height: 55%; right: 4%; top: 8%;
      border-radius: 40% 60% 55% 45%; background: color-mix(in srgb, var(--acc) 55%, transparent);
      filter: blur(2px); z-index: 0; pointer-events: none;
    }
    .hero-E-copy { position: relative; z-index: 1; }
    .hero-E-chips {
      list-style: none; display: flex; flex-wrap: wrap; gap: 0.55rem; margin: 1rem 0 1.25rem;
    }
    .hero-E-chips li {
      background: #fff; border-radius: 999px; padding: 0.45rem 0.95rem;
      font-size: 0.85rem; box-shadow: 0 6px 16px rgba(0,0,0,0.06);
    }
    body[data-hero-layout="E"] .hero .trust-pill {
      background: rgba(255,255,255,0.7); color: var(--pd); border-color: transparent;
    }
""",
        "F": """
    body[data-hero-layout="F"] .hero.hero-layout-F {
      background: #0a0a0a; color: #fff; padding-bottom: 0;
    }
    body[data-hero-layout="F"] .hero.hero-layout-F.has-photo {
      background-image: none; background: #0a0a0a;
    }
    .hero-F-banner {
      margin: 0; height: clamp(220px, 38vw, 420px); overflow: hidden;
      background: linear-gradient(120deg, #1c1917, var(--pd));
    }
    .hero-F-banner img {
      width: 100%; height: 100%; object-fit: cover; display: block;
      filter: contrast(1.05) saturate(1.05);
    }
    .hero-F-stack {
      max-width: 1000px; margin: 0 auto; padding: 0 1.25rem 0;
      position: relative; z-index: 2;
    }
    .hero-F-card {
      margin-top: -4.5rem;
      background: #111; border: 1px solid rgba(255,255,255,0.12);
      border-radius: 8px; padding: 1.75rem 1.5rem 1.5rem;
      box-shadow: 0 24px 48px rgba(0,0,0,0.45);
    }
    .hero-F-card h1 { text-transform: uppercase; letter-spacing: -0.03em; }
    .hero-F-rail {
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 0;
      margin: 0 0 0; background: #000; border: 1px solid rgba(255,255,255,0.1);
      border-top: 0; border-radius: 0 0 8px 8px; overflow: hidden;
    }
    .hero-F-rail .hero-kpi {
      padding: 1rem 1.1rem; border-right: 1px solid rgba(255,255,255,0.1);
    }
    .hero-F-rail .hero-kpi:last-child { border-right: 0; }
    .hero-F-rail .hero-kpi strong { color: var(--acc, #f87171); }
""",
    }
    return shared + sheets.get(layout_id, sheets["A"]) + mobile.get(layout_id, mobile["A"])
