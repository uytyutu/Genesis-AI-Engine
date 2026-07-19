"""Landing Page HTML builder — sandbox only, no external APIs."""

from __future__ import annotations

import html as html_lib
import re
from dataclasses import dataclass

from app.factory.analyzer import AnalysisResult
from app.factory.niche_profiles import resolve_niche_profile
from app.factory.package_features import (
    PackageFeatures,
    maps_embed_src,
    resolve_package_features,
    whatsapp_href,
)


@dataclass
class BuildStyle:
    primary: str
    primary_dark: str
    accent: str
    hero_gradient: str


def _style_from_niche(niche_id: str, *, modern: bool = False, blue_boost: bool = False) -> BuildStyle:
    profile = resolve_niche_profile(niche_id)
    style = BuildStyle(
        profile.style.primary,
        profile.style.primary_dark,
        profile.style.accent,
        profile.style.hero_gradient,
    )
    if modern:
        style = BuildStyle(
            style.primary,
            style.primary_dark,
            style.accent,
            f"linear-gradient(160deg,#0f172a,{style.primary})",
        )
    if blue_boost and niche_id == "dental":
        # Keep dental clean; do not recolor other niches to dental blue.
        style = BuildStyle(
            profile.style.primary,
            profile.style.primary_dark,
            profile.style.accent,
            profile.style.hero_gradient,
        )
    return style

_FORBIDDEN_SNIPPETS = (
    "уточним после",
    "Landing Page —",
    "Понятное предложение на главном экране",
    "Готовность к публикации после вашего одобрения",
)


