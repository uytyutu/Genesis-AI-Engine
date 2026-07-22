"""R5.1 — WebsiteSettings View (HTTP/API shape).

Presentation only. No Auth · no domain rules · no persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.website_settings import WebsiteSettings

ENGINE_ID = "website_settings_view_v1"


@dataclass(frozen=True)
class WebsiteSettingsView:
    website_id: str
    website_name: str
    company_name: str
    contact_email: str
    phone: str
    social_links: dict[str, str]
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "website_id": self.website_id,
            "website_name": self.website_name,
            "company_name": self.company_name,
            "contact_email": self.contact_email,
            "phone": self.phone,
            "social_links": dict(self.social_links),
            "updated_at": self.updated_at,
        }


def build_website_settings_view(settings: WebsiteSettings) -> WebsiteSettingsView:
    return WebsiteSettingsView(
        website_id=settings.website_id,
        website_name=settings.website_name,
        company_name=settings.company_name,
        contact_email=settings.contact_email,
        phone=settings.phone,
        social_links=settings.social_links_mapping(),
        updated_at=settings.updated_at,
    )
