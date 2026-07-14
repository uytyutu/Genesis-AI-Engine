"""Route planner — capability-first; one primary provider + failover."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.integration.genesis_brain.provider_diagnostics import _has_key
from app.integration.genesis_brain.workforce_quotas import WorkforceQuotas
from app.integration.llm_router.circuit_breaker import CircuitBreaker
from app.integration.llm_router.policies import CLOUD_EMPLOYEES, EMERGENCY_ONLY, capability_chain
from app.integration.llm_router.capabilities import task_to_capability
from app.integration.llm_router.proof import proof_provider_label, proof_provider_pin


@dataclass(frozen=True)
class RoutePlan:
    task: str
    capability: str
    primary: str | None
    failover_order: tuple[str, ...]
    reason: str
    any_cloud_configured: bool
    any_cloud_eligible: bool
    proof_pin: str | None = None


class RoutePlanner:
    """Capability → provider — vendor-agnostic selection."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory_dir = memory_dir
        self._quotas = WorkforceQuotas(memory_dir)
        self._breaker = CircuitBreaker(memory_dir)

    def plan(
        self,
        task: str | None,
        *,
        registry: dict[str, Any],
        premium_allowed: bool = True,
        health_responding: set[str] | None = None,
    ) -> RoutePlan:
        capability = task_to_capability(task)
        chain = capability_chain(capability, premium_allowed=premium_allowed)
        health = health_responding or set()
        pin = proof_provider_pin()

        configured: list[str] = []
        eligible: list[str] = []
        for eid in chain:
            if eid not in CLOUD_EMPLOYEES:
                continue
            if not _has_key(eid):
                continue
            configured.append(eid)
            provider = registry.get(eid)
            if provider is None:
                continue
            if self._breaker.is_open(eid):
                continue
            if not self._quotas.has_budget(eid):
                continue
            try:
                if not provider.available():
                    continue
            except Exception:
                continue
            eligible.append(eid)

        proven = [e for e in eligible if e in health]
        unproven = [e for e in eligible if e not in health]
        ordered = list(proven + unproven)

        # Reproducible Architecture Proof — pin without code change (dev env only).
        if pin and pin in CLOUD_EMPLOYEES and pin in configured:
            rest = [e for e in ordered if e != pin]
            if pin in eligible:
                ordered = [pin] + rest
            else:
                ordered = [pin] + [e for e in chain if e != pin and e in configured]

        ordered_tuple = tuple(ordered)
        primary = ordered_tuple[0] if ordered_tuple else None

        if pin:
            reason = (
                f"Router: capability={capability}; proof_pin={pin}; "
                f"primary={primary}; failover={max(0, len(ordered_tuple) - 1)}"
            )
        elif primary:
            reason = (
                f"Router: capability={capability}; primary={primary}; "
                f"failover={len(ordered_tuple) - 1}"
            )
        elif configured:
            reason = (
                f"Router: capability={capability}; {len(configured)} configured "
                f"but 0 eligible (circuit/quota/offline)"
            )
        else:
            reason = f"Router: capability={capability}; no cloud keys configured"

        return RoutePlan(
            task=(task or "conversation").strip().lower(),
            capability=capability,
            primary=primary,
            failover_order=ordered_tuple,
            reason=reason,
            any_cloud_configured=bool(configured),
            any_cloud_eligible=bool(eligible),
            proof_pin=proof_provider_label(),
        )

    def emergency_allowed(self, plan: RoutePlan) -> bool:
        return not plan.any_cloud_eligible

    @property
    def emergency_provider(self) -> str:
        return EMERGENCY_ONLY
