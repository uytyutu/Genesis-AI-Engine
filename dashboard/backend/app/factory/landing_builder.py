"""Landing Page HTML builder — sandbox only, no external APIs."""

from __future__ import annotations

import html as html_lib
import re
from dataclasses import dataclass

from app.factory.analyzer import AnalysisResult
from app.factory.catalog_manager import CatalogView
from app.factory.component_composer import (
    button_class_for_profile,
    compose_page_sections,
    get_component_profile,
    remapped_cta,
)
from app.factory.hero_composer import compose_hero
from app.factory.layout_variants import (
    assemble_body,
    compose_footer,
    layout_profile_css,
    resolve_component_for_layout,
    resolve_hero_for_layout,
    resolve_layout_profile,
    style_overrides,
)
from app.factory.landing_tier_css import tier_stylesheet
from app.factory.market_design import (
    assert_localization_hygiene,
    build_seo_localization,
    market_design_extra_css,
    resolve_market_design,
)
from app.factory.niche_profiles import niche_style_extra_css, resolve_niche_profile
from app.factory.package_features import (
    PackageFeatures,
    maps_embed_src,
    maps_route_url,
    resolve_package_features,
    whatsapp_href,
)
from app.factory.trust_composer import (
    collect_trust_evidence,
    compose_trust_section,
    select_trust_template,
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
    market_profile: object | None = None,
    hero_photo: bool = True,
    catalog: CatalogView | None = None,
    hero_pack_manifest: dict | None = None,
    client_logo: bool = False,
    client_logo_src: str = "assets/logo.png",
    client_gallery: list[str] | None = None,
    brand_style: str | None = None,
    client_trust: dict | None = None,
    media_css: str = "",
    media_background: bool = False,
) -> str:
    """Build Path A landing HTML.

    R3.4.1.4: when ``market_profile`` is passed (from Composer), language / CTA /
    locale / legal footer come only from that profile — no resolve(), no new
    country if/else. Legacy callers without profile keep prior helpers.
    """
    from dataclasses import replace as dc_replace

    from app.factory.landing_i18n import (
        apply_legal_footer_hrefs,
        landing_lang_for_market,
        localize_analysis,
        maps_country_label,
        ui_strings,
    )
    from app.factory.market_delivery import market_ui_lang
    from app.factory.market_profile import (
        coerce_market_profile,
        html_lang_for_profile,
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

    profile = coerce_market_profile(market_profile)  # type: ignore[arg-type]
    if profile is not None:
        # SSOT path — Composer already resolved MarketProfile
        lang = profile.language
        html_lang = html_lang_for_profile(profile)
        market_code = profile.market_code
        market_design = resolve_market_design(market_code)
        ui = ui_strings(lang)
        if profile.phone_format:
            ui["form_phone_ph"] = f"{profile.phone_format} …"
        maps_country = profile.label or profile.market_code
        # Niche copy overlay may run, but CTA stays from profile / Composer
        cta_preserved = analysis.cta_label or profile.default_cta
        analysis = localize_analysis(analysis, lang)
        analysis = dc_replace(
            analysis,
            cta_label=cta_preserved or profile.default_cta,
            hours=analysis.hours or profile.business_hours,
        )
        use_profile_footer = True
    else:
        # Legacy path (direct build_landing_html without Composer profile)
        lang = landing_lang_for_market(market_code)
        html_lang = market_ui_lang(market_code) or lang
        market_design = resolve_market_design(market_code)
        if market_design.html_lang == lang or lang == "de":
            html_lang = market_design.html_lang
        ui = apply_legal_footer_hrefs(ui_strings(lang), market_code)
        ui["form_phone_ph"] = market_design.phone_placeholder
        analysis = localize_analysis(analysis, lang)
        maps_country = maps_country_label(market_code)
        use_profile_footer = False

    # Real client stats only — never invent 12+/800+ for deliverables.
    trust_payload = client_trust if isinstance(client_trust, dict) else {}
    client_stats = trust_payload.get("stats")
    if isinstance(client_stats, (list, tuple)) and client_stats:
        for i, row in enumerate(client_stats[:3], start=1):
            if isinstance(row, dict):
                if row.get("value") is not None:
                    ui[f"stats_v{i}"] = str(row.get("value"))
                if row.get("label") is not None:
                    ui[f"stats_n{i}"] = str(row.get("label"))
    else:
        ui = {
            **ui,
            "stats_v1": "",
            "stats_v2": "",
            "stats_v3": "",
            "stats_n1": "",
            "stats_n2": "",
            "stats_n3": "",
        }

    style = _style_from_niche(analysis.niche, modern=modern, blue_boost=blue_boost)
    from app.factory.brand_style import (
        apply_brand_to_build_style,
        brand_style_extra_css,
        get_brand_style_pack,
        normalize_brand_style,
    )

    brand_id = normalize_brand_style(brand_style)
    brand_pack = get_brand_style_pack(brand_id)
    if brand_pack is not None:
        style = apply_brand_to_build_style(style, brand_pack)

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
    cert_html = "".join(f'<span class="cert-badge">{esc(t)}</span>' for t in analysis.trust_points)

    from app.factory.motion_brief import normalize_motion_level

    motion = normalize_motion_level(motion_level)
    css_motion = motion == "css"
    if css_motion:
        h1_class = ' class="hero-text large hero-anim"' if large_headline else ' class="hero-text hero-anim"'
        hero_p_class = ' class="lead hero-text hero-text-delay hero-anim hero-anim-d1"'
        trust_class = ' class="trust-row hero-text hero-text-delay-2 hero-anim hero-anim-d2"'
        sec = "section reveal"
    else:
        h1_class = ' class="large hero-anim"' if large_headline else ' class="hero-anim"'
        hero_p_class = ' class="lead hero-anim hero-anim-d1"'
        trust_class = ' class="trust-row hero-anim hero-anim-d2"'
        sec = "section"

    niche_profile = resolve_niche_profile(analysis.niche)
    layout_profile = resolve_layout_profile(
        business_name=analysis.business_name,
        package_id=tier,
        market_code=market_design.market_id,
        niche_id=niche_profile.niche_id,
    )
    hero_layout_id = resolve_hero_for_layout(
        layout_profile,
        niche_id=niche_profile.niche_id,
        business_name=analysis.business_name,
        package_id=tier,
    )
    comp_profile_id = resolve_component_for_layout(
        layout_profile,
        hero_layout=hero_layout_id,
        business_name=analysis.business_name,
        package_id=tier,
        niche_id=niche_profile.niche_id,
    )
    comp_profile = get_component_profile(comp_profile_id)
    btn_class = button_class_for_profile(comp_profile, css_motion=css_motion)
    layout_styles = style_overrides(layout_profile)

    page_title = f"{analysis.business_name} — {analysis.subtitle[:60]}"
    meta_desc = esc(analysis.subtitle[:160])
    motion_head = (
        '  <link rel="stylesheet" href="assets/motion_kit.css">\n' if css_motion else ""
    )

    wa_url = whatsapp_href(whatsapp, analysis.phone) if feat.whatsapp else ""
    show_logo = bool(feat.logo_slot or client_logo)
    logo_src = (client_logo_src or "assets/logo.png").strip() or "assets/logo.png"
    logo_block = (
        _logo_block(analysis.business_name, src=logo_src)
        if show_logo
        else f"<strong>{business}</strong>"
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
        pass  # Real review CTAs added only after TrustEvidence confirms client reviews
    reviews_nav = ""
    maps_nav = f' <a href="#maps">{esc(ui["maps"])}</a>' if feat.maps else ""
    catalog_nav = (
        f' <a href="#catalog">{esc(ui["catalog_nav"])}</a>' if catalog else ""
    )

    catalog_block = _catalog_section(catalog, ui, section_class=sec) if catalog else ""
    motion_script = (
        ('  <script src="assets/reveal.js" defer></script>\n' if css_motion else "")
        + ('  <script src="assets/catalog.js" defer></script>\n' if catalog else "")
    )
    from app.factory.ux_polish import back_to_top_html, back_to_top_script_tag

    btt_label = str(ui.get("back_to_top") or "Nach oben")
    motion_script = motion_script + back_to_top_script_tag(tier)
    back_to_top_block = back_to_top_html(tier, label=btt_label)
    seo_extra = build_seo_localization(
        profile=market_design,
        page_title=page_title,
        meta_description=analysis.subtitle[:160],
        business_name=analysis.business_name,
        subtitle=analysis.subtitle,
        phone=analysis.phone,
        email=analysis.email,
        city=city,
        market_code=market_code or market_design.market_id,
        extended=bool(feat.extended_seo),
    )

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
    css = css + "\n" + niche_style_extra_css(niche_profile)
    css = css + "\n" + market_design_extra_css(market_design)
    if hero_pack_manifest:
        from app.factory.hero_pack import pack_section_css

        extra = pack_section_css(hero_pack_manifest, tier)
        if extra:
            css = css + "\n" + extra
    if brand_pack is not None:
        css = css + "\n" + brand_style_extra_css(brand_pack)

    hero_comp = compose_hero(
        layout_id=hero_layout_id,
        business_name=analysis.business_name,
        headline=headline,
        subtitle=subtitle,
        cta_label=cta,
        trust_points=analysis.trust_points,
        benefits=analysis.benefits,
        hero_cta_extra=hero_cta_extra,
        h1_class=h1_class,
        hero_p_class=hero_p_class,
        trust_class=trust_class,
        btn_class=btn_class,
        ui=ui,
        hero_photo=hero_photo,
    )
    css = css + "\n" + hero_comp.css
    from app.factory.ux_polish import ux_polish_css

    css = css + "\n" + ux_polish_css(tier)
    hero_html = hero_comp.html
    if css_motion:
        hero_html = hero_html.replace('class="hero ', 'class="hero hero-parallax ', 1)

    gallery_paths = [p for p in (client_gallery or []) if p]
    trust_evidence = collect_trust_evidence(
        client_trust=trust_payload,
        commitments=analysis.trust_points,
        portfolio_paths=gallery_paths,
        has_maps=bool(feat.maps),
        has_process=bool(feat.process),
    )
    trust_template_id = select_trust_template(
        niche_id=niche_profile.niche_id,
        market_code=market_design.market_id,
        business_name=analysis.business_name,
        package_id=tier,
        evidence=trust_evidence,
    )
    # Fabricated testimonial quotes are forbidden — only client-supplied reviews.
    real_reviews = bool(trust_evidence.reviews)
    if real_reviews:
        reviews_nav = f' <a href="#testimonials">{esc(ui["reviews"])}</a>'
        rev_btn = f"{btn_class} btn-reviews" if css_motion else "btn btn-reviews"
        hero_cta_extra += (
            f' <a class="{rev_btn}" href="#testimonials">{esc(ui["reviews"])}</a>'
        )
        # Re-compose hero so CTA includes real review link
        hero_comp = compose_hero(
            layout_id=hero_layout_id,
            business_name=analysis.business_name,
            headline=headline,
            subtitle=subtitle,
            cta_label=cta,
            trust_points=analysis.trust_points,
            benefits=analysis.benefits,
            hero_cta_extra=hero_cta_extra,
            h1_class=h1_class,
            hero_p_class=hero_p_class,
            trust_class=trust_class,
            btn_class=btn_class,
            ui=ui,
            hero_photo=hero_photo,
        )
        hero_html = hero_comp.html
        if css_motion:
            hero_html = hero_html.replace('class="hero ', 'class="hero hero-parallax ', 1)

    # CTA strategy: early/mid → mid_cta slot; late → late_cta; dual → both
    want_mid = bool(feat.mid_cta) and layout_profile.cta_strategy in (
        "early",
        "mid",
        "dual",
    )
    want_late = bool(feat.mid_cta) and layout_profile.cta_strategy in ("late", "dual")
    page_sections = compose_page_sections(
        profile_id=comp_profile_id,
        analysis_services=analysis.services,
        service_descriptions=descriptions,
        benefits=analysis.benefits,
        ui=ui,
        business_name=analysis.business_name,
        why_title=why_title,
        section_class=sec,
        btn_class=btn_class,
        include_faq=bool(feat.faq),
        include_reviews=bool(include_testimonials and real_reviews),
        include_mid_cta=want_mid or want_late,
        gallery_paths=gallery_paths,
        client_reviews=trust_evidence.reviews if real_reviews else (),
        cards_override=layout_styles.get("cards"),
        gallery_override=layout_styles.get("gallery"),
        faq_override=layout_styles.get("faq"),
    )
    css = css + "\n" + page_sections.css
    css = css + "\n" + layout_profile_css(layout_profile)

    mid_cta_html = page_sections.mid_cta_html if want_mid else ""
    late_cta_html = (
        remapped_cta(page_sections.mid_cta_html, section_id="late-cta")
        if want_late
        else ""
    )
    if want_late and not want_mid:
        # Only late — remap the single CTA away from mid-cta id
        mid_cta_html = ""
        late_cta_html = remapped_cta(page_sections.mid_cta_html, section_id="late-cta")

    process_inner = ""
    if feat.process:
        process_inner = f"""
        <h3>{esc(ui['process_title'])}</h3>
        <div class="process-grid">
          <article class="process-card"><div class="n">1</div><h3>{esc(ui['process_s1_title'])}</h3><p class="muted">{esc(ui['process_s1_desc'])}</p></article>
          <article class="process-card"><div class="n">2</div><h3>{esc(ui['process_s2_title'])}</h3><p class="muted">{esc(ui['process_s2_desc'])}</p></article>
          <article class="process-card"><div class="n">3</div><h3>{esc(ui['process_s3_title'])}</h3><p class="muted">{esc(ui['process_s3_desc'])}</p></article>
        </div>
"""
    trust_comp = compose_trust_section(
        template_id=trust_template_id,
        evidence=trust_evidence,
        niche_id=niche_profile.niche_id,
        market_code=market_design.market_id,
        ui=ui,
        business_name=analysis.business_name,
        section_class=sec,
        process_html=process_inner,
    )
    css = css + "\n" + trust_comp.css
    if media_css:
        css = css + "\n" + media_css

    brand_attr = esc(brand_pack.id if brand_pack else "auto")
    niche_attr = esc(niche_profile.niche_id)
    hero_attr = esc(hero_comp.layout_id)
    comp_attr = esc(page_sections.profile_id)
    motion_attr = "css" if css_motion else "none"
    market_attr = esc(market_design.market_id)
    density_attr = esc(market_design.density)
    trust_attr = esc(trust_comp.template_id)
    media_bg_attr = "1" if media_background else "0"
    layout_attr = esc(layout_profile.id)
    footer_attr = esc(layout_profile.footer_variant)

    trust_strip = ""
    # R3.3 Navigation Gate: marketing trust bar is NOT a header chrome strip.
    # Claims live in Hero pills (trust_points) / Benefits — not under the menu.

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

    process_block = ""
    if feat.process and "process" not in trust_comp.blocks_used:
        process_block = f"""
  <section class="{sec}" id="process">
    <h2>{esc(ui['process_title'])}</h2>
    <div class="process-grid">
      <article class="process-card"><div class="n">1</div><h3>{esc(ui['process_s1_title'])}</h3><p class="muted">{esc(ui['process_s1_desc'])}</p></article>
      <article class="process-card"><div class="n">2</div><h3>{esc(ui['process_s2_title'])}</h3><p class="muted">{esc(ui['process_s2_desc'])}</p></article>
      <article class="process-card"><div class="n">3</div><h3>{esc(ui['process_s3_title'])}</h3><p class="muted">{esc(ui['process_s3_desc'])}</p></article>
    </div>
  </section>
"""

    stats_block = ""
    if feat.stats_strip and not hero_comp.embeds_stats and (ui.get("stats_v1") or "").strip():
        stats_cls = "stats reveal" if css_motion else "stats"
        stats_block = f"""
  <section class="{stats_cls}" id="stats" aria-label="stats">
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

    about_block = f"""
  <section class="{sec} about">
    <h2>{esc(ui['about'])}</h2>
    <p>{about}</p>
  </section>
"""
    contact_block = f"""
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
"""
    body_sections = {
        "info": info_bar,
        "stats": stats_block,
        "catalog": catalog_block,
        "services": page_sections.services_html,
        "mid_cta": mid_cta_html,
        "benefits": page_sections.benefits_html,
        "trust": trust_comp.html,
        "process": process_block,
        "showcase": showcase_block,
        "gallery": page_sections.gallery_html,
        "about": about_block,
        "faq": page_sections.faq_html,
        "calculator": calc_block,
        "reviews": page_sections.reviews_html,
        "maps": maps_block,
        "late_cta": late_cta_html,
        "contact": contact_block,
    }
    body_html = assemble_body(body_sections, layout_profile.section_order)
    footer_html = compose_footer(
        variant=layout_profile.footer_variant,
        business_name=analysis.business_name,
        ui=ui,
        phone=analysis.phone,
        email=analysis.email,
        city=city,
        market_profile=profile if use_profile_footer else None,
    )

    gallery_nav = (
        f' <a href="#gallery">{esc(ui.get("gallery_title") or "Galerie")}</a>'
        if gallery_paths
        else ""
    )
    # R3.3 Navigation Gate: header = section links + CTA only (no marketing claims).
    services_nav = f' <a href="#services">{esc(ui.get("services") or "Leistungen")}</a>'
    faq_nav = (
        f' <a href="#faq">{esc(ui.get("faq_title") or "FAQ")}</a>'
        if feat.faq
        else ""
    )
    # Do not put maps/trust/reviews marketing into the topbar — body sections remain.

    html = f"""<!DOCTYPE html>
<html lang="{esc(html_lang)}">
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
<body id="top" data-tier="{esc(tier)}" data-brand="{brand_attr}" data-niche="{niche_attr}" data-hero-layout="{hero_attr}" data-comp-profile="{comp_attr}" data-layout-profile="{layout_attr}" data-footer-variant="{footer_attr}" data-cta-strategy="{esc(layout_profile.cta_strategy)}" data-market="{market_attr}" data-density="{density_attr}" data-motion="{motion_attr}" data-trust-template="{trust_attr}" data-media-bg="{media_bg_attr}">
  <nav class="topbar" aria-label="Navigation">
    <div class="brand">{logo_block}</div>
    <div class="topbar-links">
      {services_nav}{faq_nav}{gallery_nav}{catalog_nav}<a class="btn topbar-cta" href="#contact">{cta}</a>
    </div>
  </nav>
{hero_html}
{body_html}
  {footer_html}
{back_to_top_block}{motion_script}</body>
</html>
"""
    lower = html.lower()
    for snippet in _FORBIDDEN_SNIPPETS:
        if snippet.lower() in lower:
            raise ValueError(f"forbidden_copy_snippet:{snippet}")
    assert_localization_hygiene(html)
    return html


def _logo_block(business_name: str, *, src: str = "assets/logo.png") -> str:
    safe = html_lib.escape(business_name)
    logo = html_lib.escape(src or "assets/logo.png")
    initials = "".join(w[0] for w in re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", business_name)[:2]) or "VC"
    return (
        f'<img src="{logo}" alt="{safe}" '
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
