"""Business Product BP1.3 — ChannelConnectionStore."""

from __future__ import annotations

from typing import Protocol

from app.portal.channel_connection import ChannelConnection

ENGINE_ID = "channel_connection_store_v1"


class ChannelConnectionStore(Protocol):
    def save(self, row: ChannelConnection) -> None: ...

    def get(self, connection_id: str) -> ChannelConnection | None: ...

    def list_for_profile(
        self, profile_id: str
    ) -> tuple[ChannelConnection, ...]: ...

    def delete(self, connection_id: str) -> bool: ...


class InMemoryChannelConnectionStore:
    def __init__(self) -> None:
        self._rows: dict[str, ChannelConnection] = {}

    def save(self, row: ChannelConnection) -> None:
        self._rows[row.connection_id] = row

    def get(self, connection_id: str) -> ChannelConnection | None:
        return self._rows.get(connection_id)

    def list_for_profile(
        self, profile_id: str
    ) -> tuple[ChannelConnection, ...]:
        return tuple(
            row for row in self._rows.values() if row.profile_id == profile_id
        )

    def delete(self, connection_id: str) -> bool:
        if connection_id not in self._rows:
            return False
        del self._rows[connection_id]
        return True
