"""Shared Design Engine — tokens for Website Factory (Store later).

Website Path A and Store Factory should eventually consume the same palette,
typography, radii, and motion hints so both feel like Virtus Core.
"""

from __future__ import annotations

from app.factory.design_engine.fonts import FontPack, font_link_tags, font_pack_for_niche
from app.factory.design_engine.tokens import (
    DesignTokens,
    emit_css_vars,
    resolve_for_niche,
)

__all__ = [
    "DesignTokens",
    "FontPack",
    "emit_css_vars",
    "font_link_tags",
    "font_pack_for_niche",
    "resolve_for_niche",
]
