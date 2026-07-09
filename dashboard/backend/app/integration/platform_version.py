"""Foundation F5 — platform version manifest (read-only)."""

from __future__ import annotations

import os
from datetime import datetime, timezone

MANIFEST_VERSION = "foundation-platform-version-1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_platform_version_payload(*, brain_version: str) -> dict[str, str | list[str]]:
    return {
        "manifest_version": MANIFEST_VERSION,
        "platform": "virtus-core",
        "brain_version": brain_version,
        "build_label": os.getenv("GENESIS_BUILD_LABEL", "dev"),
        "generated_at": _utc_now(),
        "capabilities_ref": "capability_registry",
        "features_ref": "feature_registry",
        "update_channel": os.getenv("GENESIS_UPDATE_CHANNEL", "manual"),
    }
