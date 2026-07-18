"""Capability ids for Hive — Horizon until Path A Gate 1 PASS."""

from __future__ import annotations

import os
from typing import Any


HIVE_CAPABILITIES: tuple[dict[str, Any], ...] = (
    {
        "id": "hive_moderation",
        "label": "Hive · content moderation",
        "module": "app.providers.hive.moderation",
    },
    {
        "id": "hive_ocr",
        "label": "Hive · OCR",
        "module": "app.providers.hive.ocr",
    },
    {
        "id": "hive_ai_detection",
        "label": "Hive · AI / deepfake detection",
        "module": "app.providers.hive.ai_detection",
    },
)


def hive_status() -> dict[str, Any]:
    key_set = bool((os.getenv("HIVE_API_KEY") or "").strip())
    return {
        "provider": "hive",
        "configured": key_set,
        "base_url": (os.getenv("HIVE_API_URL") or "https://api.thehive.ai").strip(),
        "capabilities": [c["id"] for c in HIVE_CAPABILITIES],
        "wired_into_path_a": False,
        "notes": "Platform module only — not used by Factory Path A until CEO enables.",
    }
