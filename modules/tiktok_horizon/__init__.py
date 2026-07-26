"""TikTok Horizon — internal Virtus Core content module (owner accounts only).

Stage 1: trends → ideas → scripts → prompts → quality → human review → queue.
Video generation and publishing are deliberately OFF.
"""

from __future__ import annotations

from modules.tiktok_horizon.gate import is_horizon_enabled, require_horizon_enabled
from modules.tiktok_horizon.service import HorizonService, STAGE1_CAPABILITIES

__all__ = [
    "HorizonService",
    "STAGE1_CAPABILITIES",
    "is_horizon_enabled",
    "require_horizon_enabled",
]
