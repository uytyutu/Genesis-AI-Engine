"""TikTok Horizon — internal Virtus Core content module (Owner only).

Stage 1: trends → ideas → scripts → prompts → quality → human review → queue.
Stage 2: official TikTok OAuth multi-account (INTERNAL_OWNER).
Video generation and publishing remain OFF.
"""

from __future__ import annotations

from modules.tiktok_horizon.gate import is_horizon_enabled, require_horizon_enabled
from modules.tiktok_horizon.service import HorizonService, STAGE1_CAPABILITIES
from modules.tiktok_horizon.visibility import visibility_policy

__all__ = [
    "HorizonService",
    "STAGE1_CAPABILITIES",
    "is_horizon_enabled",
    "require_horizon_enabled",
    "visibility_policy",
]
