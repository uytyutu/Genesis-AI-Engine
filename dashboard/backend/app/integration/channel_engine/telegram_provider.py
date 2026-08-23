"""TelegramProvider — thin adapter over existing workspace_bot_runtime (do not rewrite Bot API path)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from app.integration import workspace_bot_runtime as runtime
from app.integration.channel_engine.types import (
    ConnectionStatus,
    InboundMessage,
    MessageDirection,
    MessageType,
    NormalizedOutbound,
    ProviderCapability,
)

_TELEGRAM_CAPS = frozenset(
    {
        ProviderCapability.SEND_TEXT,
        ProviderCapability.RECEIVE_TEXT,
        ProviderCapability.SEND_IMAGE,
        ProviderCapability.RECEIVE_IMAGE,
        ProviderCapability.SEND_VIDEO,
        ProviderCapability.RECEIVE_VIDEO,
        ProviderCapability.SEND_DOCUMENT,
        ProviderCapability.RECEIVE_DOCUMENT,
        ProviderCapability.SEND_AUDIO,
        ProviderCapability.RECEIVE_AUDIO,
        ProviderCapability.BUTTONS,
    }
)


class TelegramProvider:
    """Official Telegram Bot API transport. AI replies stay in generate_bot_reply."""

    channel_type = "telegram"

    def supported_capabilities(self) -> frozenset[ProviderCapability]:
        return _TELEGRAM_CAPS

    def health(
        self,
        memory_dir: Path,
        workspace_id: str,
        *,
        bot_id: str = "",
        connection_id: str = "",
    ) -> ConnectionStatus:
        if not bot_id:
            return ConnectionStatus.NOT_CONNECTED
        conn = runtime.find_telegram_connection(memory_dir, workspace_id, bot_id)
        if not conn or not str(conn.get("token") or "").strip():
            return ConnectionStatus.NOT_CONNECTED
        return ConnectionStatus.CONNECTED

    def normalize_inbound(
        self,
        payload: dict[str, Any],
        *,
        workspace_id: str = "",
        bot_id: str = "",
    ) -> InboundMessage | None:
        message = payload.get("message") if isinstance(payload.get("message"), dict) else None
        if not message:
            return None
        chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
        chat_id = chat.get("id")
        text = str(message.get("text") or message.get("caption") or "").strip()
        if chat_id is None or not text:
            return None
        from_user = message.get("from") if isinstance(message.get("from"), dict) else {}
        msg_id = message.get("message_id")
        return InboundMessage(
            channel_type=self.channel_type,
            workspace_id=str(workspace_id or ""),
            conversation_external_id=str(chat_id),
            external_user_id=str(from_user.get("id") or chat_id),
            text=text,
            message_type=MessageType.TEXT,
            direction=MessageDirection.INBOUND,
            external_message_id=str(msg_id or ""),
            sender_name=str(
                from_user.get("first_name")
                or from_user.get("username")
                or ""
            ).strip(),
            sender_username=str(from_user.get("username") or "").strip(),
            bot_id=str(bot_id or ""),
            metadata={"session_key": f"tg:{chat_id}"},
            raw_reference={"update_id": payload.get("update_id"), "chat_id": chat_id},
        )

    def receive(
        self,
        memory_dir: Path,
        bot_id: str,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Delegate to existing Telegram handler — behaviour must stay identical."""
        llm_chat: Callable[..., dict[str, Any]] | None = kwargs.get("llm_chat")
        send: Callable[[str, int | str, str], dict[str, Any]] | None = kwargs.get("send")
        result = runtime.handle_telegram_update(
            memory_dir,
            bot_id,
            payload,
            llm_chat=llm_chat,
            send=send,
        )
        owned = runtime.find_bot_owner(memory_dir, bot_id)
        workspace_id = owned[0] if owned else ""
        inbound = self.normalize_inbound(
            payload, workspace_id=workspace_id, bot_id=bot_id
        )
        out = dict(result)
        out["channel_type"] = self.channel_type
        if inbound is not None:
            out["normalized"] = {
                "conversation_external_id": inbound.conversation_external_id,
                "external_user_id": inbound.external_user_id,
                "text": inbound.text,
                "session_key": inbound.metadata.get("session_key"),
            }
        return out

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
        if self.health(memory_dir, workspace_id, bot_id=bot_id) != ConnectionStatus.CONNECTED:
            return {"ok": False, "error": "CHANNEL_UNAVAILABLE", "channel_type": self.channel_type}
        conn = runtime.find_telegram_connection(memory_dir, workspace_id, bot_id)
        token = str((conn or {}).get("token") or "")
        if not token:
            return {"ok": False, "error": "AUTH_ERROR", "channel_type": self.channel_type}
        send_fn = kwargs.get("send") or runtime.send_telegram_message
        sent = send_fn(token, outbound.conversation_external_id, outbound.text)
        return {
            "ok": bool(sent.get("ok")),
            "channel_type": self.channel_type,
            "telegram": sent,
        }
