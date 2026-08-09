"""Design tokens resolved per niche for Website (and later Store) Factory."""

from __future__ import annotations

from dataclasses import dataclass

from app.factory.design_engine.fonts import FontPack, font_pack_for_niche


@dataclass(frozen=True)
class DesignTokens:
    niche_id: str
    primary: str
    primary_dark: str
    accent: str
    hero_gradient: str
    ink: str
    muted: str
    surface: str
    line: str
    radius: str
    btn_radius: str
    card_radius: str
    shadow: str
    letter_spacing: str
    btn_weight: str
    font_pack: FontPack

    @property
    def font_body(self) -> str:
        return self.font_pack.body

    @property
    def font_display(self) -> str:
        return self.font_pack.display


def resolve_for_niche(niche_id: str | None) -> DesignTokens:
    """Resolve Design Engine tokens from niche_profiles + font packs."""
    from app.factory.niche_profiles import resolve_niche_profile

    profile = resolve_niche_profile(niche_id)
    s = profile.style
    pack = font_pack_for_niche(profile.niche_id)
    # Prefer Design Engine font packs; niche_profiles may still carry legacy stacks.
    return DesignTokens(
        niche_id=profile.niche_id,
        primary=s.primary,
        primary_dark=s.primary_dark,
        accent=s.accent,
        hero_gradient=s.hero_gradient,
        ink=s.ink,
        muted=s.muted,
        surface=s.surface,
        line=s.line,
        radius=s.radius,
        btn_radius=s.btn_radius,
        card_radius=s.card_radius,
        shadow=s.shadow,
        letter_spacing=s.letter_spacing,
        btn_weight=s.btn_weight,
        font_pack=pack,
    )


def emit_css_vars(tokens: DesignTokens) -> str:
    """CSS custom properties + niche body rules for Path A landings."""
    nid = tokens.niche_id
    return f"""
    /* Design Engine · Niche Design System: {nid} */
    body[data-niche="{nid}"] {{
      --p: {tokens.primary};
      --pd: {tokens.primary_dark};
      --acc: {tokens.accent};
      --ink: {tokens.ink};
      --muted: {tokens.muted};
      --surface: {tokens.surface};
      --line: {tokens.line};
      --radius: {tokens.radius};
      --btn-radius: {tokens.btn_radius};
      --card-radius: {tokens.card_radius};
      --font-body: {tokens.font_body};
      --font-display: {tokens.font_display};
      font-family: var(--font-body);
      color: var(--ink);
    }}
    body[data-niche="{nid}"] .hero h1,
    body[data-niche="{nid}"] .section h2,
    body[data-niche="{nid}"] .mid-cta h2 {{
      font-family: var(--font-display);
      letter-spacing: {tokens.letter_spacing};
    }}
    body[data-niche="{nid}"] .btn {{
      border-radius: var(--btn-radius);
      font-weight: {tokens.btn_weight};
    }}
    body[data-niche="{nid}"] .service-card,
    body[data-niche="{nid}"] .process-card,
    body[data-niche="{nid}"] .faq-item,
    body[data-niche="{nid}"] .client-photo,
    body[data-niche="{nid}"] .product-card,
    body[data-niche="{nid}"] .mid-cta {{
      border-radius: var(--card-radius);
      box-shadow: {tokens.shadow};
    }}
    body[data-niche="{nid}"] .brand img,
    body[data-niche="{nid}"] .brand .logo-fallback {{
      border-radius: {tokens.radius};
    }}
    body[data-niche="{nid}"] .trust-pill {{
      border-radius: var(--btn-radius);
    }}
    body[data-niche="{nid}"] input,
    body[data-niche="{nid}"] textarea,
    body[data-niche="{nid}"] select,
    body[data-niche="{nid}"] .contact-form button {{
      border-radius: {tokens.radius};
    }}
"""
