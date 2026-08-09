"""Renderer Strategies — DOM architectures for Virtus Core Factory."""

from app.factory.renderers.base import RenderContext, RenderedSite
from app.factory.renderers.registry import (
    get_renderer,
    renderer_coverage,
    strategy_id_for,
)

__all__ = [
    "RenderContext",
    "RenderedSite",
    "get_renderer",
    "renderer_coverage",
    "strategy_id_for",
]
