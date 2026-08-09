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
from app.factory.design_engine import font_link_tags, font_pack_for_niche
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



def _enrich_creative_experience(
    *,
    product_dir,
    hero_html: str,
    dna_exp: str,
    atm_pack_css: str = "",
    css_out: str = "",
) -> tuple[str, str, str, str]:
    """Load CREATIVE_BRIEF + inject WebGL/experience overlays when assets exist."""
    try:
        from pathlib import Path as _P

        from app.factory.creative_direction import load_creative_brief
        from app.factory.experience_language import experience_css, experience_js

        if not product_dir:
            return hero_html, dna_exp, atm_pack_css, css_out
        root = _P(product_dir)
        brief = load_creative_brief(root)
        if brief is None:
            return hero_html, dna_exp, atm_pack_css, css_out

        snip = root / "assets" / "hero_3d_snippet.html"
        if getattr(brief, "recommends_webgl", False) and snip.is_file():
            container = (
                '<div id="virtus-3d-mount" class="virtus-3d-mount" '
                'data-virtus-3d="1" aria-hidden="true"></div>'
            )
            if "virtus-3d-mount" not in (hero_html or "") and "virtus-3d-hero" not in (hero_html or ""):
                # Prefer inject at start of hero section
                if 'class="hero' in hero_html:
                    # after opening hero tag
                    import re as _re

                    hero_html = _re.sub(
                        r"(<section[^>]*class=\"hero[^\"]*\"[^>]*>)",
                        r"\1\n" + container,
                        hero_html,
                        count=1,
                    )
                    if "virtus-3d-mount" not in hero_html:
                        hero_html = container + "\n" + hero_html
                else:
                    hero_html = container + "\n" + hero_html
            if "scene_3d.js" not in (dna_exp or ""):
                dna_exp = (dna_exp or "") + '\n<script src="assets/scene_3d.js" defer></script>\n'

        mode = getattr(brief, "media_mode", None) or brief
        exp_c = experience_css(mode)
        if exp_c and exp_c not in (atm_pack_css or "") and exp_c not in (css_out or ""):
            atm_pack_css = (atm_pack_css or "") + "\n" + exp_c
            if css_out is not None:
                css_out = (css_out or "") + "\n" + exp_c
        exp_j = (experience_js() or "").strip()
        # Bare IIFE without <script> becomes visible page text for clients — never append.
        if exp_j.startswith("<script") and exp_j not in (dna_exp or ""):
            dna_exp = (dna_exp or "") + "\n" + exp_j

        # Studio Renderer 2.0 — Premium digital experience (not bolt-on 3D)
        pkg = str(getattr(brief, "package_id", "") or "").strip().lower()
        if pkg in ("premium", "connected"):
            try:
                from app.factory.studio_renderer_v2 import (
                    studio_experience_js,
                    studio_section_media_css,
                    write_studio_assets,
                )

                write_studio_assets(
                    root,
                    niche_id=str(getattr(brief, "niche_id", "") or ""),
                    package_id=pkg,
                    business_name=str(getattr(brief, "brand_name", "") or ""),
                    metaphor=str(getattr(brief, "visual_metaphor", "") or ""),
                )
                s_css = studio_section_media_css(root / "assets")
                if s_css and s_css not in (atm_pack_css or ""):
                    atm_pack_css = (atm_pack_css or "") + "\n" + s_css
                    if css_out is not None:
                        css_out = (css_out or "") + "\n" + s_css
                # Scripts only in body; factory_service inject_studio_html also wires CDN+CSS in <head>
                if "studio_v2.js" not in (dna_exp or ""):
                    dna_exp = (dna_exp or "") + '\n<script src="assets/studio_v2.js" defer></script>\n'
                _ = studio_experience_js  # assets already written
            except Exception:
                pass
    except Exception:
        pass
    return hero_html, dna_exp, atm_pack_css, css_out



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
    hero_video: str = "",
    catalog: CatalogView | None = None,
    hero_pack_manifest: dict | None = None,
    client_logo: bool = False,
    client_logo_src: str = "assets/logo.png",
    client_gallery: list[str] | None = None,
    brand_style: str | None = None,
    client_trust: dict | None = None,
    media_css: str = "",
    media_background: bool = False,
    composition_plan: object | None = None,
    studio_plan: object | None = None,
    design_dna: object | None = None,
    product_dir: object | None = None,
    approach: str = "",
    contacts: dict | None = None,
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
    # Business Generation demos: invented company brings demo-labeled reviews + FAQ
    if isinstance(client_trust, dict) and (
        client_trust.get("reviews") or client_trust.get("faq") or client_trust.get("demo_content")
    ):
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

    # Real client stats only — never invent years/counts for deliverables.
    # Business Visual Pack may fill qualitative value props (Klar/Schnell/Lokal) so Hero slots are not empty.
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
        if tier in {"business", "premium"}:
            from app.factory.visual_intelligence.business_visual_pack import (
                ensure_business_kpi_ui,
            )

            ui = ensure_business_kpi_ui(ui, package_id=tier, niche=analysis.niche)

    trust_payload = client_trust if isinstance(client_trust, dict) else {}
    # Inject invented company FAQ + demo review label into UI strings
    faq_items = trust_payload.get("faq") if isinstance(trust_payload.get("faq"), list) else []
    for i, item in enumerate(faq_items[:5], start=1):
        if not isinstance(item, dict):
            continue
        q = str(item.get("q") or "").strip()
        a = str(item.get("a") or "").strip()
        if q:
            ui[f"faq_q{i}"] = q
        if a:
            ui[f"faq_a{i}"] = a
    if trust_payload.get("demo_content"):
        ui["reviews_muted"] = str(
            trust_payload.get("demo_label")
            or "Demo-Bewertungen — keine echten Kundenstimmen."
        )
        ui["about_demo_note"] = (
            "Demonstrationsunternehmen für Virtus Core Preview — "
            "erfunden, um eine 5-jährige Marke zu simulieren."
        )

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
    # Prefer Composer plan so meta.hero_layout == HTML data-hero-layout (GWT ZIP).
    layout_market = (market_code or market_design.market_id or "DE").strip().upper()
    plan = composition_plan
    if (
        plan is not None
        and getattr(plan, "layout_profile", None) is not None
        and getattr(plan, "hero_layout", None)
    ):
        layout_profile = plan.layout_profile
        hero_layout_id = str(plan.hero_layout).strip().upper() or "A"
        comp_profile_id = (
            str(getattr(plan, "component_profile", None) or "").strip().upper() or "A"
        )
    else:
        from app.factory.composers.layout_composer import compose_layout_profile
        from app.factory.composers.context import QuestionnaireContext

        layout_profile = compose_layout_profile(
            QuestionnaireContext(
                business_name=analysis.business_name,
                niche=niche_profile.niche_id,
                package_id=tier,
                market_code=layout_market,
                country=layout_market,
            )
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
    font_head = font_link_tags(font_pack_for_niche(niche_profile.niche_id))
    studio_apply: dict = {}
    studio_css = ""
    # Typography Studio SSOT — Brand Personality → pair + metrics (never one font for all)
    try:
        from app.factory.design_dna.typography_studio import (
            decision_as_font_pack,
            emit_typography_studio_css,
            resolve_typography_studio,
        )
        from app.factory.design_engine.fonts import font_link_tags as _flt_studio

        _dna_emo = ""
        _force_pair = ""
        if design_dna is not None:
            _dna_emo = str(getattr(design_dna, "emotion", "") or "")
            _force_pair = str(getattr(design_dna, "typography_pair", "") or "")
        _studio_typo = resolve_typography_studio(
            niche_id=str(getattr(niche_profile, "niche_id", "") or ""),
            emotion=_dna_emo or str(getattr(analysis, "emotion", "") or ""),
            package_id=tier,
            diversity_salt=str(
                getattr(analysis, "diversity_salt", "")
                or getattr(analysis, "business_name", "")
                or ""
            ),
        )
        # Brand Book typography pair wins when DNA carries it
        if _force_pair:
            from app.factory.design_dna.typography_studio import all_type_pairs

            for _p in all_type_pairs():
                if _p.id == _force_pair:
                    from app.factory.design_dna.typography_studio import metrics_for_scale

                    _m = metrics_for_scale(_p.scale, package_id=tier)
                    _studio_typo = {
                        **_studio_typo,
                        "pair": _p.as_dict(),
                        "pair_id": _p.id,
                        "headline": _p.display,
                        "body": _p.body,
                        "google_css_url": _p.google_css_url,
                        "notes": _p.notes + " · brand_book",
                        "metrics": _m.as_dict(),
                        "buttons_weight": _m.btn_weight,
                        "line_height": _m.body_lh,
                        "letter_spacing": _m.tracking_body,
                        "brand_personality": _dna_emo or _studio_typo.get("brand_personality"),
                    }
                    break
        font_head = _flt_studio(decision_as_font_pack(_studio_typo))
        studio_css = emit_typography_studio_css(_studio_typo)
    except Exception:
        pass
    if studio_plan is not None:
        try:
            from app.factory.visual_intelligence.studio.board import StudioPlan
            import re as _re_typo

            def _strip_typo_blocks(css: str) -> str:
                """Drop duplicate Typography Studio / --font-display blocks from plan CSS."""
                if not css:
                    return ""
                # Keep non-typography plan CSS only — studio_css above is SSOT.
                out = _re_typo.sub(
                    r"/\*\s*Typography Studio[\s\S]*?(?=/\*|$)",
                    "",
                    css,
                )
                # Neutralize leftover --font-* so earlier niche tokens cannot fight SSOT
                out = _re_typo.sub(
                    r"--font-(?:display|body|sans)\s*:\s*[^;]+;",
                    "",
                    out,
                )
                return out.strip()

            if isinstance(studio_plan, StudioPlan):
                studio_apply = dict(studio_plan.apply or {})
                plan_css = _strip_typo_blocks(studio_plan.css or "")
                if plan_css:
                    studio_css = (studio_css + "\n" + plan_css) if studio_css else plan_css
                # Fonts stay on Typography Studio decision — ignore plan packs that
                # would desync Google <link> from --font-display SSOT.
            elif isinstance(studio_plan, dict):
                studio_apply = dict(studio_plan.get("apply") or {})
                plan_css = _strip_typo_blocks(str(studio_plan.get("css") or ""))
                if plan_css:
                    studio_css = (studio_css + "\n" + plan_css) if studio_css else plan_css
        except Exception:
            studio_apply = {}

    wa_url = whatsapp_href(whatsapp, analysis.phone) if feat.whatsapp else ""
    show_logo = bool(feat.logo_slot or client_logo)
    logo_src = (client_logo_src or "assets/logo.png").strip() or "assets/logo.png"
    niche_for_mark = getattr(niche_profile, "niche_id", None) or ""
    from app.factory.brand_mark import site_logo_html, short_brand_name

    logo_block = site_logo_html(
        analysis.business_name,
        niche=str(niche_for_mark),
        src=logo_src,
        use_img=show_logo,
    )

    route_url = maps_route_url(
        business_name=analysis.business_name,
        city=city,
        street=street,
        country=maps_country,
    )
    maps_block = ""
    has_place = bool((city or "").strip() or (street or "").strip())
    if feat.maps and has_place:
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
    maps_nav = f' <a href="#maps">{esc(ui["maps"])}</a>' if (feat.maps and has_place) else ""
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

    # ——— Renderer Evolution ———
    # Composition / niche / Dream Brief style → Strategy that owns Hero + body DOM.
    # Legacy falls through to compose_hero + assemble_body.
    composition_id = ""
    if design_dna is not None:
        composition_id = str(getattr(design_dna, "composition", "") or "")
    dream_approach = (approach or "").strip()
    if not dream_approach and isinstance(contacts, dict):
        try:
            from app.factory.dream_brief import dream_brief_from_contacts

            dream_approach = dream_brief_from_contacts(contacts).approach()
        except Exception:
            dream_approach = ""
    try:
        from app.factory.renderers.base import RenderContext
        from app.factory.renderers.registry import get_renderer, strategy_id_for

        _renderer_sid = strategy_id_for(
            niche_id=str(niche_profile.niche_id or analysis.niche or ""),
            package_id=tier,
            composition_id=composition_id,
            approach=dream_approach,
        )
    except Exception:
        _renderer_sid = "classic"

    if _renderer_sid not in ("classic", "legacy"):
        renderer = get_renderer(
            niche_id=str(niche_profile.niche_id or analysis.niche or ""),
            package_id=tier,
            composition_id=composition_id,
            approach=dream_approach,
        )
        rendered = renderer.render(
            RenderContext(
                business_name=analysis.business_name,
                niche_id=str(niche_profile.niche_id or analysis.niche or ""),
                package_id=tier,
                headline=analysis.headline,
                subtitle=analysis.subtitle,
                about=analysis.about_text,
                cta=analysis.cta_label,
                phone=analysis.phone,
                email=analysis.email,
                hours=analysis.hours,
                city=city or "",
                services=tuple(analysis.services or ()),
                benefits=tuple(analysis.benefits or ()),
                trust_points=tuple(analysis.trust_points or ()),
                ui=ui,
                hero_video=hero_video or "",
                hero_photo=bool(hero_photo),
                composition_id=composition_id,
                demo=True,
                problem_before=str(
                    (contacts or {}).get("problem_before")
                    or ((contacts or {}).get("first_impression") or {}).get(
                        "problem_before"
                    )
                    or ""
                )
                if isinstance(contacts, dict)
                else "",
                emotion_line=str(
                    ((contacts or {}).get("first_impression") or {}).get("emotion")
                    or ""
                )
                if isinstance(contacts, dict)
                else "",
                trust_line=str(
                    ((contacts or {}).get("first_impression") or {}).get("trust")
                    or ""
                )
                if isinstance(contacts, dict)
                else "",
                offer_line=str(
                    ((contacts or {}).get("first_impression") or {}).get("offer")
                    or ""
                )
                if isinstance(contacts, dict)
                else "",
                brand_idea=str(
                    ((contacts or {}).get("first_impression") or {}).get("idea")
                    or (contacts or {}).get("commercial_idea")
                    or ""
                )
                if isinstance(contacts, dict)
                else "",
            )
        )
        return _document_from_strategy(
            rendered=rendered,
            analysis=analysis,
            ui=ui,
            feat=feat,
            tier=tier,
            css=css,
            studio_css=studio_css,
            font_head=font_head,
            motion_head=motion_head if css_motion else "",
            motion_script=motion_script,
            back_to_top_block=back_to_top_block,
            logo_block=logo_block,
            page_title=page_title,
            meta_desc=meta_desc,
            seo_extra=seo_extra,
            analytics_block=analytics_block,
            html_lang=html_lang,
            layout_profile=layout_profile,
            niche_profile=niche_profile,
            market_design=market_design,
            city=city,
            use_profile_footer=use_profile_footer,
            profile=profile,
            studio_plan=studio_plan,
            design_dna=design_dna,
            css_motion=css_motion,
            media_background=media_background,
            studio_apply=studio_apply,
            brand_pack=brand_pack,
            contacts=contacts if isinstance(contacts, dict) else None,
            product_dir=product_dir,
        )

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
        hero_video=hero_video,
    )
    css = css + "\n" + hero_comp.css
    from app.factory.ux_polish import ux_polish_css

    css = css + "\n" + ux_polish_css(tier)
    if studio_css:
        css = css + "\n" + studio_css

    dna_obj = design_dna
    dna_treat: dict[str, str] = {}
    dna_attrs = ""
    dna_atm = ""
    dna_exp = ""
    atm_pack_css = ""
    # quality_floor_css is appended LAST (after composer/trust/media) so CONTRAST LOCK wins
    if dna_obj is not None:
        try:
            from app.factory.design_dna.atmosphere_pack import build_atmosphere_pack
            from app.factory.design_dna.brand_book import resolve_brand_book
            from app.factory.design_dna.quality_floor import (
                atmosphere_html,
                experience_js,
            )

            dna_treat = {k: v for k, v in (getattr(dna_obj, "section_treatments", ()) or ())}
            attr_map = getattr(dna_obj, "body_attrs", lambda: {})()
            if attr_map:
                dna_attrs = " " + " ".join(
                    f'{html_lib.escape(k)}="{html_lib.escape(str(v))}"'
                    for k, v in attr_map.items()
                )
            # Atmosphere Pack directs living canvas when Brand Book can be resolved
            try:
                _book = resolve_brand_book(
                    business_name=analysis.business_name,
                    niche_id=str(getattr(niche_profile, "niche_id", "") or analysis.niche or ""),
                    package_id=tier,
                    diversity_salt=str(
                        getattr(analysis, "diversity_salt", "")
                        or analysis.business_name
                        or ""
                    ),
                    city=city or "",
                )
                _pack = build_atmosphere_pack(_book, dna_obj)  # type: ignore[arg-type]
                dna_atm = _pack.html_nodes or atmosphere_html(dna_obj)  # type: ignore[arg-type]
                dna_exp = _pack.js_motion or experience_js(dna_obj)  # type: ignore[arg-type]
                atm_pack_css = _pack.css_layers
            except Exception:
                dna_atm = atmosphere_html(dna_obj)  # type: ignore[arg-type]
                dna_exp = experience_js(dna_obj)  # type: ignore[arg-type]
        except Exception:
            dna_treat = {}
            dna_attrs = ""
            dna_atm = ""
            dna_exp = ""
            atm_pack_css = ""

    hero_html = hero_comp.html
    if css_motion:
        hero_html = hero_html.replace('class="hero ', 'class="hero hero-parallax ', 1)

    try:
        hero_html, dna_exp, atm_pack_css, _ = _enrich_creative_experience(
            product_dir=product_dir,
            hero_html=hero_html,
            dna_exp=dna_exp,
            atm_pack_css=atm_pack_css,
        )
    except Exception:
        pass

    gallery_paths = [p for p in (client_gallery or []) if p]
    trust_evidence = collect_trust_evidence(
        client_trust=trust_payload,
        commitments=analysis.trust_points,
        portfolio_paths=gallery_paths,
        has_maps=bool(feat.maps and has_place),
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
            hero_video=hero_video,
        )
        hero_html = hero_comp.html
        if css_motion:
            hero_html = hero_html.replace('class="hero ', 'class="hero hero-parallax ', 1)
        try:
            hero_html, dna_exp, atm_pack_css, _ = _enrich_creative_experience(
                product_dir=product_dir,
                hero_html=hero_html,
                dna_exp=dna_exp,
                atm_pack_css=atm_pack_css,
            )
        except Exception:
            pass

    # CTA strategy: early/mid → mid_cta slot; late → late_cta; dual → both
    want_mid = bool(feat.mid_cta) and layout_profile.cta_strategy in (
        "early",
        "mid",
        "dual",
    )
    want_late = bool(feat.mid_cta) and layout_profile.cta_strategy in ("late", "dual")
    # Premium Character: glass cards + depth even on cinematic heroes
    cards_for_page = layout_styles.get("cards")
    if tier == "premium" and not cards_for_page:
        cards_for_page = "glass"
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
        include_faq=bool(feat.faq) or bool(faq_items),
        include_reviews=bool(include_testimonials and real_reviews),
        include_mid_cta=want_mid or want_late,
        gallery_paths=gallery_paths,
        client_reviews=trust_evidence.reviews if real_reviews else (),
        cards_override=cards_for_page,
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
    # Reputation Pack — proof that sells before the first call (demo-labeled)
    reputation_html = ""
    reputation_js = ""
    try:
        from pathlib import Path as _Path

        from app.factory.design_dna.brand_book import resolve_brand_book
        from app.factory.design_dna.reputation_pack import (
            build_reputation_pack,
            materialize_reputation_media,
            render_reputation_html,
            reputation_pack_css,
            reputation_pack_js,
        )

        _rep_book = resolve_brand_book(
            business_name=analysis.business_name,
            niche_id=str(getattr(niche_profile, "niche_id", "") or analysis.niche or ""),
            package_id=tier,
            diversity_salt=str(
                getattr(analysis, "diversity_salt", "") or analysis.business_name or ""
            ),
            city=city or "",
        )
        _rep_pack = build_reputation_pack(_rep_book)
        _rep_media: dict[str, str] = {}
        if product_dir is not None:
            _rep_media = materialize_reputation_media(
                _Path(str(product_dir)), _rep_pack, book=_rep_book
            )
        reputation_html = render_reputation_html(
            _rep_pack, section_class=sec, media=_rep_media
        )
        reputation_js = reputation_pack_js()
        css = css + "\n" + reputation_pack_css()
        # Rich process lives inside Reputation — avoid duplicate 3-circle process
        process_inner = ""
    except Exception:
        reputation_html = ""
        reputation_js = ""

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
    if dna_obj is not None:
        try:
            from app.factory.design_dna.quality_floor import quality_floor_css

            css = css + "\n" + quality_floor_css(dna_obj)  # type: ignore[arg-type]
            if atm_pack_css:
                css = css + "\n" + atm_pack_css
        except Exception:
            pass

    brand_attr = esc(brand_pack.id if brand_pack else "auto")
    niche_attr = esc(niche_profile.niche_id)
    hero_attr = esc(hero_comp.layout_id)
    comp_attr = esc(page_sections.profile_id)
    motion_attr = "css" if css_motion else "none"
    market_attr = esc(market_design.market_id)
    density_attr = esc(
        str(studio_apply.get("density") or market_design.density)
    )
    luxury_attr = "1" if studio_apply.get("luxury_mode") else "0"
    industry_attr = esc(str(studio_apply.get("industry_theme") or ""))
    studio_attr = esc(str(studio_apply.get("data_studio") or ""))
    if studio_apply.get("hero_class_extra"):
        extra = str(studio_apply["hero_class_extra"])
        if 'class="hero ' in hero_html:
            hero_html = hero_html.replace('class="hero ', f'class="hero {extra} ', 1)
        elif "class='hero " in hero_html:
            hero_html = hero_html.replace("class='hero ", f"class='hero {extra} ", 1)
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
    if (
        feat.process
        and "process" not in trust_comp.blocks_used
        and not reputation_html.strip()
    ):
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
        # Media-backed panels only — never empty caption tiles
        media_slots: list[tuple[str, str]] = []
        if hero_photo:
            media_slots.append(("assets/hero.jpg", business))
        for i, gp in enumerate(gallery_paths[:2]):
            media_slots.append((gp, esc(ui["services"]) if i == 0 else esc(ui.get("gallery_title") or "Galerie")))
        if len(media_slots) >= 1:
            if len(media_slots) == 1:
                src, cap = media_slots[0]
                showcase_block = f"""
  <section class="{sec} showcase showcase-single" id="showcase">
    <div class="showcase-panel main has-media showcase-full"
         style="background-image:url('{esc(src)}')">
      <span class="cap">{cap}</span>
    </div>
  </section>
"""
            else:
                panels = []
                for i, (src, cap) in enumerate(media_slots[:3]):
                    tone = "main" if i == 0 else ("tone-a" if i == 1 else "tone-b")
                    panels.append(
                        f'<div class="showcase-panel {tone} has-media" '
                        f'style="background-image:url(\'{esc(src)}\')">'
                        f'<span class="cap">{cap}</span></div>'
                    )
                while len(panels) < 3:
                    panels.append(panels[-1])
                showcase_block = f"""
  <section class="{sec} showcase" id="showcase">
    <h2>{esc(ui['showcase_title'])}</h2>
    <p class="muted">{esc(ui['showcase_lead'])}</p>
    <div class="showcase-grid">
      {"".join(panels[:3])}
    </div>
  </section>
"""

    signature_block = ""
    if tier == "premium" and hero_photo:
        sig_eyebrow = esc(ui.get("signature_eyebrow") or "Premium Experience")
        sig_lead = esc(
            ui.get("signature_lead")
            or analysis.subtitle
            or "Atmosphäre, Klarheit und ein Auftritt, der Vertrauen schafft."
        )
        signature_block = f"""
  <section class="premium-signature" id="signature" aria-label="signature">
    <div class="premium-signature-copy">
      <p class="premium-signature-eyebrow">{sig_eyebrow}</p>
      <h2>{business}</h2>
      <p>{sig_lead}</p>
      <a class="{btn_class}" href="#contact">{cta}</a>
    </div>
  </section>
"""

    about_raw = (analysis.about_text or "").strip()
    about_block = ""
    if len(about_raw) >= 40:
        demo_note = ""
        if ui.get("about_demo_note"):
            demo_note = f'<p class="muted" style="margin-top:0.75rem">{esc(ui["about_demo_note"])}</p>'
        about_block = f"""
  <section class="{sec} about">
    <h2>{esc(ui['about'])}</h2>
    <p>{about}</p>
    {demo_note}
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
        "stats": _apply_section_treatment(stats_block, "stats", dna_treat),
        "catalog": catalog_block,
        "services": _apply_section_treatment(
            page_sections.services_html, "services", dna_treat
        ),
        "reputation": _apply_section_treatment(reputation_html, "reputation", dna_treat),
        "mid_cta": _apply_section_treatment(mid_cta_html, "mid_cta", dna_treat),
        "benefits": _apply_section_treatment(
            page_sections.benefits_html, "benefits", dna_treat
        ),
        "trust": _apply_section_treatment(trust_comp.html, "trust", dna_treat),
        "process": _apply_section_treatment(process_block, "process", dna_treat),
        "showcase": _apply_section_treatment(showcase_block, "showcase", dna_treat),
        "gallery": _apply_section_treatment(
            page_sections.gallery_html, "gallery", dna_treat
        ),
        "about": _apply_section_treatment(about_block, "about", dna_treat),
        "faq": _apply_section_treatment(page_sections.faq_html, "faq", dna_treat),
        "calculator": _apply_section_treatment(calc_block, "calculator", dna_treat),
        "reviews": _apply_section_treatment(
            page_sections.reviews_html, "reviews", dna_treat
        ),
        "maps": _apply_section_treatment(maps_block, "maps", dna_treat),
        "late_cta": _apply_section_treatment(late_cta_html, "late_cta", dna_treat),
        "contact": _apply_section_treatment(contact_block, "contact", dna_treat),
    }
    body_html = assemble_body(body_sections, layout_profile.section_order)
    if signature_block.strip():
        sig = _apply_section_treatment(signature_block, "signature", dna_treat)
        body_html = sig.strip() + "\n" + body_html
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
    reputation_nav = (
        ' <a href="#reputation">Reputation</a>' if reputation_html.strip() else ""
    )
    faq_nav = (
        f' <a href="#faq">{esc(ui.get("faq_title") or "FAQ")}</a>'
        if feat.faq
        else ""
    )
    # Marketing sites: no customer registration.
    # Client login / order status lives on stores; site CMS lives in Virtus Core (/client).
    account_nav = ""
    account_block = ""

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
  {font_head}{motion_head}
  <style>
{css}
  </style>
</head>
<body id="top" data-tier="{esc(tier)}" data-brand="{brand_attr}" data-niche="{niche_attr}" data-hero-layout="{hero_attr}" data-comp-profile="{comp_attr}" data-layout-profile="{layout_attr}" data-footer-variant="{footer_attr}" data-cta-strategy="{esc(layout_profile.cta_strategy)}" data-market="{market_attr}" data-density="{density_attr}" data-motion="{motion_attr}" data-trust-template="{trust_attr}" data-media-bg="{media_bg_attr}" data-luxury="{luxury_attr}" data-studio="{studio_attr}" data-industry="{industry_attr}"{dna_attrs}>
  {dna_atm}
  <nav class="topbar" aria-label="Navigation">
    <div class="brand">{logo_block}</div>
    <div class="topbar-links">
      {services_nav}{reputation_nav}{faq_nav}{gallery_nav}{catalog_nav}<a class="btn topbar-cta" href="#contact">{cta}</a>
    </div>
  </nav>
{hero_html}
{body_html}
  {footer_html}
{back_to_top_block}{motion_script}{dna_exp}{reputation_js}</body>
</html>
"""
    lower = html.lower()
    for snippet in _FORBIDDEN_SNIPPETS:
        if snippet.lower() in lower:
            raise ValueError(f"forbidden_copy_snippet:{snippet}")
    assert_localization_hygiene(html)

    # Visual Intelligence Engine — Style + Motion markers (same engine as Store / Platform)
    try:
        from app.factory.visual_intelligence.engine import (
            apply_visual_plan_to_html,
            resolve_visual_plan,
        )

        vie = resolve_visual_plan(
            niche_id=niche_profile.niche_id,
            surface="website",
            package_id=tier,
            motion_tier=(
                "premium"
                if tier == "premium"
                else "business"
                if motion == "css" or tier == "business"
                else "basic"
            ),
            pick_assets=False,
        )
        html = apply_visual_plan_to_html(html, vie)
    except Exception:
        pass

    if studio_plan is not None:
        try:
            from app.factory.visual_intelligence.studio.apply_html import (
                apply_studio_to_html,
            )

            html = apply_studio_to_html(html, studio_plan)  # type: ignore[arg-type]
        except Exception:
            pass

    return html


