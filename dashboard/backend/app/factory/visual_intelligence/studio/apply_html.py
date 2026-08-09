"""Apply Digital Creative Studio plan to real HTML (attrs + CSS + hero classes)."""

from __future__ import annotations

import re
from typing import Any

from app.factory.visual_intelligence.studio.board import StudioPlan
from app.factory.visual_intelligence.studio.luxury_director import luxury_director_css
from app.factory.design_engine.fonts import FontPack, font_link_tags


def apply_studio_to_html(html: str, plan: StudioPlan | dict[str, Any]) -> str:
    """Mutate landing/store HTML so director decisions are visible in the product."""
    if isinstance(plan, StudioPlan):
        apply = dict(plan.apply or {})
        css = plan.css or ""
        luxury = plan.luxury_mode
        font_pack = apply.get("font_pack")
    else:
        apply = dict(plan.get("apply") or {})
        css = str(plan.get("css") or "")
        luxury = bool(plan.get("luxury_mode") or apply.get("luxury_mode"))
        font_pack = apply.get("font_pack")
        if not css:
            css = luxury_director_css(enabled=luxury)

    out = html

    # Body attributes — real markers for CSS and Blind Test
    lux = "1" if luxury else "0"
    studio = str(apply.get("data_studio") or "digital_creative_studio_v1")
    density = str(apply.get("density") or "")
    theme = str(apply.get("industry_theme") or "")

    def _inject_body_attrs(m: re.Match[str]) -> str:
        tag = m.group(0)
        extras = [
            f'data-luxury="{lux}"',
            f'data-studio="{studio}"',
        ]
        if density and "data-density=" not in tag:
            extras.append(f'data-density="{_esc_attr(density)}"')
        elif density and "data-density=" in tag:
            tag = re.sub(
                r'\bdata-density=["\'][^"\']*["\']',
                f'data-density="{_esc_attr(density)}"',
                tag,
                count=1,
            )
        if theme:
            extras.append(f'data-industry="{_esc_attr(theme)}"')
        if "data-luxury=" in tag:
            tag = re.sub(r'\bdata-luxury=["\'][^"\']*["\']', f'data-luxury="{lux}"', tag, count=1)
            extras = [e for e in extras if not e.startswith("data-luxury=")]
        if "data-studio=" in tag:
            tag = re.sub(
                r'\bdata-studio=["\'][^"\']*["\']',
                f'data-studio="{_esc_attr(studio)}"',
                tag,
                count=1,
            )
            extras = [e for e in extras if not e.startswith("data-studio=")]
        if not extras:
            return tag
        return tag[:-1] + " " + " ".join(extras) + ">"

    out = re.sub(r"<body\b[^>]*>", _inject_body_attrs, out, count=1, flags=re.I)

    # Hero class extras for Luxury Mode
    hero_extra = str(apply.get("hero_class_extra") or "").strip()
    if hero_extra:
        def _hero_class(m: re.Match[str]) -> str:
            attrs = m.group(1)
            if "class=" in attrs:
                return "<" + m.group(0)[1:].replace(
                    'class="', f'class="{hero_extra} ', 1
                ) if 'class="' in attrs else (
                    re.sub(
                        r"class='([^']*)'",
                        lambda mm: f"class='{hero_extra} {mm.group(1)}'",
                        m.group(0),
                        count=1,
                    )
                )
            return f'<{m.group(0)[1:-1]} class="{hero_extra}">'

        # Prefer first hero section/header/div
        out = re.sub(
            r"<(header|section|div)(\b[^>]*\bclass=[\"'][^\"']*\bhero\b[^\"']*[\"'][^>]*)>",
            lambda m: _inject_class(m.group(0), hero_extra),
            out,
            count=1,
            flags=re.I,
        )

    # Inject director CSS before </head>
    if css.strip():
        block = f'<style id="digital-creative-studio">\n{css}\n</style>\n</head>'
        if "id=\"digital-creative-studio\"" not in out:
            out = re.sub(r"</head>", block, out, count=1, flags=re.I)

    # Typography font links
    if isinstance(font_pack, FontPack):
        links = font_link_tags(font_pack)
        if links and "fonts.googleapis.com" in links:
            # Prefer studio fonts: insert after charset viewport block
            if 'id="studio-fonts"' not in out:
                out = out.replace(
                    "</head>",
                    f'<!-- studio-fonts -->\n{links}</head>',
                    1,
                )

    # Store director markers
    store = apply.get("store") if isinstance(apply.get("store"), dict) else None
    if store:
        decisions = store.get("decisions") or {}
        card = str(decisions.get("card_style") or "")
        banner = str(decisions.get("hero_banner") or "")
        n = decisions.get("first_screen_products")
        attrs = []
        if card:
            attrs.append(f'data-card-style="{_esc_attr(card)}"')
        if banner:
            attrs.append(f'data-hero-banner="{_esc_attr(banner)}"')
        if n is not None:
            attrs.append(f'data-first-screen-products="{int(n)}"')
        if attrs:
            out = re.sub(
                r"<body\b[^>]*>",
                lambda m: m.group(0)[:-1] + " " + " ".join(attrs) + ">",
                out,
                count=1,
                flags=re.I,
            )
        # Luxury merch class on product cards — mutate existing class= safely
        if decisions.get("luxury_merchandising") or card == "premium":
            def _premium_card(m: re.Match[str]) -> str:
                tag = m.group(0)
                if "data-card-tier=" in tag:
                    return tag
                if re.search(r'\bclass="', tag):
                    tag = re.sub(
                        r'\bclass="([^"]*)"',
                        lambda mm: f'class="{mm.group(1)} product-card product-card--premium"',
                        tag,
                        count=1,
                    )
                elif re.search(r"\bclass='", tag):
                    tag = re.sub(
                        r"\bclass='([^']*)'",
                        lambda mm: f"class='{mm.group(1)} product-card product-card--premium'",
                        tag,
                        count=1,
                    )
                else:
                    tag = tag[:-1] + ' class="product-card product-card--premium">'
                if "data-card-tier=" not in tag:
                    tag = tag[:-1] + ' data-card-tier="premium">'
                return tag

            out = re.sub(
                r"<article\b[^>]*\bdata-product-card\b[^>]*>",
                _premium_card,
                out,
                count=12,
                flags=re.I,
            )
            store_css = """
/* Store Director — premium cards */
[data-product-card][data-card-tier="premium"],
.product-card--premium {
  border-radius: 1.1rem;
  box-shadow: 0 16px 40px rgba(15,23,42,.10);
  transition: transform .35s ease, box-shadow .35s ease;
}
.product-card--premium:hover {
  transform: translateY(-4px);
  box-shadow: 0 22px 48px rgba(15,23,42,.14);
}
"""
            if "store-director-css" not in out:
                out = out.replace(
                    "</head>",
                    f'<style id="store-director-css">{store_css}</style>\n</head>',
                    1,
                )

    # Business directors — mutate HTML for conversion / trust / perf / a11y / locale
    from app.factory.visual_intelligence.studio.conversion_director import (
        apply_conversion_html,
        score_conversion_html,
    )
    from app.factory.visual_intelligence.studio.trust_director import apply_trust_html
    from app.factory.visual_intelligence.studio.performance_director import (
        apply_performance_html,
        score_performance_html,
    )
    from app.factory.visual_intelligence.studio.accessibility_director import (
        apply_accessibility_html,
    )
    from app.factory.visual_intelligence.studio.localization_director import (
        apply_localization_html,
    )

    conv = apply.get("conversion") if isinstance(apply.get("conversion"), dict) else {}
    trust = apply.get("trust") if isinstance(apply.get("trust"), dict) else {}
    perf = apply.get("performance") if isinstance(apply.get("performance"), dict) else {}
    a11y = apply.get("accessibility") if isinstance(apply.get("accessibility"), dict) else {}
    loc = apply.get("localization") if isinstance(apply.get("localization"), dict) else {}

    if conv:
        out = apply_conversion_html(out, conv)
    elif apply.get("require_mid_cta") or apply.get("cta_after_services"):
        out = apply_conversion_html(
            out, {"apply": {"require_mid_cta": True, "cta_after_services": True}}
        )

    if trust:
        out = apply_trust_html(out, trust)
    elif apply.get("trust_density"):
        out = apply_trust_html(
            out,
            {
                "apply": {
                    "trust_density": apply.get("trust_density"),
                    "certs_near_hero": apply.get("certs_near_hero"),
                    "map_with_contacts": apply.get("map_with_contacts"),
                }
            },
        )

    perf_score = score_performance_html(out, luxury_mode=luxury)
    if perf:
        out = apply_performance_html(out, perf, perf_score)
    else:
        out = apply_performance_html(
            out,
            {"apply": {"prefer_static_hero": apply.get("prefer_static_hero", True)}},
            perf_score,
        )

    if a11y:
        out = apply_accessibility_html(out, a11y)
    else:
        out = apply_accessibility_html(out, {"apply": {"require_alt": True, "skip_link": True}})

    if loc:
        out = apply_localization_html(out, loc)
    elif apply.get("style") or apply.get("market_code"):
        out = apply_localization_html(
            out,
            {
                "apply": {
                    "style": apply.get("style"),
                    "portfolio_weight": apply.get("portfolio_weight"),
                    "social_proof_weight": apply.get("social_proof_weight"),
                    "market_code": apply.get("market_code"),
                    "legal_pack": apply.get("legal_pack"),
                }
            },
        )

    # Stash conversion snapshot for callers (non-serialized marker via comment)
    conv_score = score_conversion_html(out)
    if conv_score.get("recommendations"):
        tip = str(conv_score["recommendations"][0])[:120]
        if "conversion-director-note" not in out:
            out = out.replace(
                "</head>",
                f'<!-- conversion-director-note: {_esc_attr(tip)} -->\n</head>',
                1,
            )

    return out


def _inject_class(tag: str, extra: str) -> str:
    if re.search(r'\bclass="', tag):
        return re.sub(r'\bclass="', f'class="{extra} ', tag, count=1)
    if re.search(r"\bclass='", tag):
        return re.sub(r"\bclass='", f"class='{extra} ", tag, count=1)
    return tag[:-1] + f' class="{extra}">'


def _esc_attr(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
    )
