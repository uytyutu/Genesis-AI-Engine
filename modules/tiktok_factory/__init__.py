"""TikTok / Media Horizon — dormant factory.

Principle (CEO):
  Spider → recurring problem → frequency check → educational script → human approve → publish → /order

NOT Mission 1. Inactive unless config/features.json tiktok_enabled=true.
Never touch Stripe / Country Desk / Factory Path A.
"""

from __future__ import annotations

from modules.tiktok_factory.gate import is_tiktok_enabled, require_tiktok_enabled
from modules.tiktok_factory.scenario_pipeline import (
    MEDIA_PRINCIPLE_RU,
    ScenarioDraft,
    build_educational_scenario,
    list_supported_channels,
)

__all__ = [
    "MEDIA_PRINCIPLE_RU",
    "ScenarioDraft",
    "build_educational_scenario",
    "is_tiktok_enabled",
    "list_supported_channels",
    "require_tiktok_enabled",
]
