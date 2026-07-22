"""Business Product BP1.3 — ChannelConnectionService (registry only).

Never sends/receives messages · never imports channel SDKs.
"""

from __future__ import annotations

from typing import Any

from app.portal.channel_connection import (
    CHANNEL_ORDER,
    ChannelConnectionError,
    apply_channel_update,
    new_channel_connection,
)
from app.portal.channel_connection_store import ChannelConnectionStore
from app.portal.channel_connection_view import (
    ChannelConnectionView,
    build_channel_view,
)
from app.portal.chatbot_business_profile_store import ChatBotBusinessProfileStore

ENGINE_ID = "channel_connection_service_v1"


class ChannelConnectionService:
    def __init__(
        self,
        *,
        channels: ChannelConnectionStore,
        profiles: ChatBotBusinessProfileStore,
    ) -> None:
        self._channels = channels
        self._profiles = profiles

    def _require_profile_id(self, account_id: str) -> str:
        profile = self._profiles.get_for_account(account_id)
        if profile is None:
            raise ChannelConnectionError("profile_required")
        return profile.profile_id

    def list_for_account(
        self, *, account_id: str, channel: str | None = None
    ) -> list[ChannelConnectionView]:
        profile_id = self._require_profile_id(account_id)
        rows = list(self._channels.list_for_profile(profile_id))
        if channel is not None:
            rows = [row for row in rows if row.channel == channel]
        order = {name: index for index, name in enumerate(CHANNEL_ORDER)}
        rows.sort(
            key=lambda item: (
                order.get(item.channel, 99),
                item.updated_at,
                item.display_name,
            )
        )
        return [build_channel_view(row) for row in rows]

    def create(
        self,
        *,
        account_id: str,
        channel: str,
        display_name: str | None = None,
        status: str = "not_configured",
        configuration: dict[str, Any] | None = None,
    ) -> ChannelConnectionView:
        profile_id = self._require_profile_id(account_id)
        existing = self._channels.list_for_profile(profile_id)
        if any(row.channel == channel for row in existing):
            raise ChannelConnectionError("channel_already_exists")
        row = new_channel_connection(
            profile_id=profile_id,
            channel=channel,
            display_name=display_name,
            status=status,
            configuration=configuration,
        )
        self._channels.save(row)
        return build_channel_view(row)

    def update(
        self,
        *,
        account_id: str,
        connection_id: str,
        display_name: str | None = None,
        status: str | None = None,
        configuration: dict[str, Any] | None = None,
    ) -> ChannelConnectionView:
        profile_id = self._require_profile_id(account_id)
        current = self._channels.get(connection_id)
        if current is None or current.profile_id != profile_id:
            raise ChannelConnectionError("connection_not_found")
        updated = apply_channel_update(
            current,
            display_name=display_name,
            status=status,
            configuration=configuration,
        )
        self._channels.save(updated)
        return build_channel_view(updated)

    def delete(self, *, account_id: str, connection_id: str) -> None:
        profile_id = self._require_profile_id(account_id)
        current = self._channels.get(connection_id)
        if current is None or current.profile_id != profile_id:
            raise ChannelConnectionError("connection_not_found")
        self._channels.delete(connection_id)
