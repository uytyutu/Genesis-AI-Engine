"""Landing Page HTML builder — sandbox only, no external APIs."""

from __future__ import annotations

import html as html_lib
import re
from dataclasses import dataclass

from app.factory.analyzer import AnalysisResult
from app.factory.catalog_manager import CatalogView
from app.factory.landing_tier_css import tier_stylesheet
from app.factory.niche_profiles import resolve_niche_profile
from app.factory.package_features import (
    PackageFeatures,
    maps_embed_src,
    maps_route_url,
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
    market_code: str | None = None,
    hero_photo: bool = True,
    catalog: CatalogView | None = None,
    hero_pack_manifest: dict | None = None,
) -> str:
    from app.factory.landing_i18n import (
        apply_legal_footer_hrefs,
        landing_lang_for_market,
        localize_analysis,
        maps_country_label,
        ui_strings,
    )

    feat = features or resolve_package_features("basic")
    tier = feat.package_id
    if feat.premium_design:
        modern = True
        large_headline = True
    if feat.calculator:
        calculator = True
    if feat.testimonials:
        include_testimonials = True

    lang = landing_lang_for_market(market_code)
    ui = apply_legal_footer_hrefs(ui_strings(lang), market_code)
    analysis = localize_analysis(analysis, lang)
    maps_country = maps_country_label(market_code)

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
    city_esc = esc(city) if city else ""

    services_html = "".join(
        f'<li class="service-card"><h3>{esc(title)}</h3><p class="service-desc">{esc(desc)}</p></li>'
        for title, desc in zip(analysis.services, descriptions)
    )
    trust_html = "".join(f'<span class="trust-pill">{esc(t)}</span>' for t in analysis.trust_points)
    benefits_html = "".join(f"<li>{esc(b)}</li>" for b in analysis.benefits)
    cert_html = "".join(f'<span class="cert-badge">{esc(t)}</span>' for t in analysis.trust_points)

    from app.factory.motion_brief import normalize_motion_level

    motion = normalize_motion_level(motion_level)
    css_motion = motion == "css"
    if css_motion:
        h1_class = ' class="hero-text large hero-anim"' if large_headline else ' class="hero-text hero-anim"'
        hero_p_class = ' class="lead hero-text hero-text-delay hero-anim hero-anim-d1"'
        trust_class = ' class="trust-row hero-text hero-text-delay-2 hero-anim hero-anim-d2"'
        btn_class = "btn cta-button"
        sec = "section reveal"
    else:
        h1_class = ' class="large hero-anim"' if large_headline else ' class="hero-anim"'
        hero_p_class = ' class="lead hero-anim hero-anim-d1"'
        trust_class = ' class="trust-row hero-anim hero-anim-d2"'
        btn_class = "btn"
        sec = "section"

    page_title = f"{analysis.business_name} — {analysis.subtitle[:60]}"
    meta_desc = esc(analysis.subtitle[:160])
    motion_head = (
        '  <link rel="stylesheet" href="assets/motion_kit.css">\n' if css_motion else ""
    )

    wa_url = whatsapp_href(whatsapp, analysis.phone) if feat.whatsapp else ""
    logo_block = (
        _logo_block(analysis.business_name) if feat.logo_slot else f"<strong>{business}</strong>"
    )

    route_url = maps_route_url(
        business_name=analysis.business_name,
        city=city,
        street=street,
        country=maps_country,
    )
    maps_block = ""
    if feat.maps:
        src = maps_embed_src(
            business_name=analysis.business_name,
            city=city,
            street=street,
            country=maps_country,
        )
        maps_block = f"""
  <section class="{sec} maps" id="maps">
    <h2>{esc(ui['maps'])}</h2>
    <p class="muted">{esc(ui['maps_muted'])}</p>
    <div class="maps-frame">
      <iframe title="{esc(ui['maps_iframe_title'])}" src="{esc(src)}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
    </div>
    <div class="maps-actions">
      <a class="btn-route" href="{esc(route_url)}" target="_blank" rel="noopener">{esc(ui['route_btn'])}</a>
      <span class="chip">{esc(ui['parking'])}</span>
      <span class="chip"><strong>{esc(ui['hours'])}:</strong> {hours}</span>
    </div>
  </section>
"""

    calc_block = _calculator_block(ui, section_class=sec) if calculator else ""
    form_block = _contact_form_block(
        analysis.email,
        ui,
        inquiry_skus=bool(catalog and catalog.request_cart),
    ) if feat.contact_form else ""
    wa_contact = ""
    if feat.whatsapp:
        wa_contact = (
            f'<p><strong>{esc(ui["whatsapp"])}:</strong> <a class="wa-btn" href="{esc(wa_url)}" '
            f'target="_blank" rel="noopener">{esc(ui["whatsapp_send"])}</a></p>'
        )
    hero_cta_extra = ""
    if feat.whatsapp and wa_url != "#contact":
        wa_btn = f"{btn_class} btn-wa" if css_motion else "btn btn-wa"
        hero_cta_extra = (
            f' <a class="{wa_btn}" href="{esc(wa_url)}" target="_blank" rel="noopener">'
            f'{esc(ui["whatsapp"])}</a>'
        )
    if include_testimonials:
        rev_btn = f"{btn_class} btn-reviews" if css_motion else "btn btn-reviews"
        hero_cta_extra += (
            f' <a class="{rev_btn}" href="#testimonials">{esc(ui["reviews"])}</a>'
        )
    reviews_nav = (
        f' <a href="#testimonials">{esc(ui["reviews"])}</a>' if include_testimonials else ""
    )
    maps_nav = f' <a href="#maps">{esc(ui["maps"])}</a>' if feat.maps else ""
    catalog_nav = (
        f' <a href="#catalog">{esc(ui["catalog_nav"])}</a>' if catalog else ""
    )

    catalog_block = _catalog_section(catalog, ui, section_class=sec) if catalog else ""
    services_block = f"""
  <section class="{sec}" id="services">
    <h2>{esc(ui['services'])}</h2>
    <ul class="services">{services_html}</ul>
  </section>
"""
    motion_script = (
        ('  <script src="assets/reveal.js" defer></script>\n' if css_motion else "")
        + ('  <script src="assets/catalog.js" defer></script>\n' if catalog else "")
    )
    seo_extra = ""
    if feat.extended_seo:
        import json as _json

        from app.factory.market_delivery import normalize_market

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
                    "addressCountry": normalize_market(market_code or "DE"),
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
        analytics_block = f"""
  <!-- {esc(ui['analytics_comment'])} -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-XXXXXXXXXX');
  </script>
"""

    why_title = esc(ui["why"].format(business=analysis.business_name))
    css = tier_stylesheet(tier, style)
    if hero_pack_manifest:
        from app.factory.hero_pack import pack_section_css

        extra = pack_section_css(hero_pack_manifest, tier)
        if extra:
            css = css + "\n" + extra
    hero_photo_class = " has-photo" if hero_photo else ""

    trust_strip = ""
    if feat.trust_bar:
        trust_strip = f'<div class="trust-strip"><span>{esc(ui["trust_bar"])}</span></div>'

    info_bar = ""
    if feat.trust_bar:
        bits = []
        if phone:
            bits.append(f'<span><strong>{esc(ui["phone"])}</strong> {phone}</span>')
        if hours:
            bits.append(f'<span><strong>{esc(ui["hours"])}</strong> {hours}</span>')
        if city_esc:
            bits.append(f"<span>{city_esc}</span>")
        if bits:
            info_bar = f'<div class="info-bar">{"".join(bits)}</div>'

    mid_cta = ""
    if feat.mid_cta:
        mid_cta = f"""
  <section class="mid-cta" id="mid-cta">
    <h2>{esc(ui['mid_cta_title'])}</h2>
    <a class="{btn_class}" href="#contact">{esc(ui['mid_cta_btn'])}</a>
  </section>
"""

    process_block = ""
    if feat.process:
        process_block = f"""
  <section class="{sec}" id="process">
    <h2>{esc(ui['process_title'])}</h2>
    <div class="process-grid">
      <article class="process-card"><div class="n">1</div><h3>{esc(ui['process_s1_title'])}</h3><p class="muted">{esc(ui['process_s1_desc'])}</p></article>
      <article class="process-card"><div class="n">2</div><h3>{esc(ui['process_s2_title'])}</h3><p class="muted">{esc(ui['process_s2_desc'])}</p></article>
      <article class="process-card"><div class="n">3</div><h3>{esc(ui['process_s3_title'])}</h3><p class="muted">{esc(ui['process_s3_desc'])}</p></article>
    </div>
    <div class="cert-row">{cert_html}</div>
  </section>
"""

    faq_block = ""
    if feat.faq:
        faq_block = f"""
  <section class="{sec}" id="faq">
    <h2>{esc(ui['faq_title'])}</h2>
    <div class="faq-list">
      <article class="faq-item"><h3>{esc(ui['faq_q1'])}</h3><p>{esc(ui['faq_a1'])}</p></article>
      <article class="faq-item"><h3>{esc(ui['faq_q2'])}</h3><p>{esc(ui['faq_a2'])}</p></article>
      <article class="faq-item"><h3>{esc(ui['faq_q3'])}</h3><p>{esc(ui['faq_a3'])}</p></article>
    </div>
  </section>
"""

    stats_block = ""
    if feat.stats_strip:
        stats_block = f"""
  <section class="stats" id="stats" aria-label="stats">
    <div class="stat"><strong>{esc(ui['stats_v1'])}</strong><span>{esc(ui['stats_n1'])}</span></div>
    <div class="stat"><strong>{esc(ui['stats_v2'])}</strong><span>{esc(ui['stats_n2'])}</span></div>
    <div class="stat"><strong>{esc(ui['stats_v3'])}</strong><span>{esc(ui['stats_n3'])}</span></div>
  </section>
"""

    showcase_block = ""
    if feat.showcase:
        showcase_block = f"""
  <section class="{sec} showcase" id="showcase">
    <h2>{esc(ui['showcase_title'])}</h2>
    <p class="muted">{esc(ui['showcase_lead'])}</p>
    <div class="showcase-grid">
      <div class="showcase-panel main"><span class="cap">{business}</span></div>
      <div class="showcase-panel tone-a"><span class="cap">{esc(ui['services'])}</span></div>
      <div class="showcase-panel tone-b"><span class="cap">{esc(ui['reviews'])}</span></div>
    </div>
  </section>
"""

    html = f"""<!DOCTYPE html>
<html lang="{esc(lang)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(page_title)}</title>
  <meta name="description" content="{meta_desc}">
  {seo_extra}
  {analytics_block}
  {motion_head}
  <style>
{css}
  </style>
</head>
<body data-tier="{esc(tier)}">
  <nav class="topbar">
    <div class="brand">{logo_block}</div>
    <div class="topbar-links">
      {catalog_nav}{maps_nav}{reviews_nav}<a href="#contact">{cta}</a>
    </div>
  </nav>
  {trust_strip}
  <header class="hero{hero_photo_class}">
    <div class="hero-inner">
      <h1{h1_class}>{headline}</h1>
      <p{hero_p_class}>{subtitle}</p>
      <div{trust_class}>{trust_html}</div>
      <div class="hero-ctas">
        <a class="{btn_class}" href="#contact">{cta}</a>{hero_cta_extra}
      </div>
    </div>
  </header>
  {info_bar}
  {stats_block}
  {catalog_block}
  {services_block}
  {mid_cta}
  <section class="{sec} benefits">
    <h2>{why_title}</h2>
    <ul>{benefits_html}</ul>
  </section>
  {process_block}
  {showcase_block}
  <section class="{sec} about">
    <h2>{esc(ui['about'])}</h2>
    <p>{about}</p>
  </section>
  {faq_block}
  {calc_block}
  {_testimonials_section(include_testimonials, ui, section_class=sec)}
  {maps_block}
  <section class="{sec}" id="contact">
    <h2>{esc(ui['contact'])}</h2>
    <p class="muted">{esc(ui['contact_muted'])}</p>
    <div class="contact-grid">
      <p><strong>{esc(ui['phone'])}:</strong> <a href="tel:{_tel_href(analysis.phone)}">{phone}</a></p>
      {wa_contact}
      <p><strong>{esc(ui['email'])}:</strong> <a href="mailto:{email}">{email}</a></p>
      <p><strong>{esc(ui['hours'])}:</strong> {hours}</p>
    </div>
    {form_block}
  </section>
  <footer>
    {business} · © {business}<br>
    <a href="{esc(ui['legal_a_href'])}" style="color:#94a3b8;margin-right:0.75rem">{esc(ui['legal_a'])}</a>
    <a href="{esc(ui['legal_b_href'])}" style="color:#94a3b8">{esc(ui['legal_b'])}</a>
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


def _calculator_block(ui: dict[str, str], *, section_class: str = "section") -> str:
    esc = html_lib.escape
    from_lbl = esc(ui["calc_from"])
    return f"""
    <section class="{section_class} calculator" id="calculator">
      <h2>{esc(ui['calculator'])}</h2>
      <p class="muted">{esc(ui['calculator_muted'])}</p>
      <div class="calc-grid">
        <label>{esc(ui['calc_service'])}<select id="svc"><option>{esc(ui['calc_opt0'])}</option><option>{esc(ui['calc_opt1'])}</option><option>{esc(ui['calc_opt2'])}</option></select></label>
        <label>{esc(ui['calc_qty'])}<input type="number" id="qty" value="1" min="1" max="10"></label>
        <p class="calc-result">{esc(ui['calc_sum'])}: <strong id="total">{from_lbl} 49 €</strong></p>
      </div>
    </section>
    <script>
      (function(){{
        const prices = {{0:49,1:99,2:199}};
        const fromLbl = {esc(ui['calc_from'])!r};
        function upd(){{
          const s = document.getElementById('svc').selectedIndex;
          const q = Math.max(1, parseInt(document.getElementById('qty').value||'1',10));
          document.getElementById('total').textContent = fromLbl + ' ' + (prices[s]*q) + ' €';
        }}
        document.getElementById('svc').onchange = upd;
        document.getElementById('qty').oninput = upd;
      }})();
    </script>
