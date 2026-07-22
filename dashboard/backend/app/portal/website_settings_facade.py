"""R5.1 — WebsiteSettingsFacade (reference ModuleFacade).

```text
Authorization (caller)
    ↓
WebsiteSettingsFacade
    ↓
WebsiteSettings Domain + Store
```

Sole application entry for Basic Profile get/update.
Does not authenticate · authorize · know cookies · Session · Ownership.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.portal.website_settings import (
    WebsiteSettingsError,
    WebsiteSettingsUpdate,
    apply_website_settings_update,
    empty_website_settings,
)
from app.portal.website_settings_store import WebsiteSettingsStore
from app.portal.website_settings_view import (
    WebsiteSettingsView,
    build_website_settings_view,
)

ENGINE_ID = "website_settings_facade_v1"


@dataclass(frozen=True)
class WebsiteSettingsFacade:
    """Reference ModuleFacade — copy this shape for Analytics / CRM / …"""

    _store: WebsiteSettingsStore

    @classmethod
    def from_store(cls, store: WebsiteSettingsStore) -> WebsiteSettingsFacade:
        return cls(_store=store)

    def get_settings(self, website_id: str) -> WebsiteSettingsView:
        row = self._store.get(website_id)
        if row is None:
            row = empty_website_settings(website_id)
        return build_website_settings_view(row)

    def update_settings(
        self,
        website_id: str,
        *,
        website_name: str,
        company_name: str,
        contact_email: str,
        phone: str,
        social_links: Mapping[str, str],
    ) -> WebsiteSettingsView:
        current = self._store.get(website_id)
        if current is None:
            current = empty_website_settings(website_id)
        update = WebsiteSettingsUpdate(
            website_name=website_name,
            company_name=company_name,
            contact_email=contact_email,
            phone=phone,
            social_links=social_links,
        )
        try:
            next_row = apply_website_settings_update(current, update)
        except WebsiteSettingsError:
            raise
        self._store.save(next_row)
        return build_website_settings_view(next_row)
