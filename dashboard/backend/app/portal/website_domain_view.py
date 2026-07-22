"""R5.3 — WebsiteDomain View (HTTP/API shape).

Presentation only. No Auth · no domain rules · no persistence.
Contract is intended to stay stable when Store gains real DNS/SSL backends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.website_domain import WebsiteDomain

ENGINE_ID = "website_domain_view_v1"


@dataclass(frozen=True)
class WebsiteDomainView:
    website_id: str
    primary_domain: str
    custom_domain: str
    domain_status: str
    verification_status: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "website_id": self.website_id,
            "primary_domain": self.primary_domain,
            "custom_domain": self.custom_domain,
            "domain_status": self.domain_status,
            "verification_status": self.verification_status,
            "updated_at": self.updated_at,
        }


def build_website_domain_view(binding: WebsiteDomain) -> WebsiteDomainView:
    return WebsiteDomainView(
        website_id=binding.website_id,
        primary_domain=binding.primary_domain,
        custom_domain=binding.custom_domain,
        domain_status=binding.domain_status,
        verification_status=binding.verification_status,
        updated_at=binding.updated_at,
    )