"""


def _contact_form_block(
    email: str, ui: dict[str, str], *, inquiry_skus: bool = False
) -> str:
    from urllib.parse import quote

    esc = html_lib.escape
    subject = quote(ui["form_subject"])
    action = f"mailto:{esc(email)}?subject={subject}"
    sku_field = ""
    if inquiry_skus:
        sku_field = (
            f'<label>{esc(ui["catalog_inquiry_label"])}'
            f'<input id="catalog-inquiry-skus" name="skus" '
            f'placeholder="SKU…" readonly></label>'
        )
    return f"""
    <form class="contact-form" action="{action}" method="get">
      <label>{esc(ui['form_name'])}<input name="name" required placeholder="{esc(ui['form_name_ph'])}"></label>
      <label>{esc(ui['form_phone'])}<input name="phone" type="tel" placeholder="{esc(ui['form_phone_ph'])}"></label>
      {sku_field}
      <label>{esc(ui['form_message'])}<textarea name="body" rows="4" required placeholder="{esc(ui['form_message_ph'])}"></textarea></label>
      <button type="submit">{esc(ui['form_submit'])}</button>
    </form>
"""


def _catalog_section(
    catalog: CatalogView,
    ui: dict[str, str],
    *,
    section_class: str = "section",
) -> str:
    esc = html_lib.escape
    rich = " rich" if catalog.rich_cards else ""
    tools = ""
    if catalog.search or catalog.filters:
        search = ""
        if catalog.search:
            search = (
                f'<input type="search" id="catalog-search" '
                f'placeholder="{esc(ui["catalog_search_ph"])}" '
                f'aria-label="{esc(ui["catalog_search_ph"])}">'
            )
        filt = ""
        if catalog.filters and catalog.categories:
            opts = "".join(
                f'<option value="{esc(c["id"])}">{esc(c["label"])}</option>'
                for c in catalog.categories
            )
            filt = (
                f'<select id="catalog-filter" aria-label="{esc(ui["catalog_filter_all"])}">'
                f'<option value="">{esc(ui["catalog_filter_all"])}</option>{opts}</select>'
            )
        tools = f'<div class="catalog-tools">{search}{filt}</div>'

    cards = []
    for p in catalog.products:
        img = p.images[0] if p.images else ""
        img_html = (
            f'<img src="{esc(img)}" alt="{esc(p.name)}" loading="lazy">'
            if img
            else '<div class="product-ph" aria-hidden="true"></div>'
        )
        price = f"{p.price:g} {esc(p.currency)}"
        cta_label = ui["catalog_request"] if p.cta != "contact" else ui["catalog_contact"]
        cta = p.cta if p.cta in ("contact", "request") else "request"
        d3 = "true" if p.three_d_model_enabled else "false"
        vxp = esc(p.vxp_product_id or "")
        cards.append(
            f'<article class="product-card{rich}" data-sku="{esc(p.sku)}" '
            f'data-type="{esc(p.content_type)}" data-category="{esc(p.category_id)}" '
            f'data-name="{esc(p.name)}" '
            f'data-summary="{esc(p.summary)}" data-vxp="{vxp}" data-3d="{d3}">'
            f"{img_html}"
            f"<h3>{esc(p.name)}</h3>"
            f'<p class="price">{price}</p>'
            f'<p class="summary">{esc(p.summary)}</p>'
            f'<button type="button" class="btn-catalog" data-cta="{esc(cta)}">'
            f"{esc(cta_label)}</button>"
            f"</article>"
        )
    cart = ""
    if catalog.request_cart:
        cart = (
            f'<div class="catalog-cart" id="catalog-cart" hidden>'
            f"<h3>{esc(ui['catalog_cart_title'])}</h3>"
            f'<ul id="catalog-cart-items"></ul>'
            f'<a class="btn" href="#contact">{esc(ui["catalog_request"])}</a>'
            f"</div>"
        )
    grid = "".join(cards)
    return f"""
  <section class="{section_class} catalog" id="catalog">
    <h2>{esc(ui['catalog_title'])}</h2>
    <p class="muted">{esc(ui['catalog_lead'])}</p>
    {tools}
    <div class="catalog-grid">{grid}</div>
    {cart}
  </section>
"""


def _testimonials_section(
    enabled: bool, ui: dict[str, str], *, section_class: str = "section"
) -> str:
    if not enabled:
        return ""
    esc = html_lib.escape
    return f"""
  <section class="{section_class} testimonials" id="testimonials">
    <h2>{esc(ui['reviews'])}</h2>
    <p class="muted">{esc(ui['reviews_muted'])}</p>
    <div class="testimonial-grid">
      <blockquote class="testimonial-card"><p>{esc(ui['t1'])}</p><cite>{esc(ui['t1_cite'])}</cite></blockquote>
      <blockquote class="testimonial-card"><p>{esc(ui['t2'])}</p><cite>{esc(ui['t2_cite'])}</cite></blockquote>
      <blockquote class="testimonial-card"><p>{esc(ui['t3'])}</p><cite>{esc(ui['t3_cite'])}</cite></blockquote>
    </div>
  </section>
"""
