"""Kill switch — shares config/features.json tiktok_enabled with Video Factory."""

from __future__ import annotations

from modules.tiktok_factory.gate import (
    is_tiktok_enabled,
    load_features,
    require_tiktok_enabled,
    set_tiktok_enabled,
)

is_horizon_enabled = is_tiktok_enabled
require_horizon_enabled = require_tiktok_enabled

__all__ = [
    "is_horizon_enabled",
    "require_horizon_enabled",
    "load_features",
    "set_tiktok_enabled",
]
