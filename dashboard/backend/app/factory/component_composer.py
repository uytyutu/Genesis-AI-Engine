"""R2.2b — Component Composer: one page language per Component Profile.

Hero restricts the allowlist; seed(business|package|niche|hero) picks one profile.
All section families on the page come from that single profile (no mix-and-match).
"""

from __future__ import annotations

import hashlib
import html as html_lib
from dataclasses import dataclass
from typing import Callable

PROFILE_IDS = ("A", "B", "C")

# Hero layout → compatible Component Profiles (CEO map).
HERO_PROFILE_COMPAT: dict[str, tuple[str, ...]] = {
    "A": ("A", "C"),
    "B": ("B",),
    "C": ("C", "A"),
    "D": ("B", "C"),
    "E": ("A",),
    "F": ("B",),
}


@dataclass(frozen=True)
class ComponentProfile:
    """Full page language — HTML compositions, not CSS tokens alone."""

    id: str
    cards: str
    buttons: str
    benefits: str
    reviews: str
    faq: str
    gallery: str
    cta: str
    label: str


# Registry — add Profile D without changing selection logic.
COMPONENT_PROFILES: dict[str, ComponentProfile] = {
    "A": ComponentProfile(
        id="A",
        cards="glass",
        buttons="pill",
        benefits="circles",
        reviews="float",
        faq="rounded",
        gallery="masonry",
        cta="glass",
        label="Glass / soft rhythm",
    ),
    "B": ComponentProfile(
        id="B",
        cards="solid",
        buttons="square",
        benefits="timeline",
        reviews="quote",
        faq="twocol",
        gallery="grid",
        cta="solid_bar",
        label="Solid / industrial density",
    ),
    "C": ComponentProfile(
        id="C",
        cards="minimal",
        buttons="outline",
        benefits="editorial",
        reviews="rating",
        faq="accordion",
        gallery="feature_first",
        cta="editorial",
        label="Minimal / editorial",
    ),
}


@dataclass(frozen=True)
class ComposedSections:
    profile_id: str
    btn_class: str
    services_html: str
    benefits_html: str
    faq_html: str
    gallery_html: str
    reviews_html: str
    mid_cta_html: str
    css: str


def select_component_profile(
    *,
    hero_layout: str,
    business_name: str,
    package_id: str,
    niche_id: str,
) -> str:
    """Deterministic profile from Hero-compatible pool."""
    hero = (hero_layout or "A").strip().upper()
    if hero not in HERO_PROFILE_COMPAT:
        hero = "A"
    pool = HERO_PROFILE_COMPAT[hero]
    niche = (niche_id or "generic").strip().lower() or "generic"
    seed = (
        f"{business_name.strip()}|{package_id.strip().lower()}|"
        f"{niche}|{hero}"
    )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    # Offset digest so profile pick is independent of hero pick (same prefix seed).
    return pool[int(digest[8:16], 16) % len(pool)]


def get_component_profile(profile_id: str) -> ComponentProfile:
    pid = (profile_id or "A").strip().upper()
    return COMPONENT_PROFILES.get(pid) or COMPONENT_PROFILES["A"]


def button_class_for_profile(profile: ComponentProfile, *, css_motion: bool) -> str:
    base = "btn cta-button" if css_motion else "btn"
    return f"{base} btn-{profile.buttons}"


def compose_page_sections(
    *,
    profile_id: str,
    analysis_services: list[str],
    service_descriptions: tuple[str, ...] | list[str],
    benefits: tuple[str, ...] | list[str],
    ui: dict[str, str],
    business_name: str,
    why_title: str,
    section_class: str,
    btn_class: str,
    include_faq: bool,
    include_reviews: bool,
    include_mid_cta: bool,
    gallery_paths: list[str],
) -> ComposedSections:
    profile = get_component_profile(profile_id)
    esc = html_lib.escape
    sec = section_class
    business = esc(business_name)

    services = _CARD_RENDERERS[profile.cards](
        analysis_services, service_descriptions, ui, sec
    )
    benefits_html = _BENEFIT_RENDERERS[profile.benefits](benefits, why_title, sec)
    faq_html = (
        _FAQ_RENDERERS[profile.faq](ui, sec) if include_faq else ""
    )
    gallery_html = (
        _GALLERY_RENDERERS[profile.gallery](gallery_paths, ui, business, sec)
        if gallery_paths
        else ""
    )
    reviews_html = (
        _REVIEW_RENDERERS[profile.reviews](ui, sec) if include_reviews else ""
    )
    mid_cta_html = (
        _CTA_RENDERERS[profile.cta](ui, btn_class, sec) if include_mid_cta else ""
    )

    return ComposedSections(
        profile_id=profile.id,
        btn_class=btn_class,
        services_html=services,
        benefits_html=benefits_html,
        faq_html=faq_html,
        gallery_html=gallery_html,
        reviews_html=reviews_html,
        mid_cta_html=mid_cta_html,
        css=_profile_css(profile),
    )


