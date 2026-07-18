"""Hive OCR — extract text from image URL (project model must support OCR)."""

from __future__ import annotations

from typing import Any

from app.providers.hive.client import HiveClient


def ocr_image_url(client: HiveClient, image_url: str, **extra: Any) -> dict[str, Any]:
    """Submit image URL; exact model fields depend on the Hive project key."""
    return client.task_sync_media_url(image_url, **extra)