def _document_from_strategy(
    *,
    rendered: object,
    analysis: AnalysisResult,
    ui: dict[str, str],
    feat: PackageFeatures,
    tier: str,
    css: str,
    studio_css: str,
    font_head: str,
    motion_head: str,
    motion_script: str,
    back_to_top_block: str,
    logo_block: str,
    page_title: str,
    meta_desc: str,
    seo_extra: str,
    analytics_block: str,
    html_lang: str,
    layout_profile: object,
    niche_profile: object,
    market_design: object,
    city: str,
    use_profile_footer: bool,
    profile: object | None,
    studio_plan: object | None,
    design_dna: object | None,
    css_motion: bool,
    media_background: bool,
    studio_apply: dict,
    brand_pack: object | None,
    contacts: dict | None = None,
    product_dir: object | None = None,
) -> str:
    """Assemble full HTML from a Renderer Strategy (distinct DOM architecture)."""
    from pathlib import Path as _Path

    from app.factory.commercial_chrome import (
        build_commercial_chrome,
        social_from_contacts,
        social_icons_html,
    )
    from app.factory.renderers.base import RenderedSite
    from app.factory.ux_polish import ux_polish_css

    assert isinstance(rendered, RenderedSite)
    esc = html_lib.escape
    cta = esc(analysis.cta_label)
    contact_href = {
        "craftsman": "#cc-contact",
        "editorial": "#cc-contact",
        "luxury": "#cc-contact",
        "corporate": "#cc-contact",
        "commerce": "#cc-contact",
        "clinic": "#cc-contact",
        "legal": "#cc-contact",
        "restaurant": "#cc-contact",
        "technology": "#cc-contact",
        "minimal": "#cc-contact",
    }.get(rendered.strategy_id, "#cc-contact")
    css_out = css + "\n" + rendered.css
    if studio_css:
        css_out = css_out + "\n" + studio_css
    css_out = css_out + "\n" + ux_polish_css(tier)

    social_links = social_from_contacts(
        contacts if isinstance(contacts, dict) else None
    )
    chrome_html, chrome_css = build_commercial_chrome(
        business_name=analysis.business_name,
        phone=analysis.phone,
        email=analysis.email,
        city=city or "",
        ui=ui,
        social=social_links,
    )
    css_out = css_out + "\n" + chrome_css

    try:
        from app.factory.renderers.niche_composition import niche_composition_css

        css_out = css_out + "\n" + niche_composition_css(
            str(getattr(niche_profile, "niche_id", "") or "")
        )
    except Exception:
        pass

    topbar_social = (
        '<span class="topbar-socials" aria-label="Social Media">'
        + social_icons_html(
            social_links,
            business_name=analysis.business_name,
            class_name="topbar-social",
        )
        + "</span>"
    )

    dna_attrs = ""
    dna_atm = ""
    dna_exp = ""
    if design_dna is not None:
        try:
            from app.factory.design_dna.atmosphere_pack import build_atmosphere_pack
            from app.factory.design_dna.brand_book import resolve_brand_book
            from app.factory.design_dna.quality_floor import (
                atmosphere_html,
                experience_js,
                quality_floor_css,
            )

            attr_map = getattr(design_dna, "body_attrs", lambda: {})()
            if attr_map:
                dna_attrs = " " + " ".join(
                    f'{html_lib.escape(k)}="{html_lib.escape(str(v))}"'
                    for k, v in attr_map.items()
                )
            try:
                _book = resolve_brand_book(
                    business_name=analysis.business_name,
                    niche_id=str(getattr(niche_profile, "niche_id", "") or ""),
                    package_id=tier,
                    city=city or "",
                )
                _pack = build_atmosphere_pack(_book, design_dna)  # type: ignore[arg-type]
                dna_atm = _pack.html_nodes or atmosphere_html(design_dna)  # type: ignore[arg-type]
                dna_exp = _pack.js_motion or experience_js(design_dna)  # type: ignore[arg-type]
                if _pack.css_layers:
                    css_out = css_out + "\n" + _pack.css_layers
            except Exception:
                dna_atm = atmosphere_html(design_dna)  # type: ignore[arg-type]
                dna_exp = experience_js(design_dna)  # type: ignore[arg-type]
            css_out = css_out + "\n" + quality_floor_css(design_dna)  # type: ignore[arg-type]
        except Exception:
            pass

    
    # Creative / WebGL / experience overlays (Strategy)
    try:
        _hero_s = getattr(rendered, "hero_html", "") or ""
        _hero_s, dna_exp, _a, css_out = _enrich_creative_experience(
            product_dir=product_dir,
            hero_html=_hero_s,
            dna_exp=dna_exp,
            atm_pack_css="",
            css_out=css_out,
        )
        if _hero_s and _hero_s != getattr(rendered, "hero_html", None):
            try:
                object.__setattr__(rendered, "hero_html", _hero_s)
            except Exception:
                try:
                    rendered.hero_html = _hero_s  # type: ignore[attr-defined]
                except Exception:
                    pass
    except Exception:
        pass

    # Reputation Pack on Strategy path (craftsman/clinic/…) — same proof layer as classic
    reputation_html = ""
    reputation_js = ""
    try:
        from app.factory.design_dna.brand_book import resolve_brand_book
        from app.factory.design_dna.reputation_pack import (
            build_reputation_pack,
            materialize_reputation_media,
            render_reputation_html,
            reputation_pack_css,
            reputation_pack_js,
        )

        _rep_book = resolve_brand_book(
            business_name=analysis.business_name,
            niche_id=str(getattr(niche_profile, "niche_id", "") or analysis.niche or ""),
            package_id=tier,
            diversity_salt=str(
                getattr(analysis, "diversity_salt", "") or analysis.business_name or ""
            ),
            city=city or "",
        )
        _rep_pack = build_reputation_pack(_rep_book)
        _rep_media: dict[str, str] = {}
        if product_dir is not None:
            _rep_media = materialize_reputation_media(
                _Path(str(product_dir)), _rep_pack, book=_rep_book
            )
        reputation_html = render_reputation_html(
            _rep_pack, section_class="section", media=_rep_media
        )
        reputation_js = reputation_pack_js()
        css_out = css_out + "\n" + reputation_pack_css()
    except Exception:
        reputation_html = ""
        reputation_js = ""

    reputation_nav = (
        ' <a href="#reputation">Reputation</a>' if reputation_html.strip() else ""
    )

    footer_html = compose_footer(
        variant=getattr(layout_profile, "footer_variant", "compact"),
        business_name=analysis.business_name,
        ui=ui,
        phone=analysis.phone,
        email=analysis.email,
        city=city,
        market_profile=profile if use_profile_footer else None,
    )

    brand_attr = esc(getattr(brand_pack, "id", None) or "auto")
    niche_attr = esc(str(getattr(niche_profile, "niche_id", "") or ""))
    hero_attr = esc(rendered.hero_layout_attr or rendered.strategy_id)
    layout_attr = esc(str(getattr(layout_profile, "id", "strategy")))
    footer_attr = esc(str(getattr(layout_profile, "footer_variant", "compact")))
    market_attr = esc(str(getattr(market_design, "market_id", "DE")))
    density_attr = esc(
        str(studio_apply.get("density") or getattr(market_design, "density", ""))
    )
    luxury_attr = "1" if studio_apply.get("luxury_mode") else "0"
    industry_attr = esc(str(studio_apply.get("industry_theme") or ""))
    studio_attr = esc(str(studio_apply.get("data_studio") or ""))
    motion_attr = "css" if css_motion else "none"
    media_bg_attr = "1" if media_background else "0"
    sid = esc(rendered.strategy_id)

    html = f"""<!DOCTYPE html>
<html lang="{esc(html_lang)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(page_title)}</title>
  <meta name="description" content="{meta_desc}">
  {seo_extra}
  {analytics_block}
  {font_head}{motion_head}
  <style>
{css_out}
  </style>
</head>
<body id="top" data-tier="{esc(tier)}" data-renderer="{sid}" data-brand="{brand_attr}" data-niche="{niche_attr}" data-hero-layout="{hero_attr}" data-comp-profile="strategy" data-layout-profile="{layout_attr}" data-footer-variant="{footer_attr}" data-cta-strategy="strategy" data-market="{market_attr}" data-density="{density_attr}" data-motion="{motion_attr}" data-trust-template="strategy" data-media-bg="{media_bg_attr}" data-luxury="{luxury_attr}" data-studio="{studio_attr}" data-industry="{industry_attr}"{dna_attrs}>
  {dna_atm}
  <nav class="topbar" aria-label="Navigation">
    <div class="brand">{logo_block}</div>
    <div class="topbar-links">
      {rendered.nav_links_html}{reputation_nav}{topbar_social}<a class="btn topbar-cta" href="{contact_href}">{cta}</a>
    </div>
  </nav>
{rendered.hero_html}
{rendered.body_html}
{reputation_html}
  {chrome_html}
  {footer_html}
{back_to_top_block}{motion_script}{dna_exp}{reputation_js}{rendered.js}</body>
</html>
"""

    lower = html.lower()
    for snippet in _FORBIDDEN_SNIPPETS:
        if snippet.lower() in lower:
            raise ValueError(f"forbidden_copy_snippet:{snippet}")
    assert_localization_hygiene(html)

    try:
        from app.factory.visual_intelligence.engine import (
            apply_visual_plan_to_html,
            resolve_visual_plan,
        )

        vie = resolve_visual_plan(
            niche_id=str(getattr(niche_profile, "niche_id", "") or ""),
            surface="website",
            package_id=tier,
            motion_tier=(
                "premium"
                if tier == "premium"
                else "business"
                if css_motion or tier == "business"
                else "basic"
            ),
            pick_assets=False,
        )
        html = apply_visual_plan_to_html(html, vie)
    except Exception:
        pass

    if studio_plan is not None:
        try:
            from app.factory.visual_intelligence.studio.apply_html import (
                apply_studio_to_html,
            )

            html = apply_studio_to_html(html, studio_plan)  # type: ignore[arg-type]
        except Exception:
            pass

    return html


def _apply_section_treatment(html: str, key: str, treatments: dict[str, str]) -> str:
    """Attach sec-treat-* class so Design DNA rhythm CSS can paint the block."""
    treat = (treatments or {}).get(key)
    if not treat or not (html or "").strip():
        return html
    cls = f"sec-treat-{treat}"
    if cls in html:
        return html
    if re.search(r'\bclass="', html):
        return re.sub(r'\bclass="', f'class="{cls} ', html, count=1)
    if re.search(r"\bclass='", html):
        return re.sub(r"\bclass='", f"class='{cls} ", html, count=1)
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
