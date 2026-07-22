"""Business Product BP1.3 — ChannelConnection domain (stub registry).

Answers only: through which channels can Vector work?

```text
Channel Connections describe communication endpoints.
Channel Connections never send messages.
Channel Connections never receive messages.
Channel Connections never depend on external SDKs.
```
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "channel_connection_domain_v1"

ChannelType = Literal[
    "website",
    "telegram",
    "instagram",
    "facebook",
    "whatsapp",
    "email",
    "other",
]

ChannelStatus = Literal[
    "not_configured",
    "configured",
    "enabled",
    "disabled",
]

ALLOWED_CHANNELS: frozenset[str] = frozenset(
    {
        "website",
        "telegram",
        "instagram",
        "facebook",
        "whatsapp",
        "email",
        "other",
    }
)

ALLOWED_CHANNEL_STATUSES: frozenset[str] = frozenset(
    {
        "not_configured",
        "configured",
        "enabled",
        "disabled",
    }
)

CHANNEL_ORDER: tuple[str, ...] = (
    "website",
    "telegram",
    "instagram",
    "facebook",
    "whatsapp",
    "email",
    "other",
)

# Stub config keys allowed per channel — no secrets / tokens / OAuth.
ALLOWED_CONFIG_KEYS: dict[str, frozenset[str]] = {
    "website": frozenset({"widget_name", "theme", "language"}),
    "telegram": frozenset({"bot_username", "webhook_placeholder"}),
    "instagram": frozenset({"business_account_placeholder"}),
    "facebook": frozenset({"page_placeholder"}),
    "whatsapp": frozenset({"business_number_placeholder"}),
    "email": frozenset({"inbox_address_placeholder"}),
    "other": frozenset({"label", "notes"}),
}

_FORBIDDEN_CONFIG_FRAGMENTS: tuple[str, ...] = (
    "token",
    "secret",
    "password",
    "api_key",
    "apikey",
    "oauth",
    "access_key",
    "private_key",
)


class ChannelConnectionError(ValueError):
    """Invalid Channel Connection operation."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sanitize_configuration(
    channel: str, configuration: dict[str, Any] | None
) -> dict[str, str]:
    raw = configuration or {}
    allowed = ALLOWED_CONFIG_KEYS.get(channel, frozenset())
    clean: dict[str, str] = {}
    for key, value in raw.items():
        key_l = str(key).strip().lower()
        if key_l not in allowed:
            raise ChannelConnectionError(f"unknown_config_key:{key}")
        if any(frag in key_l for frag in _FORBIDDEN_CONFIG_FRAGMENTS):
            raise ChannelConnectionError("secret_config_forbidden")
        text = str(value).strip()
        if len(text) > 500:
            raise ChannelConnectionError("config_value_too_long")
        clean[key_l] = text
    return clean


def _default_display_name(channel: str) -> str:
    labels = {
        "website": "Website Widget",
        "telegram": "Telegram",
        "instagram": "Instagram",
        "facebook": "Facebook",
        "whatsapp": "WhatsApp",
        "email": "Email",
        "other": "Other Channel",
    }
    return labels.get(channel, channel)


@dataclass(frozen=True)
class ChannelConnection:
    """Endpoint registry row — not a messenger runtime."""

    connection_id: str
    profile_id: str
    channel: ChannelType
    display_name: str
    status: ChannelStatus
    configuration: dict[str, str]
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["configuration"] = dict(self.configuration)
        return payload


def new_channel_connection(
    *,
    profile_id: str,
    channel: str,
    display_name: str | None = None,
    status: str = "not_configured",
    configuration: dict[str, Any] | None = None,
) -> ChannelConnection:
    if not profile_id.strip():
        raise ChannelConnectionError("profile_required")
    if channel not in ALLOWED_CHANNELS:
        raise ChannelConnectionError("unknown_channel")
    if status not in ALLOWED_CHANNEL_STATUSES:
        raise ChannelConnectionError("unknown_status")
    config = _sanitize_configuration(channel, configuration)
    if status == "not_configured" and config:
        status = "configured"
    name = (display_name or "").strip() or _default_display_name(channel)
    now = _utc_now_iso()
    return ChannelConnection(
        connection_id=str(uuid4()),
        profile_id=profile_id,
        channel=channel,  # type: ignore[arg-type]
        display_name=name,
        status=status,  # type: ignore[arg-type]
        configuration=config,
        created_at=now,
        updated_at=now,
    )


def apply_channel_update(
    current: ChannelConnection,
    *,
    display_name: str | None = None,
    status: str | None = None,
    configuration: dict[str, Any] | None = None,
) -> ChannelConnection:
    next_status = current.status
    if status is not None:
        if status not in ALLOWED_CHANNEL_STATUSES:
            raise ChannelConnectionError("unknown_status")
        next_status = status  # type: ignore[assignment]
    next_config = current.configuration
    if configuration is not None:
        next_config = _sanitize_configuration(current.channel, configuration)
        if next_status == "not_configured" and next_config:
            next_status = "configured"  # type: ignore[assignment]
    next_name = current.display_name
    if display_name is not None:
        next_name = display_name.strip() or current.display_name
    return replace(
        current,
        display_name=next_name,
        status=next_status,
        configuration=next_config,
        updated_at=_utc_now_iso(),
    )
