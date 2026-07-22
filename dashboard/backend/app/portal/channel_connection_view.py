"""Business Product BP1.3 — Channel Connection View."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.channel_connection import ChannelConnection

ENGINE_ID = "channel_connection_view_v1"


@dataclass(frozen=True)
class ChannelConnectionView:
    connection_id: str
    profile_id: str
    channel: str
    display_name: str
    status: str
    configuration: dict[str, str]
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "profile_id": self.profile_id,
            "channel": self.channel,
            "display_name": self.display_name,
            "status": self.status,
            "configuration": dict(self.configuration),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def build_channel_view(row: ChannelConnection) -> ChannelConnectionView:
    return ChannelConnectionView(
        connection_id=row.connection_id,
        profile_id=row.profile_id,
        channel=row.channel,
        display_name=row.display_name,
        status=row.status,
        configuration=dict(row.configuration),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