# --- Family registries (extend by adding a key; no selection if/else) ----------

def _cards_glass(
    services: list[str],
    descriptions: tuple[str, ...] | list[str],
    ui: dict[str, str],
    sec: str,
) -> str:
    esc = html_lib.escape
    descs = list(descriptions) + [""] * max(0, len(services) - len(descriptions))
    cards = "".join(
        f'<li class="svc-card svc-glass"><h3>{esc(t)}</h3>'
        f'<p class="service-desc">{esc(d)}</p></li>'
        for t, d in zip(services, descs)
    )
    return f"""
  <section class="{sec} services-block" id="services" data-comp-family="cards" data-comp-variant="glass">
    <h2>{esc(ui['services'])}</h2>
    <ul class="services services-glass">{cards}</ul>
  </section>
"""


def _cards_solid(
    services: list[str],
    descriptions: tuple[str, ...] | list[str],
    ui: dict[str, str],
    sec: str,
) -> str:
    esc = html_lib.escape
    descs = list(descriptions) + [""] * max(0, len(services) - len(descriptions))
    cards = "".join(
        f'<li class="svc-card svc-solid"><span class="svc-accent" aria-hidden="true"></span>'
        f'<h3>{esc(t)}</h3><p class="service-desc">{esc(d)}</p></li>'
        for t, d in zip(services, descs)
    )
    return f"""
  <section class="{sec} services-block" id="services" data-comp-family="cards" data-comp-variant="solid">
    <h2>{esc(ui['services'])}</h2>
    <ul class="services services-solid">{cards}</ul>
  </section>
"""


def _cards_minimal(
    services: list[str],
    descriptions: tuple[str, ...] | list[str],
    ui: dict[str, str],
    sec: str,
) -> str:
    esc = html_lib.escape
    descs = list(descriptions) + [""] * max(0, len(services) - len(descriptions))
    cards = "".join(
        f'<li class="svc-card svc-minimal"><h3>{esc(t)}</h3>'
        f'<p class="service-desc">{esc(d)}</p></li>'
        for t, d in zip(services, descs)
    )
    return f"""
  <section class="{sec} services-block" id="services" data-comp-family="cards" data-comp-variant="minimal">
    <h2>{esc(ui['services'])}</h2>
    <ul class="services services-minimal">{cards}</ul>
  </section>
"""


_CARD_RENDERERS: dict[str, Callable[..., str]] = {
    "glass": _cards_glass,
    "solid": _cards_solid,
    "minimal": _cards_minimal,
}


def _benefits_circles(
    benefits: tuple[str, ...] | list[str], why_title: str, sec: str
) -> str:
    esc = html_lib.escape
    items = "".join(
        f'<li class="ben-circle"><span class="ben-dot" aria-hidden="true"></span>'
        f'<p>{esc(b)}</p></li>'
        for b in benefits
    )
    return f"""
  <section class="{sec} benefits" id="benefits" data-comp-family="benefits" data-comp-variant="circles">
    <h2>{why_title}</h2>
    <ul class="ben-circles">{items}</ul>
  </section>
"""


def _benefits_timeline(
    benefits: tuple[str, ...] | list[str], why_title: str, sec: str
) -> str:
    esc = html_lib.escape
    items = "".join(
        f'<li class="ben-step"><span class="ben-n">{i}</span><p>{esc(b)}</p></li>'
        for i, b in enumerate(benefits, start=1)
    )
    return f"""
  <section class="{sec} benefits" id="benefits" data-comp-family="benefits" data-comp-variant="timeline">
    <h2>{why_title}</h2>
    <ol class="ben-timeline">{items}</ol>
  </section>
"""


