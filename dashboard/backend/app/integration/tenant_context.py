"""Foundation F2 — tenant skeleton (Platform → Workspace → Project).

Mission 1: single platform tenant; public visitors are anonymous on tier free.
No customer provisioning yet — types and resolution only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.integration.attachment_policy import AttachmentTier, resolve_attachment_tier

PlatformLayer = Literal["platform", "workspace", "project"]
TenantKind = Literal["owner", "visitor", "customer"]

OWNER_TENANT_ID = "_platform"


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    kind: TenantKind
    layer: PlatformLayer
    visitor_id: str | None = None
    subscription_tier: AttachmentTier = "free"

    def to_dict(self) -> dict[str, str]:
        return {
            "tenant_id": self.tenant_id,
            "kind": self.kind,
            "layer": self.layer,
            "visitor_id": self.visitor_id or "",
            "subscription_tier": self.subscription_tier,
        }


def resolve_tenant_context(
    *,
    visitor_id: str | None = None,
    layer: PlatformLayer = "platform",
    subscription_tier: AttachmentTier | None = None,
) -> TenantContext:
    """Resolve tenant for the current request. Mission 1 → owner platform tenant."""
    vid = (visitor_id or "").strip()[:64] or None
    tier = resolve_attachment_tier(
        visitor_id=vid,
        subscription_tier=subscription_tier,
    )
    if vid and vid != "anonymous":
        return TenantContext(
            tenant_id=OWNER_TENANT_ID,
            kind="visitor",
            layer=layer,
            visitor_id=vid,
            subscription_tier=tier,
        )
    return TenantContext(
        tenant_id=OWNER_TENANT_ID,
        kind="owner",
        layer=layer,
        visitor_id=vid,
        subscription_tier=tier,
    )
