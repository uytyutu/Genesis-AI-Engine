"""R5.1 — WebsiteSettings Domain (Basic Profile).

Reference Portal module domain. Answers: what is the editable profile
of this Website?

```text
WebsiteSettings
  website_name · company_name · contact_email · phone · social_links
```

Does not authenticate · authorize · know Session · Ownership · HTTP.
No SEO · Theme · Branding · Logo · Favicon · Colors.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

ENGINE_ID = "website_settings_domain_v1"

_MAX_NAME = 200
_MAX_EMAIL = 320
_MAX_PHONE = 64
_MAX_SOCIAL_KEY = 64
_MAX_SOCIAL_URL = 400
_MAX_SOCIAL_ENTRIES = 20

ALLOWED_SOCIAL_NETWORKS: frozenset[str] = frozenset(
    {
        "instagram",
        "facebook",
        "linkedin",
        "x",
        "twitter",
        "youtube",
        "tiktok",
        "website",
    }
)


class WebsiteSettingsError(ValueError):
    """Invalid Basic Profile field."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_social_links(
    raw: Mapping[str, str] | None,
) -> tuple[tuple[str, str], ...]:
    if raw is None:
        return ()
    if len(raw) > _MAX_SOCIAL_ENTRIES:
        raise WebsiteSettingsError("social_links_too_many")
    out: list[tuple[str, str]] = []
    for key, value in raw.items():
        network = str(key).strip().lower()
        url = str(value).strip()
        if not network:
            raise WebsiteSettingsError("social_network_empty")
        if len(network) > _MAX_SOCIAL_KEY:
            raise WebsiteSettingsError("social_network_too_long")
        if network not in ALLOWED_SOCIAL_NETWORKS:
            raise WebsiteSettingsError("social_network_not_allowed")
        if len(url) > _MAX_SOCIAL_URL:
            raise WebsiteSettingsError("social_url_too_long")
        if not url:
            continue
        out.append((network, url))
    out.sort(key=lambda pair: pair[0])
    return tuple(out)


@dataclass(frozen=True)
class WebsiteSettings:
    """Editable Basic Profile for one Website — not Auth, not Ownership."""

    settings_id: str
    website_id: str
    website_name: str
    company_name: str
    contact_email: str
    phone: str
    social_links: tuple[tuple[str, str], ...]
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["social_links"] = dict(self.social_links)
        return data

    def social_links_mapping(self) -> dict[str, str]:
        return dict(self.social_links)


@dataclass(frozen=True)
class WebsiteSettingsUpdate:
    """Intent to replace Basic Profile fields (full replace of listed fields)."""

    website_name: str
    company_name: str
    contact_email: str
    phone: str
    social_links: Mapping[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "website_name": self.website_name,
            "company_name": self.company_name,
            "contact_email": self.contact_email,
            "phone": self.phone,
            "social_links": dict(self.social_links),
        }


def empty_website_settings(website_id: str) -> WebsiteSettings:
    """Default profile when nothing has been saved yet."""
    now = _utc_now_iso()
    return WebsiteSettings(
        settings_id=str(uuid4()),
        website_id=website_id,
        website_name="",
        company_name="",
        contact_email="",
        phone="",
        social_links=(),
        created_at=now,
        updated_at=now,
    )


def apply_website_settings_update(
    current: WebsiteSettings,
    update: WebsiteSettingsUpdate,
) -> WebsiteSettings:
    """Validate and apply Basic Profile update. Domain-only."""
    website_name = update.website_name.strip()
    company_name = update.company_name.strip()
    contact_email = update.contact_email.strip()
    phone = update.phone.strip()

    if len(website_name) > _MAX_NAME:
        raise WebsiteSettingsError("website_name_too_long")
    if len(company_name) > _MAX_NAME:
        raise WebsiteSettingsError("company_name_too_long")
    if len(contact_email) > _MAX_EMAIL:
        raise WebsiteSettingsError("contact_email_too_long")
    if contact_email and "@" not in contact_email:
        raise WebsiteSettingsError("contact_email_invalid")
    if len(phone) > _MAX_PHONE:
        raise WebsiteSettingsError("phone_too_long")

    social = _normalize_social_links(update.social_links)
    return WebsiteSettings(
        settings_id=current.settings_id,
        website_id=current.website_id,
        website_name=website_name,
        company_name=company_name,
        contact_email=contact_email,
        phone=phone,
        social_links=social,
        created_at=current.created_at,
        updated_at=_utc_now_iso(),
    )