def _benefits_editorial(
    benefits: tuple[str, ...] | list[str], why_title: str, sec: str
) -> str:
    esc = html_lib.escape
    items = "".join(f"<li>{esc(b)}</li>" for b in benefits)
    return f"""
  <section class="{sec} benefits" id="benefits" data-comp-family="benefits" data-comp-variant="editorial">
    <h2>{why_title}</h2>
    <div class="ben-editorial">
      <ul class="ben-editorial-list">{items}</ul>
    </div>
  </section>
"""


_BENEFIT_RENDERERS: dict[str, Callable[..., str]] = {
    "circles": _benefits_circles,
    "timeline": _benefits_timeline,
    "editorial": _benefits_editorial,
}


def _faq_rounded(ui: dict[str, str], sec: str) -> str:
    esc = html_lib.escape
    return f"""
  <section class="{sec}" id="faq" data-comp-family="faq" data-comp-variant="rounded">
    <h2>{esc(ui['faq_title'])}</h2>
    <div class="faq-rounded">
      <article class="faq-bubble"><h3>{esc(ui['faq_q1'])}</h3><p>{esc(ui['faq_a1'])}</p></article>
      <article class="faq-bubble"><h3>{esc(ui['faq_q2'])}</h3><p>{esc(ui['faq_a2'])}</p></article>
      <article class="faq-bubble"><h3>{esc(ui['faq_q3'])}</h3><p>{esc(ui['faq_a3'])}</p></article>
    </div>
  </section>
"""


def _faq_twocol(ui: dict[str, str], sec: str) -> str:
    esc = html_lib.escape
    return f"""
  <section class="{sec}" id="faq" data-comp-family="faq" data-comp-variant="twocol">
    <h2>{esc(ui['faq_title'])}</h2>
    <div class="faq-twocol">
      <article class="faq-panel"><h3>{esc(ui['faq_q1'])}</h3><p>{esc(ui['faq_a1'])}</p></article>
      <article class="faq-panel"><h3>{esc(ui['faq_q2'])}</h3><p>{esc(ui['faq_a2'])}</p></article>
      <article class="faq-panel faq-span"><h3>{esc(ui['faq_q3'])}</h3><p>{esc(ui['faq_a3'])}</p></article>
    </div>
  </section>
"""


def _faq_accordion(ui: dict[str, str], sec: str) -> str:
    esc = html_lib.escape
    return f"""
  <section class="{sec}" id="faq" data-comp-family="faq" data-comp-variant="accordion">
    <h2>{esc(ui['faq_title'])}</h2>
    <div class="faq-accordion">
      <details class="faq-acc" open><summary>{esc(ui['faq_q1'])}</summary><p>{esc(ui['faq_a1'])}</p></details>
      <details class="faq-acc"><summary>{esc(ui['faq_q2'])}</summary><p>{esc(ui['faq_a2'])}</p></details>
      <details class="faq-acc"><summary>{esc(ui['faq_q3'])}</summary><p>{esc(ui['faq_a3'])}</p></details>
    </div>
  </section>
"""


_FAQ_RENDERERS: dict[str, Callable[..., str]] = {
    "rounded": _faq_rounded,
    "twocol": _faq_twocol,
    "accordion": _faq_accordion,
}


def _reviews_float(ui: dict[str, str], sec: str) -> str:
    esc = html_lib.escape
    return f"""
  <section class="{sec} testimonials" id="testimonials" data-comp-family="reviews" data-comp-variant="float">
    <h2>{esc(ui['reviews'])}</h2>
    <p class="muted">{esc(ui['reviews_muted'])}</p>
    <div class="rev-float">
      <blockquote class="rev-card rev-float-a"><p>{esc(ui['t1'])}</p><cite>{esc(ui['t1_cite'])}</cite></blockquote>
      <blockquote class="rev-card rev-float-b"><p>{esc(ui['t2'])}</p><cite>{esc(ui['t2_cite'])}</cite></blockquote>
      <blockquote class="rev-card rev-float-c"><p>{esc(ui['t3'])}</p><cite>{esc(ui['t3_cite'])}</cite></blockquote>
    </div>
  </section>
"""


