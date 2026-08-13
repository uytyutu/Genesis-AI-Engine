"""ChannelProvider protocol — official adapters only; one brain above them."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from app.integration.channel_engine.types import (
    ConnectionStatus,
    InboundMessage,
    NormalizedOutbound,
    ProviderCapability,
)


@runtime_checkable
class ChannelProvider(Protocol):
    """Transport adapter. Must not own AI / Lead / Offer logic."""

    channel_type: str

    def supported_capabilities(self) -> frozenset[ProviderCapability]:
        ...

    def health(
        self,
        memory_dir: Path,
        workspace_id: str,
        *,
        bot_id: str = "",
        connection_id: str = "",
    ) -> ConnectionStatus:
        ...

    def normalize_inbound(
        self,
        payload: dict[str, Any],
        *,
        workspace_id: str = "",
        bot_id: str = "",
    ) -> InboundMessage | None:
        """Return None when the payload should be ignored (no user text, etc.)."""
        ...

    def receive(
        self,
        memory_dir: Path,
        bot_id: str,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Ingest one provider event (webhook update). Existing behaviour preserved per provider."""
        ...

    def send(
        self,
        memory_dir: Path,
        workspace_id: str,
        outbound: NormalizedOutbound,
        *,
        bot_id: str = "",
        connection_id: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        ...
