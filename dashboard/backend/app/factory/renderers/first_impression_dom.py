"""Shared First Impression DOM — Story → Emotion → Trust → Offer → CTA.

Not Photo → H1 → Button.
Used by Renderer Strategies; does not add page sections.
"""

from __future__ import annotations

import html as html_lib

from app.factory.renderers.base import RenderContext

_esc = html_lib.escape


def impression_lines(ctx: RenderContext) -> dict[str, str]:
    trust = ctx.trust_line or (
        ctx.trust_points[0] if ctx.trust_points else ""
    )
    return {
        "problem": (ctx.problem_before or "").strip(),
        "story": (ctx.headline or "").strip(),
        "emotion": (ctx.emotion_line or "").strip(),
        "trust": trust.strip(),
        "offer": (ctx.offer_line or ctx.subtitle or "").strip(),
        "idea": (ctx.brand_idea or "").strip(),
        "cta": (ctx.cta or "").strip(),
    }


def first_impression_copy_html(
    ctx: RenderContext,
    *,
    cta_href: str,
    cta_class: str = "fi-cta",
    extra_cta_html: str = "",
) -> str:
    """Markup arc only — Strategy wraps with its own shell/media."""
    L = impression_lines(ctx)
    problem = (
        f'<p class="fi-problem" data-fi="problem">{_esc(L["problem"])}</p>'
        if L["problem"]
        else ""
    )
    emotion = (
        f'<p class="fi-emotion" data-fi="emotion">{_esc(L["emotion"])}</p>'
        if L["emotion"]
        else ""
    )
    trust = (
        f'<p class="fi-trust" data-fi="trust">{_esc(L["trust"])}</p>'
        if L["trust"]
        else ""
    )
    offer = (
        f'<p class="fi-offer" data-fi="offer">{_esc(L["offer"])}</p>'
        if L["offer"]
        else ""
    )
    idea = (
        f'<p class="fi-idea" data-fi="idea">{_esc(L["idea"])}</p>'
        if L["idea"] and L["idea"] != L["story"]
        else ""
    )
    return f"""
    <div class="fi-arc" data-stage="first-impression-generation" data-first-impression="1">
      {problem}
      <h1 data-fi="story">{_esc(L["story"])}</h1>
      {emotion}
      {trust}
      {offer}
      {idea}
      <div class="fi-actions" data-fi="cta">
        <a class="{_esc(cta_class)}" href="{_esc(cta_href)}">{_esc(L["cta"])}</a>
        {extra_cta_html}
      </div>
    </div>"""


_FI_BASE_CSS = """
/* First Impression Generation — arc rhythm + readable ink (never wash into photo) */
.fi-arc { display: flex; flex-direction: column; gap: .75rem; }
.fi-arc h1 {
  margin: 0;
  color: inherit;
  font-weight: 600;
  line-height: 1.08;
}
.fi-problem {
  margin: 0; font-size: .78rem; letter-spacing: .06em;
  text-transform: uppercase; max-width: 42ch; line-height: 1.45;
  color: inherit; opacity: .7;
}
.fi-emotion { margin: 0; max-width: 36ch; line-height: 1.5; color: inherit; opacity: .92; }
.fi-trust { margin: 0; font-size: .92rem; max-width: 34ch; color: inherit; opacity: .85; }
.fi-offer { margin: 0; max-width: 40ch; line-height: 1.55; color: inherit; opacity: .92; }
.fi-idea {
  margin: .15rem 0 0; font-size: .8rem;
  font-style: italic; max-width: 36ch; color: inherit; opacity: .65;
}
.fi-actions { display: flex; flex-wrap: wrap; gap: .6rem; margin-top: .55rem; }
"""


__all__ = [
    "first_impression_copy_html",
    "impression_lines",
    "_FI_BASE_CSS",
]
