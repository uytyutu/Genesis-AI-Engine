"""Genesis AI Hub — provider registry (capabilities, not consumer brands)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Capability = Literal[
    "chat", "code", "vision", "document", "image", "audio", "embed", "tool"
]
ProviderKind = Literal["llm", "tool", "local", "development"]
ProviderStatus = Literal["available", "degraded", "offline", "disabled"]
MinTier = Literal["free", "pro", "business", "ceo"]


@dataclass(frozen=True)
class ProviderDefinition:
    id: str
    kind: ProviderKind
    capabilities: tuple[Capability, ...]
    label: str
    status: ProviderStatus
    min_tier: MinTier


# Internal registry — UI shows capabilities, not vendor marketing names.
PROVIDER_REGISTRY: dict[str, ProviderDefinition] = {
    "genesis-rules": ProviderDefinition(
        id="genesis-rules",
        kind="local",
        capabilities=("chat",),
        label="Virtus Local Intelligence",
        status="available",
        min_tier="free",
    ),
    "genesis-planner": ProviderDefinition(
        id="genesis-planner",
        kind="local",
        capabilities=("chat", "tool"),
        label="Virtus Planner",
        status="available",
        min_tier="ceo",
    ),
    "cursor-tool": ProviderDefinition(
        id="cursor-tool",
        kind="development",
        capabilities=("code", "tool"),
        label="Development Provider · Cursor",
        status="available",
        min_tier="ceo",
    ),
    "dev-provider-placeholder": ProviderDefinition(
        id="dev-provider-placeholder",
        kind="development",
        capabilities=("code",),
        label="Development Provider · alternate (future)",
        status="disabled",
        min_tier="ceo",
    ),
}


def providers_for_capability(capability: Capability, tier: MinTier = "ceo") -> list[ProviderDefinition]:
    tier_order = ("free", "pro", "business", "ceo")
    min_idx = tier_order.index(tier)
    out: list[ProviderDefinition] = []
    for p in PROVIDER_REGISTRY.values():
        if capability not in p.capabilities:
            continue
        if tier_order.index(p.min_tier) > min_idx:
            continue
        if p.status == "disabled":
            continue
        out.append(p)
    return out


def default_development_provider() -> ProviderDefinition | None:
    for pid in ("cursor-tool", "dev-provider-placeholder"):
        p = PROVIDER_REGISTRY.get(pid)
        if p and p.status == "available":
            return p
    return None


def list_providers(*, tier: MinTier = "ceo") -> list[dict]:
    tier_order = ("free", "pro", "business", "ceo")
    min_idx = tier_order.index(tier)
    rows: list[dict] = []
    for p in PROVIDER_REGISTRY.values():
        if tier_order.index(p.min_tier) > min_idx:
            continue
        rows.append(
            {
                "id": p.id,
                "kind": p.kind,
                "capabilities": list(p.capabilities),
                "label": p.label,
                "status": p.status,
                "min_tier": p.min_tier,
            }
        )
    return rows
