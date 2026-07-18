"""Hive visual / text moderation helpers."""

from __future__ import annotations

from typing import Any

from app.providers.hive.client import HiveClient


def moderate_image_url(client: HiveClient, image_url: str, **extra: Any) -> dict[str, Any]:
    return client.task_sync_media_url(image_url, **extra)


def moderate_text(client: HiveClient, text: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"text_data": text, **extra}
    return client.task_sync(payload)
