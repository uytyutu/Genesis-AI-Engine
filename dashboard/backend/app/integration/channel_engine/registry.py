"""Provider registry — isolated adapters; one failure must not take others down."""

from __future__ import annotations

from typing import Any

from app.integration.channel_engine.provider import ChannelProvider

_REGISTRY: dict[str, ChannelProvider] = {}
_BOOTSTRAPPED = False


def register_provider(provider: ChannelProvider, *, replace: bool = False) -> None:
    key = str(getattr(provider, "channel_type", "") or "").strip().lower()
    if not key:
        raise ValueError("provider.channel_type required")
    if key in _REGISTRY and not replace:
        return
    _REGISTRY[key] = provider


def get_provider(channel_type: str) -> ChannelProvider | None:
    _ensure_defaults()
    return _REGISTRY.get(str(channel_type or "").strip().lower())


def list_providers() -> dict[str, ChannelProvider]:
    _ensure_defaults()
    return dict(_REGISTRY)


def _ensure_defaults() -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    _BOOTSTRAPPED = True
    # Lazy import keeps Telegram optional for unit-importing types alone.
    from app.integration.channel_engine.telegram_provider import TelegramProvider
    from app.integration.channel_engine.whatsapp_provider import WhatsAppProvider

    register_provider(TelegramProvider())
    register_provider(WhatsAppProvider())


def reset_registry_for_tests() -> None:
    """Test helper — clears adapters and re-allows default bootstrap."""
    global _BOOTSTRAPPED
    _REGISTRY.clear()
    _BOOTSTRAPPED = False


def provider_capability_snapshot() -> dict[str, Any]:
    """Internal matrix snapshot for health / future Channels UI."""
    out: dict[str, Any] = {}
    for name, provider in list_providers().items():
        caps = sorted(c.value for c in provider.supported_capabilities())
        out[name] = {"capabilities": caps}
    return out
