"""Hive AI provider — moderation, OCR, AI-detection (not wired into Path A)."""

from app.providers.hive.client import HiveClient, HiveConfig, HiveError

__all__ = ["HiveClient", "HiveConfig", "HiveError"]
