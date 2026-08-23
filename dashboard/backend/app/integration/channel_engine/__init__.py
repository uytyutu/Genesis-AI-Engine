"""Virtus Channel Engine — one inbox / one brain / many official channel adapters.

Phase 1: TelegramProvider · Phase 2: Unified Inbox · Phase 3: WhatsApp Cloud API foundation.
WhatsApp never reports CONNECTED without App Review + controlled Live E2E.
Instagram / Messenger / AI Office are out of scope here.
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
