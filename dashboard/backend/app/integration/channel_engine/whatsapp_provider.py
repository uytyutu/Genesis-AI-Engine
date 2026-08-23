"""WhatsAppProvider — Cloud API foundation (Phase 3).

Official Meta WhatsApp Cloud API only.
Never reports CONNECTED / live until App Review + controlled E2E PASS.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.channel_engine.types import (
    ConnectionStatus,
    InboundMessage,
    MessageDirection,
    MessageType,
    NormalizedOutbound,
    ProviderCapability,
)
from app.integration.channel_engine import whatsapp_cloud as wa


_WA_CAPS = frozenset(
    {
        ProviderCapability.SEND_TEXT,
        ProviderCapability.RECEIVE_TEXT,
        ProviderCapability.SEND_IMAGE,
        ProviderCapability.RECEIVE_IMAGE,
        ProviderCapability.SEND_DOCUMENT,
        ProviderCapability.RECEIVE_DOCUMENT,
        ProviderCapability.TEMPLATED_MESSAGES,
        ProviderCapability.BUTTONS,
    }
)


class WhatsAppProvider:
    channel_type = "whatsapp"

    def supported_capabilities(self) -> frozenset[ProviderCapability]:
        return _WA_CAPS

    def health(
        self,
        memory_dir: Path,
        workspace_id: str,
        *,
        bot_id: str = "",
        connection_id: str = "",
    ) -> ConnectionStatus:
        status = wa.whatsapp_foundation_status()
        code = str(status.get("status") or "SETUP_REQUIRED")
        try:
            return ConnectionStatus(code)
        except ValueError:
            return ConnectionStatus.SETUP_REQUIRED

    def foundation_status(self) -> dict[str, Any]:
        return wa.whatsapp_foundation_status()

    def normalize_inbound(
        self,
        payload: dict[str, Any],
        *,
        workspace_id: str = "",
        bot_id: str = "",
    ) -> InboundMessage | None:
        events = wa.normalize_whatsapp_webhook(payload)
        if not events:
            return None
        ev = events[0]
        return InboundMessage(
            channel_type=self.channel_type,
            workspace_id=str(workspace_id or ""),
            conversation_external_id=str(ev.get("conversation_external_id") or ""),
            external_user_id=str(ev.get("external_user_id") or ""),
            text=str(ev.get("text") or ""),
            message_type=MessageType.TEXT,
            direction=MessageDirection.INBOUND,
            external_message_id=str(ev.get("external_message_id") or ""),
            sender_name=str(ev.get("sender_name") or ""),
            bot_id=str(bot_id or ""),
            metadata={
                "phone_number_id": ev.get("phone_number_id"),
                "waba_id": ev.get("waba_id"),
                "foundation_only": True,
            },
            raw_reference={"provider": "whatsapp_cloud_api"},
        )

    def receive(
        self,
        memory_dir: Path,
        bot_id: str,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Foundation receive: normalize + ack. Does NOT call generate_bot_reply."""
        events = wa.normalize_whatsapp_webhook(payload if isinstance(payload, dict) else {})
        inbound = self.normalize_inbound(payload if isinstance(payload, dict) else {}, bot_id=bot_id)
        return {
            "ok": True,
            "channel_type": self.channel_type,
            "live": False,
            "delivery": "foundation_ack_only",
            "status": self.foundation_status().get("status"),
            "events": len(events),
            "normalized": (
                {
                    "conversation_external_id": inbound.conversation_external_id,
                    "external_user_id": inbound.external_user_id,
                    "text": inbound.text,
                }
                if inbound
                else None
            ),
            "note": "WhatsApp inbound accepted for foundation only — AI Employee Live not enabled.",
        }

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
        # Hard stop: no production outbound until Live E2E + App Review.
        status = self.foundation_status()
        return {
            "ok": False,
            "error": "APP_REVIEW_REQUIRED",
            "channel_type": self.channel_type,
            "status": status.get("status"),
            "detail": status.get("note"),
            "live": False,
        }
