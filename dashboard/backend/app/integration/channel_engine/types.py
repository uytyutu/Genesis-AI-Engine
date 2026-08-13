"""Normalized channel types for Virtus Channel Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


CHANNEL_TYPES: tuple[str, ...] = (
    "telegram",
    "whatsapp",
    "messenger",
    "instagram",
    "webchat",
    "email",
)


class ConnectionStatus(str, Enum):
    NOT_CONNECTED = "NOT_CONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    REAUTH_REQUIRED = "REAUTH_REQUIRED"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"
    # Meta / WhatsApp honesty — never treat as live Connected without E2E
    SETUP_REQUIRED = "SETUP_REQUIRED"
    APP_REVIEW_REQUIRED = "APP_REVIEW_REQUIRED"
    AVAILABLE = "AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class MessageDirection(str, Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class MessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    VOICE = "VOICE"
    DOCUMENT = "DOCUMENT"
    LOCATION = "LOCATION"
    CONTACT = "CONTACT"
    STICKER = "STICKER"
    REACTION = "REACTION"
    SYSTEM = "SYSTEM"
    UNKNOWN = "UNKNOWN"


class ProviderCapability(str, Enum):
    SEND_TEXT = "SEND_TEXT"
    RECEIVE_TEXT = "RECEIVE_TEXT"
    SEND_IMAGE = "SEND_IMAGE"
    RECEIVE_IMAGE = "RECEIVE_IMAGE"
    SEND_VIDEO = "SEND_VIDEO"
    RECEIVE_VIDEO = "RECEIVE_VIDEO"
    SEND_DOCUMENT = "SEND_DOCUMENT"
    RECEIVE_DOCUMENT = "RECEIVE_DOCUMENT"
    SEND_AUDIO = "SEND_AUDIO"
    RECEIVE_AUDIO = "RECEIVE_AUDIO"
    BUTTONS = "BUTTONS"
    QUICK_REPLIES = "QUICK_REPLIES"
    RICH_MESSAGES = "RICH_MESSAGES"
    TEMPLATED_MESSAGES = "TEMPLATED_MESSAGES"
    REACTIONS = "REACTIONS"
    READ_RECEIPTS = "READ_RECEIPTS"
    TYPING = "TYPING"


@dataclass(frozen=True)
class InboundMessage:
    """Provider-agnostic inbound message (AI Employee never needs raw provider JSON)."""

    channel_type: str
    workspace_id: str
    conversation_external_id: str
    external_user_id: str
    text: str
    message_type: MessageType = MessageType.TEXT
    direction: MessageDirection = MessageDirection.INBOUND
    external_message_id: str = ""
    sender_name: str = ""
    sender_username: str = ""
    bot_id: str = ""
    channel_connection_id: str = ""
    attachments: tuple[dict[str, Any], ...] = ()
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_reference: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedOutbound:
    conversation_external_id: str
    text: str
    message_type: MessageType = MessageType.TEXT
    metadata: dict[str, Any] = field(default_factory=dict)