def _reviews_quote(ui: dict[str, str], sec: str) -> str:
    esc = html_lib.escape
    return f"""
  <section class="{sec} testimonials" id="testimonials" data-comp-family="reviews" data-comp-variant="quote">
    <h2>{esc(ui['reviews'])}</h2>
    <p class="muted">{esc(ui['reviews_muted'])}</p>
    <div class="rev-quotes">
      <blockquote class="rev-quote"><span class="rev-mark" aria-hidden="true">“</span><p>{esc(ui['t1'])}</p><cite>{esc(ui['t1_cite'])}</cite></blockquote>
      <blockquote class="rev-quote"><span class="rev-mark" aria-hidden="true">“</span><p>{esc(ui['t2'])}</p><cite>{esc(ui['t2_cite'])}</cite></blockquote>
      <blockquote class="rev-quote"><span class="rev-mark" aria-hidden="true">“</span><p>{esc(ui['t3'])}</p><cite>{esc(ui['t3_cite'])}</cite></blockquote>
    </div>
  </section>
"""


def _reviews_rating(ui: dict[str, str], sec: str) -> str:
    esc = html_lib.escape
    stars = '<span class="rev-stars" aria-hidden="true">★★★★★</span>'
    return f"""
  <section class="{sec} testimonials" id="testimonials" data-comp-family="reviews" data-comp-variant="rating">
    <h2>{esc(ui['reviews'])}</h2>
    <p class="muted">{esc(ui['reviews_muted'])}</p>
    <div class="rev-rating-grid">
      <blockquote class="rev-rate">{stars}<p>{esc(ui['t1'])}</p><cite>{esc(ui['t1_cite'])}</cite></blockquote>
      <blockquote class="rev-rate">{stars}<p>{esc(ui['t2'])}</p><cite>{esc(ui['t2_cite'])}</cite></blockquote>
      <blockquote class="rev-rate">{stars}<p>{esc(ui['t3'])}</p><cite>{esc(ui['t3_cite'])}</cite></blockquote>
    </div>
  </section>
"""


_REVIEW_RENDERERS: dict[str, Callable[..., str]] = {
    "float": _reviews_float,
    "quote": _reviews_quote,
    "rating": _reviews_rating,
}


def _gallery_masonry(
    paths: list[str], ui: dict[str, str], business: str, sec: str
) -> str:
    esc = html_lib.escape
    figs = "\n".join(
        f'      <figure class="gal-item"><img src="{esc(p)}" alt="{business}" loading="lazy"></figure>'
        for p in paths
    )
    return f"""
  <section class="{sec} client-gallery" id="gallery" data-comp-family="gallery" data-comp-variant="masonry">
    <h2>{esc(ui.get('gallery_title') or 'Galerie')}</h2>
    <p class="muted">{esc(ui.get('gallery_muted') or '')}</p>
    <div class="gal-masonry">{figs}
    </div>
  </section>
"""


def _gallery_grid(
    paths: list[str], ui: dict[str, str], business: str, sec: str
) -> str:
    esc = html_lib.escape
    figs = "\n".join(
        f'      <figure class="gal-cell"><img src="{esc(p)}" alt="{business}" loading="lazy"></figure>'
        for p in paths
    )
    return f"""
  <section class="{sec} client-gallery" id="gallery" data-comp-family="gallery" data-comp-variant="grid">
    <h2>{esc(ui.get('gallery_title') or 'Galerie')}</h2>
    <p class="muted">{esc(ui.get('gallery_muted') or '')}</p>
    <div class="gal-grid">{figs}
    </div>
  </section>
"""


def _gallery_feature_first(
    paths: list[str], ui: dict[str, str], business: str, sec: str
) -> str:
    esc = html_lib.escape
    first, rest = paths[0], paths[1:]
    side = "\n".join(
        f'      <figure class="gal-side"><img src="{esc(p)}" alt="{business}" loading="lazy"></figure>'
        for p in rest
    ) or f'      <figure class="gal-side gal-side-empty" aria-hidden="true"></figure>'
    return f"""
  <section class="{sec} client-gallery" id="gallery" data-comp-family="gallery" data-comp-variant="feature_first">
    <h2>{esc(ui.get('gallery_title') or 'Galerie')}</h2>
    <p class="muted">{esc(ui.get('gallery_muted') or '')}</p>
    <div class="gal-feature">
      <figure class="gal-hero"><img src="{esc(first)}" alt="{business}" loading="lazy"></figure>
      <div class="gal-side-col">{side}
      </div>
    </div>
  </section>
"""