def build_landing_html(
    analysis: AnalysisResult,
    *,
    features: PackageFeatures | None = None,
    whatsapp: str = "",
    city: str = "",
    street: str = "",
    modern: bool = False,
    blue_boost: bool = False,
    calculator: bool = False,
    include_testimonials: bool = False,
    large_headline: bool = False,
    motion_level: str = "none",
) -> str:
    feat = features or resolve_package_features("basic")
    if feat.premium_design:
        modern = True
        large_headline = True
    if feat.calculator:
        calculator = True
    if feat.testimonials:
        include_testimonials = True

    style = _style_from_niche(analysis.niche, modern=modern, blue_boost=blue_boost)

    descriptions = analysis.service_descriptions
    if len(descriptions) < len(analysis.services):
        descriptions = descriptions + ("",) * (len(analysis.services) - len(descriptions))

    esc = html_lib.escape
    business = esc(analysis.business_name)
    headline = esc(analysis.headline)
    subtitle = esc(analysis.subtitle)
    about = esc(analysis.about_text)
    cta = esc(analysis.cta_label)
    phone = esc(analysis.phone)
    email = esc(analysis.email)
    hours = esc(analysis.hours)

    services_html = "".join(
        f'<li class="service-card"><h3>{esc(title)}</h3><p class="service-desc">{esc(desc)}</p></li>'
        for title, desc in zip(analysis.services, descriptions)
    )
    trust_html = "".join(f'<span class="trust-pill">{esc(t)}</span>' for t in analysis.trust_points)
    benefits_html = "".join(f"<li>{esc(b)}</li>" for b in analysis.benefits)
    from app.factory.motion_brief import normalize_motion_level

    motion = normalize_motion_level(motion_level)
    css_motion = motion == "css"
    if css_motion:
        h1_class = ' class="hero-text large"' if large_headline else ' class="hero-text"'
        hero_p_class = ' class="hero-text hero-text-delay"'
        trust_class = ' class="trust-row hero-text hero-text-delay-2"'
        btn_class = "btn cta-button"
        sec = "section reveal"
    else:
        h1_class = ' class="large"' if large_headline else ""
        hero_p_class = ""
        trust_class = ' class="trust-row"'
        btn_class = "btn"
        sec = "section"
    page_title = f"{analysis.business_name} — {analysis.subtitle[:60]}"
    meta_desc = esc(analysis.subtitle[:160])
    motion_head = (
        '  <link rel="stylesheet" href="assets/motion_kit.css">\n' if css_motion else ""
    )
    motion_script = (
        '  <script src="assets/reveal.js" defer></script>\n' if css_motion else ""
    )

    wa_url = whatsapp_href(whatsapp, analysis.phone) if feat.whatsapp else ""
    logo_block = (
        _logo_block(analysis.business_name) if feat.logo_slot else f"<strong>{business}</strong>"
    )
    maps_block = ""
    if feat.maps:
        src = maps_embed_src(business_name=analysis.business_name, city=city, street=street)
        maps_block = f"""
  <section class="{sec} maps" id="maps">
    <h2>Standort</h2>
    <p class="muted">So finden Sie uns — Karte anhand Ihrer Firmendaten.</p>
    <div class="maps-frame">
      <iframe title="Google Maps" src="{esc(src)}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
    </div>
  </section>
"""
    calc_block = _calculator_block(section_class=sec) if calculator else ""
    form_block = _contact_form_block(analysis.email) if feat.contact_form else ""
    wa_contact = ""
    if feat.whatsapp:
        wa_contact = (
            f'<p><strong>WhatsApp:</strong> <a class="wa-btn" href="{esc(wa_url)}" '
            f'target="_blank" rel="noopener">Nachricht senden</a></p>'
        )
    hero_cta_extra = ""
    if feat.whatsapp and wa_url != "#contact":
        wa_btn = f"{btn_class} btn-wa" if css_motion else "btn btn-wa"
        hero_cta_extra = (
            f' <a class="{wa_btn}" href="{esc(wa_url)}" target="_blank" rel="noopener">WhatsApp</a>'
        )

    seo_extra = ""
    if feat.extended_seo:
        import json as _json

        ld = _json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "LocalBusiness",
                "name": analysis.business_name,
                "description": analysis.subtitle[:200],
                "telephone": analysis.phone,
                "email": analysis.email,
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": city or "",
                    "addressCountry": "DE",
                },
            },
            ensure_ascii=False,
        )
        seo_extra = f"""
  <meta name="robots" content="index,follow">
  <meta property="og:title" content="{esc(page_title)}">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:type" content="website">
  <script type="application/ld+json">{ld}</script>
"""

    analytics_block = ""
    if feat.analytics:
        analytics_block = """
  <!-- Google Analytics: Measurement-ID nach Go-live ersetzen (G-XXXXXXXXXX) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-XXXXXXXXXX');
  </script>
"""

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(page_title)}</title>
  <meta name="description" content="{meta_desc}">
  {seo_extra}
  {analytics_block}
  {motion_head}
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; color: #0f172a; line-height: 1.65; }}
    .topbar {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 0.75rem 1.5rem; background: rgba(15,23,42,0.92); color: #fff;
      position: sticky; top: 0; z-index: 10; gap: 1rem;
    }}
    .brand {{ display: flex; align-items: center; gap: 0.75rem; }}
    .brand img {{ height: 40px; width: auto; max-width: 140px; object-fit: contain; background: #fff; border-radius: 6px; padding: 2px 6px; }}
    .brand .logo-fallback {{
      width: 40px; height: 40px; border-radius: 8px; background: {style.accent}; color: #0f172a;
      display: grid; place-items: center; font-weight: 800; font-size: 0.85rem;
    }}
    .topbar strong {{ font-size: 1rem; letter-spacing: -0.01em; }}
    .topbar a {{ color: {style.accent}; text-decoration: none; font-weight: 600; font-size: 0.9rem; }}
    .hero {{
      background: {style.hero_gradient};
      color: #fff;
      padding: 4rem 1.5rem 5rem;
      text-align: center;
    }}
    .hero h1 {{ font-size: clamp(1.85rem, 4.5vw, 3rem); font-weight: 800; letter-spacing: -0.02em; margin-bottom: 1rem; max-width: 44rem; margin-inline: auto; }}
    .hero h1.large {{ font-size: clamp(2.25rem, 5vw, 3.5rem); }}
    .hero p {{ font-size: 1.15rem; opacity: 0.95; max-width: 38rem; margin: 0 auto 1.5rem; }}
    .trust-row {{ display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center; margin-bottom: 2rem; }}
    .trust-pill {{ background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25); padding: 0.35rem 0.85rem; border-radius: 999px; font-size: 0.8rem; }}
    .hero-ctas {{ display: flex; flex-wrap: wrap; gap: 0.75rem; justify-content: center; }}
    .btn {{
      display: inline-block;
      background: {style.accent};
      color: #0f172a;
      font-weight: 700;
      padding: 0.875rem 2rem;
      border-radius: 999px;
      text-decoration: none;
      box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }}
    .btn-wa {{ background: #25d366; color: #052e16; }}
    .wa-btn {{ color: #15803d; font-weight: 700; }}
    .section {{ padding: 3.5rem 1.5rem; max-width: 960px; margin: 0 auto; }}
    .section h2 {{ font-size: 1.75rem; margin-bottom: 1.25rem; color: {style.primary_dark}; }}
    .services {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); list-style: none; }}
    .service-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1.25rem;
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .service-card h3 {{ font-size: 1.05rem; margin-bottom: 0.5rem; color: {style.primary_dark}; }}
    .service-desc {{ font-size: 0.92rem; color: #475569; line-height: 1.5; }}
    .service-card:hover {{ transform: translateY(-2px); box-shadow: 0 12px 24px rgba(0,0,0,0.08); }}
    .about {{ background: #f1f5f9; }}
    .benefits {{ background: #fff; }}
    .benefits ul {{ list-style: none; display: grid; gap: 0.75rem; }}
    .benefits li {{ padding-left: 1.5rem; position: relative; }}
    .benefits li::before {{ content: "✓"; position: absolute; left: 0; color: {style.primary}; font-weight: 700; }}
    .muted {{ color: #64748b; margin-bottom: 1rem; }}
    .contact-grid {{ display: grid; gap: 0.5rem; font-size: 1rem; }}
    .contact-form {{ display: grid; gap: 0.75rem; max-width: 480px; margin-top: 1.25rem; }}
    .contact-form label {{ display: grid; gap: 0.35rem; font-weight: 600; font-size: 0.9rem; }}
    .contact-form input, .contact-form textarea {{
      padding: 0.65rem 0.75rem; border-radius: 8px; border: 1px solid #cbd5e1; font: inherit;
    }}
    .contact-form button {{
      justify-self: start; background: {style.primary}; color: #fff; border: 0;
      padding: 0.75rem 1.5rem; border-radius: 999px; font-weight: 700; cursor: pointer;
    }}
    .calculator {{ background: #fff; border-top: 1px solid #e2e8f0; }}
    .calc-grid {{ display: grid; gap: 1rem; max-width: 400px; }}
    .calc-grid label {{ display: flex; flex-direction: column; gap: 0.5rem; font-weight: 600; }}
    .calc-grid select, .calc-grid input {{ padding: 0.5rem; border-radius: 8px; border: 1px solid #cbd5e1; }}
    .calc-result {{ font-size: 1.25rem; margin-top: 0.5rem; }}
    .testimonials {{ background: #f8fafc; }}
    .testimonial-grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    .testimonial-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.25rem; }}
    .testimonial-card cite {{ display: block; margin-top: 0.75rem; font-size: 0.875rem; color: #64748b; }}
    .maps-frame {{ border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; aspect-ratio: 16/9; }}
    .maps-frame iframe {{ width: 100%; height: 100%; border: 0; }}
    footer {{ text-align: center; padding: 2rem; font-size: 0.875rem; background: #0f172a; color: #cbd5e1; }}
    @media (max-width: 640px) {{
      .hero {{ padding: 3rem 1rem 4rem; }}
      .section {{ padding: 2.5rem 1rem; }}
    }}
  </style>
</head>
<body>
  <nav class="topbar">
    <div class="brand">{logo_block}</div>
    <a href="#contact">{cta}</a>
  </nav>
  <header class="hero">
    <h1{h1_class}>{headline}</h1>
    <p{hero_p_class}>{subtitle}</p>
    <div{trust_class}>{trust_html}</div>
    <div class="hero-ctas">
      <a class="{btn_class}" href="#contact">{cta}</a>{hero_cta_extra}
    </div>
  </header>
  <section class="{sec}" id="services">
    <h2>Leistungen</h2>
    <ul class="services">{services_html}</ul>
  </section>
  <section class="{sec} benefits">
    <h2>Warum {business}</h2>
    <ul>{benefits_html}</ul>
  </section>
  <section class="{sec} about">
    <h2>Über uns</h2>
    <p>{about}</p>
  </section>
  {calc_block}
  {_testimonials_section(include_testimonials, section_class=sec)}
  {maps_block}
  <section class="{sec}" id="contact">
    <h2>Kontakt</h2>
    <p class="muted">Schreiben oder rufen Sie an — wir melden uns schnellstmöglich.</p>
    <div class="contact-grid">
      <p><strong>Telefon:</strong> <a href="tel:{_tel_href(analysis.phone)}">{phone}</a></p>
      {wa_contact}
      <p><strong>E-Mail:</strong> <a href="mailto:{email}">{email}</a></p>
      <p><strong>Öffnungszeiten:</strong> {hours}</p>
    </div>
    {form_block}
  </section>
  <footer>
    {business} · © {business}<br>
    <a href="impressum.html" style="color:#94a3b8;margin-right:0.75rem">Impressum</a>
    <a href="datenschutz.html" style="color:#94a3b8">Datenschutz</a>
  </footer>
{motion_script}</body>
</html>
"""
    lower = html.lower()
    for snippet in _FORBIDDEN_SNIPPETS:
        if snippet.lower() in lower:
            raise ValueError(f"forbidden_copy_snippet:{snippet}")
    return html


def _logo_block(business_name: str) -> str:
    safe = html_lib.escape(business_name)
    initials = "".join(w[0] for w in re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", business_name)[:2]) or "VC"
    return (
        f'<img src="assets/logo.png" alt="{safe}" '
        f'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'grid\'">'
        f'<span class="logo-fallback" style="display:none">{html_lib.escape(initials[:2].upper())}</span>'
        f"<strong>{safe}</strong>"
    )


def _tel_href(phone: str) -> str:
    return re.sub(r"[^\d+]", "", phone)


def _calculator_block(*, section_class: str = "section") -> str:
    return f"""
    <section class="{section_class} calculator" id="calculator">
      <h2>Kostenrechner</h2>
      <p class="muted">Unverbindliche Schätzung — Details klären wir im Gespräch.</p>
      <div class="calc-grid">
        <label>Leistung<select id="svc"><option>Basis</option><option>Standard</option><option>Premium</option></select></label>
        <label>Anzahl<input type="number" id="qty" value="1" min="1" max="10"></label>
        <p class="calc-result">Summe: <strong id="total">ab 49 €</strong></p>
      </div>
    </section>
    <script>
      (function(){{
        const prices = {{0:49,1:99,2:199}};
        function upd(){{
          const s = document.getElementById('svc').selectedIndex;
          const q = Math.max(1, parseInt(document.getElementById('qty').value||'1',10));
          document.getElementById('total').textContent = 'ab ' + (prices[s]*q) + ' €';
        }}
        document.getElementById('svc').onchange = upd;
        document.getElementById('qty').oninput = upd;
      }})();
    </script>
"""


def _contact_form_block(email: str) -> str:
    action = f"mailto:{html_lib.escape(email)}?subject=Anfrage%20Website"
    return f"""
    <form class="contact-form" action="{action}" method="get">
      <label>Name<input name="name" required placeholder="Ihr Name"></label>
      <label>Telefon<input name="phone" type="tel" placeholder="+49 …"></label>
      <label>Nachricht<textarea name="body" rows="4" required placeholder="Kurz Ihr Anliegen"></textarea></label>
      <button type="submit">Anfrage senden</button>
    </form>
"""


def _testimonials_section(enabled: bool, *, section_class: str = "section") -> str:
    if not enabled:
        return ""
    return f"""
  <section class="{section_class} testimonials" id="testimonials">
    <h2>Kundenstimmen</h2>
    <p class="muted">Beispieltexte — bitte durch echte Kundenstimmen ersetzen.</p>
    <div class="testimonial-grid">
      <blockquote class="testimonial-card"><p>«Professionell und zuverlässig — klare Empfehlung.»</p><cite>— Anna K.</cite></blockquote>
      <blockquote class="testimonial-card"><p>«Transparente Preise und gutes Ergebnis.»</p><cite>— Michael W.</cite></blockquote>
      <blockquote class="testimonial-card"><p>«Schnelle Terminvergabe und freundlicher Service.»</p><cite>— Familie S.</cite></blockquote>
    </div>
  </section>
"""
