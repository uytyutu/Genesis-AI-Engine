"""R5.1 — WebsiteSettingsStore (temporary in-memory adapter).

``WebsiteSettingsStore`` is the abstraction; ``InMemoryWebsiteSettingsStore``
is today's adapter. Future DB store plugs in without changing the Facade.
"""

from __future__ import annotations

from typing import Protocol

from app.portal.website_settings import WebsiteSettings

ENGINE_ID = "website_settings_store_v1"


class WebsiteSettingsStore(Protocol):
    def get(self, website_id: str) -> WebsiteSettings | None: ...

    def save(self, settings: WebsiteSettings) -> None: ...


class InMemoryWebsiteSettingsStore:
    """Process-local settings map — replace with durable store later."""

    def __init__(self) -> None:
        self._rows: dict[str, WebsiteSettings] = {}

    def get(self, website_id: str) -> WebsiteSettings | None:
        return self._rows.get(website_id)

    def save(self, settings: WebsiteSettings) -> None:
        self._rows[settings.website_id] = settings
