"""Business Product BP1.3 — ChannelConnectionFacade."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.channel_connection import ChannelConnectionError
from app.portal.channel_connection_service import ChannelConnectionService
from app.portal.channel_connection_store import (
    ChannelConnectionStore,
    InMemoryChannelConnectionStore,
)
from app.portal.channel_connection_view import ChannelConnectionView
from app.portal.chatbot_business_profile_store import ChatBotBusinessProfileStore

ENGINE_ID = "channel_connection_facade_v1"


@dataclass(frozen=True)
class ChannelConnectionFacade:
    _service: ChannelConnectionService

    @classmethod
    def from_parts(
        cls,
        *,
        profiles: ChatBotBusinessProfileStore,
        channels: ChannelConnectionStore | None = None,
    ) -> ChannelConnectionFacade:
        return cls(
            _service=ChannelConnectionService(
                channels=channels
                if channels is not None
                else InMemoryChannelConnectionStore(),
                profiles=profiles,
            )
        )

    def list_channels(
        self, *, account_id: str, channel: str | None = None
    ) -> list[ChannelConnectionView]:
        try:
            return self._service.list_for_account(
                account_id=account_id, channel=channel
            )
        except ChannelConnectionError:
            raise

    def create_channel(
        self,
        *,
        account_id: str,
        channel: str,
        display_name: str | None = None,
        status: str = "not_configured",
        configuration: dict[str, Any] | None = None,
    ) -> ChannelConnectionView:
        try:
            return self._service.create(
                account_id=account_id,
                channel=channel,
                display_name=display_name,
                status=status,
                configuration=configuration,
            )
        except ChannelConnectionError:
            raise

    def update_channel(
        self,
        *,
        account_id: str,
        connection_id: str,
        display_name: str | None = None,
        status: str | None = None,
        configuration: dict[str, Any] | None = None,
    ) -> ChannelConnectionView:
        try:
            return self._service.update(
                account_id=account_id,
                connection_id=connection_id,
                display_name=display_name,
                status=status,
                configuration=configuration,
            )
        except ChannelConnectionError:
            raise

    def delete_channel(self, *, account_id: str, connection_id: str) -> None:
        try:
            self._service.delete(
                account_id=account_id, connection_id=connection_id
            )
        except ChannelConnectionError:
            raise
