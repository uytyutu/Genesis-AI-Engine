"""Hive AI-generated / deepfake detection helpers."""

from __future__ import annotations

from typing import Any

from app.providers.hive.client import HiveClient


def detect_ai_image_url(client: HiveClient, image_url: str, **extra: Any) -> dict[str, Any]:
    """Submit media to the project's AI-detection model (key-bound project)."""
    return client.task_sync_media_url(image_url, **extra)
