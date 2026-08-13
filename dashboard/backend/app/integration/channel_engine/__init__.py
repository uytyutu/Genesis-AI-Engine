"""Virtus Channel Engine — one inbox / one brain / many official channel adapters.

Phase 1: abstraction + TelegramProvider wrapping existing workspace_bot_runtime.
Does not implement AI Office, Meta messaging, or Unified Inbox UI.
"""

from __future__ import annotations

from app.integration.channel_engine.provider import ChannelProvider
from app.integration.channel_engine.registry import get_provider, list_providers, register_provider
from app.integration.channel_engine.types import (
    CHANNEL_TYPES,
    ConnectionStatus,
    InboundMessage,
    MessageDirection,
    MessageType,
    NormalizedOutbound,
    ProviderCapability,
)

__all__ = [
    "CHANNEL_TYPES",
    "ChannelProvider",
    "ConnectionStatus",
    "InboundMessage",
    "MessageDirection",
    "MessageType",
    "NormalizedOutbound",
    "ProviderCapability",
    "get_provider",
    "list_providers",
    "register_provider",
]
