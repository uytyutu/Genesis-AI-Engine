"""Non-live connectors — registered so Farm Engine is multi-platform ready."""

from __future__ import annotations

from typing import Any

from .base import ConnectorStatus, Tier


class StubConnector:
    """Placeholder: enabled in catalog, never fetches until status → live."""

    def __init__(
        self,
        *,
        id: str,
        display_name: str,
        tier: Tier,
        status: ConnectorStatus,
        official_docs_url: str,
        notes_ru: str = "",
    ) -> None:
        self.id = id
        self.display_name = display_name
        self.tier = tier
        self.status = status
        self.official_docs_url = official_docs_url
        self.notes_ru = notes_ru

    def fetch_raw(self) -> list[dict[str, Any]]:
        return []

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        return None
