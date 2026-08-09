"""Renderer Strategies — different site architectures (DOM), not section shuffles.

Composition Library selects a Strategy.
Each Strategy owns First Impression + body DOM + rhythm.
LegacyStrategy preserves the pre-Evolution path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class RenderContext:
    """Inputs every Strategy may use — no HTML assembly here."""

    business_name: str
    niche_id: str
    package_id: str
    headline: str
    subtitle: str
    about: str
    cta: str
    phone: str
    email: str
    hours: str
    city: str
    services: tuple[str, ...]
    benefits: tuple[str, ...]
    trust_points: tuple[str, ...]
    ui: dict[str, str]
    hero_video: str = ""
    hero_photo: bool = True
    composition_id: str = ""
    demo: bool = True
    # First Impression Generation — client story arc
    problem_before: str = ""
    emotion_line: str = ""
    trust_line: str = ""
    offer_line: str = ""
    brand_idea: str = ""


@dataclass
class RenderedSite:
    """Concrete DOM pieces — must differ by Strategy, not only CSS."""

    strategy_id: str
    hero_html: str
    body_html: str
    css: str
    js: str = ""
    nav_links_html: str = ""
    hero_layout_attr: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


class RendererStrategy(Protocol):
    id: str
    label: str

    def render(self, ctx: RenderContext) -> RenderedSite: ...


__all__ = [
    "RenderContext",
    "RenderedSite",
    "RendererStrategy",
]
