"""ClassicRenderer — former Legacy; shrink coverage toward 0% over time.

Does not emit DOM — signals fall-through to compose_hero + assemble_body.
KPI: measure % of niches still on Classic and drive it down.
"""

from __future__ import annotations

from app.factory.renderers.base import RenderContext, RenderedSite


class ClassicRenderer:
    id = "classic"
    label = "Classic section assembler (shrink toward 0%)"

    def render(self, ctx: RenderContext) -> RenderedSite:
        raise RuntimeError(
            "ClassicRenderer does not render DOM; use build_landing_html classic path"
        )


# Back-compat alias — do not use in new code
LegacyRenderer = ClassicRenderer


__all__ = ["ClassicRenderer", "LegacyRenderer"]
