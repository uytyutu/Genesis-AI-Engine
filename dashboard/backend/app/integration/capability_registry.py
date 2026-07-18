"""Foundation F1 — unified read-only capability registry.

Aggregates existing registries without replacing them:
- ai_hub.provider_registry (owner AI Hub)
- public_truth_catalog / pricing_display (Mission 1 commerce)
- opportunity_service sources
- factory product intents (mirror of create/page.tsx TYPES)
- environment gates (outreach, acceptance, dev mode)

Does not change runtime behaviour — snapshot only.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app.integration.ai_hub.provider_registry import PROVIDER_REGISTRY, MinTier

CapabilityDomain = Literal[
    "ai_hub_provider",
    "brain_employee",
    "public_product",
    "subscription",
    "opportunity_source",
    "factory_product",
    "env_gate",
]

# Canonical factory intents — keep in sync with dashboard/frontend/app/create/page.tsx TYPES.
_FACTORY_PRODUCT_TYPES: tuple[dict[str, Any], ...] = (
    {"id": "landing-page", "label": "Landing Page", "ready": True, "enabled": True},
    {"id": "telegram-bot", "label": "Telegram Bot", "ready": False, "enabled": False},
    {"id": "shop", "label": "Интернет-магазин", "ready": False, "enabled": False},
    {"id": "crm", "label": "CRM", "ready": False, "enabled": False},
)

_ENV_GATES: tuple[dict[str, str], ...] = (
    {
        "id": "outreach_send",
        "env": "GENESIS_OUTREACH_ENABLED",
        "label": "Acquisition outreach send",
        "source": "acquisition_studio_service",
    },
    {
        "id": "acceptance_gate",
        "env": "GENESIS_ACCEPTANCE_GATE",
        "label": "LocalMind-only acceptance tests",
        "source": "genesis_brain.providers",
    },
    {
        "id": "dev_mode",
        "env": "GENESIS_DEV_MODE",
        "label": "Debug / Thinking Brief on non-localhost",
        "source": "security.dev_mode_allowed",
    },
    {
        "id": "hive_api",
        "env": "HIVE_API_KEY",
        "label": "Hive AI media provider (not Path A)",
        "source": "providers.hive",
    },
)

REGISTRY_VERSION = "foundation-f1-1"


@dataclass(frozen=True)
class CapabilityEntry:
    id: str
    domain: CapabilityDomain
    label: str
    exists: bool
    stable: bool
    ready: bool
    enabled: bool
    tier: str | None
    source: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _env_enabled(env_name: str) -> bool:
    return os.getenv(env_name, "").strip().lower() in ("1", "true", "yes", "on")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CapabilityRegistry:
    """Read-only merge of all capability sources in the platform."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory_dir = memory_dir

    def list_capabilities(self) -> list[CapabilityEntry]:
        rows: list[CapabilityEntry] = []
        rows.extend(self._ai_hub_providers())
        rows.extend(self._public_commerce())
        rows.extend(self._opportunity_sources())
        rows.extend(self._factory_products())
        rows.extend(self._env_gates())
        return rows

    def snapshot(self) -> dict[str, Any]:
        caps = self.list_capabilities()
        enabled = [c for c in caps if c.enabled]
        truth_version = "mission1-truth-1"
        for c in caps:
            if c.domain == "public_product" and c.source == "pricing_display.json":
                truth_version = c.notes.split("version=", 1)[-1] if "version=" in c.notes else truth_version
                break
        return {
            "version": REGISTRY_VERSION,
            "generated_at": _utc_now(),
            "truth_catalog_version": truth_version,
            "summary": {
                "total": len(caps),
                "enabled": len(enabled),
                "domains": sorted({c.domain for c in caps}),
            },
            "capabilities": [c.to_dict() for c in caps],
        }

    def get(self, capability_id: str, *, domain: CapabilityDomain | None = None) -> CapabilityEntry | None:
        for row in self.list_capabilities():
            if row.id == capability_id and (domain is None or row.domain == domain):
                return row
        return None

    def _ai_hub_providers(self) -> list[CapabilityEntry]:
        out: list[CapabilityEntry] = []
        for p in PROVIDER_REGISTRY.values():
            enabled = p.status == "available"
            out.append(
                CapabilityEntry(
                    id=p.id,
                    domain="ai_hub_provider",
                    label=p.label,
                    exists=True,
                    stable=p.status in ("available", "disabled"),
                    ready=p.status != "offline",
                    enabled=enabled,
                    tier=p.min_tier,
                    source="ai_hub.provider_registry",
                    notes=f"capabilities={','.join(p.capabilities)}; kind={p.kind}; status={p.status}",
                )
            )
        return out

    def _public_commerce(self) -> list[CapabilityEntry]:
        import json

        display: dict[str, Any] | None = None
        source = "mission1-defaults"
        if self._memory_dir:
            cfg = self._memory_dir / "pricing_display.json"
            if cfg.is_file():
                try:
                    display = json.loads(cfg.read_text(encoding="utf-8"))
                    source = "pricing_display.json"
                except (json.JSONDecodeError, OSError):
                    display = None

        out: list[CapabilityEntry] = []

        if display:
            version_note = f"version={display.get('version', 'unknown')}"
            for cat in display.get("service_categories") or []:
                for item in cat.get("items") or []:
                    iid = str(item.get("id") or "")
                    if not iid:
                        continue
                    available = bool(item.get("available"))
                    out.append(
                        CapabilityEntry(
                            id=f"product:{iid}",
                            domain="public_product",
                            label=str(item.get("name") or iid),
                            exists=True,
                            stable=True,
                            ready=available,
                            enabled=available,
                            tier="free",
                            source=source,
                            notes=f"{version_note}; cta={item.get('cta_href')}",
                        )
                    )
            for sub in display.get("subscriptions") or []:
                sid = str(sub.get("id") or "")
                if not sid:
                    continue
                available = bool(sub.get("available"))
                out.append(
                    CapabilityEntry(
                        id=f"subscription:{sid}",
                        domain="subscription",
                        label=str(sub.get("name") or sid),
                        exists=True,
                        stable=sid == "free",
                        ready=available,
                        enabled=available,
                        tier=sid,
                        source=source,
                        notes=version_note,
                    )
                )
            return out

        # Mission 1 defaults — aligned with public_truth_catalog / sales packages.
        out.append(
            CapabilityEntry(
                id="product:landing",
                domain="public_product",
                label="Landing Page",
                exists=True,
                stable=True,
                ready=True,
                enabled=True,
                tier="free",
                source=source,
                notes="packages=basic,business,premium; prices=350,650,1200; cta=/order",
            )
        )
        out.append(
            CapabilityEntry(
                id="subscription:free",
                domain="subscription",
                label="Free",
                exists=True,
                stable=True,
                ready=True,
                enabled=True,
                tier="free",
                source=source,
                notes="Mission 1 public chat tier",
            )
        )
        return out

    def _opportunity_sources(self) -> list[CapabilityEntry]:
        from app.integration.opportunity_service import OpportunityService

        svc = OpportunityService(memory_dir=self._memory_dir)
        out: list[CapabilityEntry] = []
        for src in svc.list_sources():
            sid = str(src.get("id") or "")
            enabled = bool(src.get("enabled"))
            out.append(
                CapabilityEntry(
                    id=f"opportunity:{sid}",
                    domain="opportunity_source",
                    label=str(src.get("label") or sid),
                    exists=True,
                    stable=sid in ("manual", "google_maps"),
                    ready=enabled,
                    enabled=enabled,
                    tier="ceo",
                    source="opportunity_service._SOURCE_REGISTRY",
                    notes=f"adapter={src.get('adapter')}; auto_search={src.get('auto_search')}",
                )
            )
        return out

    def _factory_products(self) -> list[CapabilityEntry]:
        out: list[CapabilityEntry] = []
        for row in _FACTORY_PRODUCT_TYPES:
            pid = str(row["id"])
            enabled = bool(row.get("enabled"))
            ready = bool(row.get("ready"))
            out.append(
                CapabilityEntry(
                    id=f"factory:{pid}",
                    domain="factory_product",
                    label=str(row.get("label") or pid),
                    exists=pid == "landing-page",
                    stable=pid == "landing-page",
                    ready=ready,
                    enabled=enabled,
                    tier="ceo" if pid == "landing-page" else "business",
                    source="create/page.tsx (canonical mirror)",
                    notes="Mission 1: only landing-page enabled",
                )
            )
        return out

    def _env_gates(self) -> list[CapabilityEntry]:
        out: list[CapabilityEntry] = []
        for gate in _ENV_GATES:
            env_name = gate["env"]
            enabled = _env_enabled(env_name)
            out.append(
                CapabilityEntry(
                    id=f"env:{gate['id']}",
                    domain="env_gate",
                    label=gate["label"],
                    exists=True,
                    stable=True,
                    ready=True,
                    enabled=enabled,
                    tier="ceo",
                    source=gate["source"],
                    notes=f"env={env_name}",
                )
            )
        return out


def providers_for_tier(tier: MinTier = "ceo") -> list[dict[str, Any]]:
    """Thin delegate — keeps ai_hub.provider_registry as source of truth."""
    from app.integration.ai_hub.provider_registry import list_providers

    return list_providers(tier=tier)