_GALLERY_RENDERERS: dict[str, Callable[..., str]] = {
    "masonry": _gallery_masonry,
    "grid": _gallery_grid,
    "feature_first": _gallery_feature_first,
}


def _cta_glass(ui: dict[str, str], btn_class: str, sec: str) -> str:
    esc = html_lib.escape
    return f"""
  <section class="mid-cta mid-cta-glass" id="mid-cta" data-comp-family="cta" data-comp-variant="glass">
    <div class="mid-cta-inner">
      <h2>{esc(ui['mid_cta_title'])}</h2>
      <a class="{btn_class}" href="#contact">{esc(ui['mid_cta_btn'])}</a>
    </div>
  </section>
"""


def _cta_solid_bar(ui: dict[str, str], btn_class: str, sec: str) -> str:
    esc = html_lib.escape
    return f"""
  <section class="mid-cta mid-cta-solid" id="mid-cta" data-comp-family="cta" data-comp-variant="solid_bar">
    <h2>{esc(ui['mid_cta_title'])}</h2>
    <a class="{btn_class}" href="#contact">{esc(ui['mid_cta_btn'])}</a>
  </section>
"""


def _cta_editorial(ui: dict[str, str], btn_class: str, sec: str) -> str:
    esc = html_lib.escape
    return f"""
  <section class="mid-cta mid-cta-editorial" id="mid-cta" data-comp-family="cta" data-comp-variant="editorial">
    <div class="mid-cta-rule" aria-hidden="true"></div>
    <h2>{esc(ui['mid_cta_title'])}</h2>
    <a class="{btn_class}" href="#contact">{esc(ui['mid_cta_btn'])}</a>
  </section>
"""


_CTA_RENDERERS: dict[str, Callable[..., str]] = {
    "glass": _cta_glass,
    "solid_bar": _cta_solid_bar,
    "editorial": _cta_editorial,
}


