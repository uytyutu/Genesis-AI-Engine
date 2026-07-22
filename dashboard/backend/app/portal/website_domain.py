"""R5.3 — WebsiteDomain Domain (site↔domain link, resource state).

Reference **resource management** Portal module. Answers: what domain
state is linked to this Website?

```text
WebsiteDomain
  primary_domain · custom_domain · domain_status · verification_status
```

Does not authenticate · authorize · know Session · Ownership · HTTP.
No DNS records · SSL · ACME · registrar · Cloudflare · auto-verify · purchase.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "website_domain_domain_v1"

_MAX_HOST = 253

DomainStatus = Literal["none", "pending", "active", "error"]
VerificationStatus = Literal["unverified", "pending", "verified", "failed"]

ALLOWED_DOMAIN_STATUS: frozenset[str] = frozenset(
    {"none", "pending", "active", "error"}
)
ALLOWED_VERIFICATION_STATUS: frozenset[str] = frozenset(
    {"unverified", "pending", "verified", "failed"}
)


class WebsiteDomainError(ValueError):
    """Invalid Website Domain state."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_hostname(value: str, *, field: str) -> str:
    host = value.strip().lower().rstrip(".")
    if len(host) > _MAX_HOST:
        raise WebsiteDomainError(f"{field}_too_long")
    if not host:
        return ""
    if "://" in host or "/" in host or " " in host:
        raise WebsiteDomainError(f"{field}_invalid")
    if "." not in host and host != "localhost":
        raise WebsiteDomainError(f"{field}_invalid")
    return host


@dataclass(frozen=True)
class WebsiteDomain:
    """Link between one Website and its domain state — not DNS infrastructure."""

    binding_id: str
    website_id: str
    primary_domain: str
    custom_domain: str
    domain_status: DomainStatus
    verification_status: VerificationStatus
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WebsiteDomainUpdate:
    """Intent to set Website domain resource state (full replace of listed fields)."""

    primary_domain: str
    custom_domain: str
    domain_status: str
    verification_status: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "primary_domain": self.primary_domain,
            "custom_domain": self.custom_domain,
            "domain_status": self.domain_status,
            "verification_status": self.verification_status,
        }


def empty_website_domain(website_id: str) -> WebsiteDomain:
    """Default: no domain attached."""
    now = _utc_now_iso()
    return WebsiteDomain(
        binding_id=str(uuid4()),
        website_id=website_id,
        primary_domain="",
        custom_domain="",
        domain_status="none",
        verification_status="unverified",
        created_at=now,
        updated_at=now,
    )


def apply_website_domain_update(
    current: WebsiteDomain,
    update: WebsiteDomainUpdate,
) -> WebsiteDomain:
    """Validate and apply domain state. Domain-only — no DNS side effects."""
    primary = _normalize_hostname(update.primary_domain, field="primary_domain")
    custom = _normalize_hostname(update.custom_domain, field="custom_domain")

    status = str(update.domain_status).strip().lower()
    verification = str(update.verification_status).strip().lower()
    if status not in ALLOWED_DOMAIN_STATUS:
        raise WebsiteDomainError("domain_status_invalid")
    if verification not in ALLOWED_VERIFICATION_STATUS:
        raise WebsiteDomainError("verification_status_invalid")

    return WebsiteDomain(
        binding_id=current.binding_id,
        website_id=current.website_id,
        primary_domain=primary,
        custom_domain=custom,
        domain_status=status,  # type: ignore[arg-type]
        verification_status=verification,  # type: ignore[arg-type]
        created_at=current.created_at,
        updated_at=_utc_now_iso(),
    )