def _profile_css(profile: ComponentProfile) -> str:
    """Profile language CSS — scoped by data-comp-profile."""
    pid = profile.id
    shared = f"""
    /* Component Composer R2.2b — Profile {pid}: {profile.label} */
    body[data-comp-profile="{pid}"] .btn-{profile.buttons} {{ }}
    body[data-comp-profile] .btn-pill {{ border-radius: 999px; }}
    body[data-comp-profile] .btn-square {{ border-radius: 6px; }}
    body[data-comp-profile] .btn-outline {{
      background: transparent; color: inherit; border: 2px solid currentColor;
      box-shadow: none;
    }}
    body[data-comp-profile="{pid}"] .hero .btn-outline {{
      color: #fff; border-color: rgba(255,255,255,0.9);
    }}
"""
    sheets = {
        "A": """
    body[data-comp-profile="A"] .services-glass {
      display: grid; gap: 1.25rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      list-style: none;
    }
    body[data-comp-profile="A"] .svc-glass {
      background: rgba(255,255,255,0.55); border: 1px solid rgba(255,255,255,0.7);
      border-radius: 22px; padding: 1.5rem 1.35rem;
      backdrop-filter: blur(10px); box-shadow: 0 16px 40px rgba(15,23,42,0.08);
    }
    body[data-comp-profile="A"] .ben-circles {
      list-style: none; display: grid; gap: 1.25rem;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    }
    body[data-comp-profile="A"] .ben-circle {
      text-align: center; padding: 1.25rem 1rem;
      background: #fff; border-radius: 24px; box-shadow: 0 10px 28px rgba(15,23,42,0.06);
    }
    body[data-comp-profile="A"] .ben-dot {
      display: block; width: 2.75rem; height: 2.75rem; margin: 0 auto 0.85rem;
      border-radius: 50%; background: var(--acc); border: 3px solid var(--p);
    }
    body[data-comp-profile="A"] .faq-rounded { display: grid; gap: 1rem; }
    body[data-comp-profile="A"] .faq-bubble {
      background: #fff; border-radius: 20px; padding: 1.15rem 1.35rem;
      border: 1px solid var(--line); box-shadow: 0 8px 24px rgba(15,23,42,0.05);
    }
    body[data-comp-profile="A"] .rev-float {
      display: grid; gap: 1.25rem; grid-template-columns: repeat(3, 1fr);
      align-items: start; padding: 1rem 0 2rem;
    }
    body[data-comp-profile="A"] .rev-card {
      background: rgba(255,255,255,0.92); border-radius: 18px; padding: 1.25rem;
      box-shadow: 0 18px 36px rgba(15,23,42,0.12); border: 1px solid rgba(255,255,255,0.8);
    }
    body[data-comp-profile="A"] .rev-float-a { transform: translateY(0); }
    body[data-comp-profile="A"] .rev-float-b { transform: translateY(1.5rem); }
    body[data-comp-profile="A"] .rev-float-c { transform: translateY(0.5rem); }
    body[data-comp-profile="A"] .gal-masonry {
      column-count: 3; column-gap: 0.85rem;
    }
    body[data-comp-profile="A"] .gal-item {
      break-inside: avoid; margin: 0 0 0.85rem; border-radius: 16px; overflow: hidden;
    }
    body[data-comp-profile="A"] .gal-item img { width: 100%; display: block; }
    body[data-comp-profile="A"] .mid-cta-glass {
      background: transparent; padding: 2rem 1.25rem;
    }
    body[data-comp-profile="A"] .mid-cta-glass .mid-cta-inner {
      max-width: 720px; margin: 0 auto; text-align: center;
      padding: 2.5rem 1.75rem; border-radius: 28px;
      background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.35);
      backdrop-filter: blur(12px); color: #fff;
      background-image: linear-gradient(135deg, var(--pd), var(--p));
    }
    body[data-comp-profile="A"] .mid-cta-glass h2 { color: #fff; margin-bottom: 1rem; }
    @media (max-width: 800px) {
      body[data-comp-profile="A"] .rev-float { grid-template-columns: 1fr; }
      body[data-comp-profile="A"] .rev-float-b { transform: none; }
      body[data-comp-profile="A"] .gal-masonry { column-count: 2; }
    }
""",
        "B": """
    body[data-comp-profile="B"] .services-solid {
      display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      list-style: none;
    }
    body[data-comp-profile="B"] .svc-solid {
      position: relative; background: #fff; border: 1px solid var(--line);
      border-radius: 8px; padding: 1.25rem 1.15rem 1.25rem 1.35rem;
      box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    }
    body[data-comp-profile="B"] .svc-accent {
      position: absolute; left: 0; top: 0; bottom: 0; width: 5px; background: var(--p);
      border-radius: 8px 0 0 8px;
    }
    body[data-comp-profile="B"] .ben-timeline {
      list-style: none; display: grid; gap: 0; border-left: 3px solid var(--p); margin-left: 0.75rem;
    }
    body[data-comp-profile="B"] .ben-step {
      display: grid; grid-template-columns: 2.5rem 1fr; gap: 0.75rem;
      padding: 1rem 0 1rem 1rem; position: relative;
    }
    body[data-comp-profile="B"] .ben-n {
      width: 2rem; height: 2rem; border-radius: 4px; background: var(--p); color: #fff;
      display: grid; place-items: center; font-weight: 800; font-size: 0.85rem;
    }
    body[data-comp-profile="B"] .faq-twocol {
      display: grid; gap: 1rem; grid-template-columns: 1fr 1fr;
    }
    body[data-comp-profile="B"] .faq-panel {
      background: #0f172a; color: #e2e8f0; border-radius: 8px; padding: 1.15rem;
    }
    body[data-comp-profile="B"] .faq-panel h3 { color: var(--acc); }
    body[data-comp-profile="B"] .faq-span { grid-column: 1 / -1; }
    body[data-comp-profile="B"] .rev-quotes { display: grid; gap: 1.5rem; }
    body[data-comp-profile="B"] .rev-quote {
      border-left: 4px solid var(--p); padding: 0.5rem 0 0.5rem 1.25rem;
      background: transparent; position: relative;
    }
    body[data-comp-profile="B"] .rev-mark {
      font-size: 3rem; line-height: 1; color: var(--acc); font-weight: 700;
      display: block; margin-bottom: 0.25rem;
    }
    body[data-comp-profile="B"] .gal-grid {
      display: grid; gap: 0.65rem; grid-template-columns: repeat(3, 1fr);
    }
    body[data-comp-profile="B"] .gal-cell {
      margin: 0; aspect-ratio: 1; overflow: hidden; border-radius: 6px; background: #111;
    }
    body[data-comp-profile="B"] .gal-cell img { width: 100%; height: 100%; object-fit: cover; display: block; }
    body[data-comp-profile="B"] .mid-cta-solid {
      text-align: left; padding: 2rem 1.5rem 2rem max(1.5rem, 8vw);
      background: #0a0a0a; color: #fff; display: flex; flex-wrap: wrap;
      align-items: center; justify-content: space-between; gap: 1rem;
    }
    body[data-comp-profile="B"] .mid-cta-solid h2 { color: #fff; margin: 0; font-size: 1.45rem; }
    @media (max-width: 720px) {
      body[data-comp-profile="B"] .faq-twocol { grid-template-columns: 1fr; }
      body[data-comp-profile="B"] .gal-grid { grid-template-columns: 1fr 1fr; }
    }
""",
        "C": """
    body[data-comp-profile="C"] .services-minimal {
      display: grid; gap: 0; list-style: none; border-top: 1px solid var(--line);
    }
    body[data-comp-profile="C"] .svc-minimal {
      padding: 1.5rem 0; border-bottom: 1px solid var(--line); background: transparent;
      border-radius: 0; box-shadow: none;
    }
    body[data-comp-profile="C"] .svc-minimal h3 { font-weight: 600; letter-spacing: 0.01em; }
    body[data-comp-profile="C"] .ben-editorial { max-width: 36rem; }
    body[data-comp-profile="C"] .ben-editorial-list {
      list-style: none; display: grid; gap: 1rem;
    }
    body[data-comp-profile="C"] .ben-editorial-list li {
      padding: 0; font-size: 1.05rem; line-height: 1.7; color: var(--ink);
      border: 0; padding-left: 0;
    }
    body[data-comp-profile="C"] .ben-editorial-list li::before { content: none; }
    body[data-comp-profile="C"] .faq-accordion { display: grid; gap: 0; border-top: 1px solid var(--line); }
    body[data-comp-profile="C"] .faq-acc {
      border-bottom: 1px solid var(--line); padding: 0.85rem 0;
      background: transparent;
    }
    body[data-comp-profile="C"] .faq-acc summary {
      cursor: pointer; font-weight: 600; color: var(--pd); list-style: none;
    }
    body[data-comp-profile="C"] .faq-acc summary::-webkit-details-marker { display: none; }
    body[data-comp-profile="C"] .faq-acc p { margin-top: 0.65rem; color: #475569; }
    body[data-comp-profile="C"] .rev-rating-grid {
      display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    }
    body[data-comp-profile="C"] .rev-rate {
      background: transparent; border: 0; border-top: 2px solid var(--acc);
      padding: 1rem 0; border-radius: 0;
    }
    body[data-comp-profile="C"] .rev-stars { color: var(--acc); letter-spacing: 0.15em; font-size: 0.85rem; }
    body[data-comp-profile="C"] .gal-feature {
      display: grid; grid-template-columns: 1.6fr 1fr; gap: 0.75rem;
    }
    body[data-comp-profile="C"] .gal-hero, body[data-comp-profile="C"] .gal-side {
      margin: 0; overflow: hidden; border-radius: 4px; background: var(--surface);
    }
    body[data-comp-profile="C"] .gal-hero { min-height: 280px; }
    body[data-comp-profile="C"] .gal-hero img,
    body[data-comp-profile="C"] .gal-side img {
      width: 100%; height: 100%; object-fit: cover; display: block; min-height: 140px;
    }
    body[data-comp-profile="C"] .gal-side-col { display: grid; gap: 0.75rem; }
    body[data-comp-profile="C"] .mid-cta-editorial {
      background: #fff; color: var(--ink); text-align: left;
      padding: 3rem max(1.5rem, 12vw); border-top: 1px solid var(--line);
    }
    body[data-comp-profile="C"] .mid-cta-editorial h2 { color: var(--ink); font-weight: 500; }
    body[data-comp-profile="C"] .mid-cta-rule {
      width: 3rem; height: 2px; background: var(--acc); margin-bottom: 1.25rem;
    }
    @media (max-width: 720px) {
      body[data-comp-profile="C"] .gal-feature { grid-template-columns: 1fr; }
    }
""",
    }
    return shared + sheets.get(pid, sheets["A"])
