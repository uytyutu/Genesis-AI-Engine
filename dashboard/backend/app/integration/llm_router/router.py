"""LLM Router — Rule #0: capability-first, vendor-agnostic."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.genesis_brain.providers import build_provider_registry
from app.integration.llm_router.circuit_breaker import CircuitBreaker
from app.integration.llm_router.planner import RoutePlan, RoutePlanner
from app.integration.llm_router.capabilities import task_to_capability
from app.integration.llm_router.policies import CLOUD_EMPLOYEES, normalize_task
from app.integration.llm_router.proof import proof_provider_pin
from app.integration.provider_health_service import probe_providers


class LLMRouter:
    """
    Rule #0 — Virtus Core never targets a specific model vendor.

    Stable pipeline:
      Vector → Identity → Memory → Planner → LLM Router → Capability → Provider

    Providers swap (Groq today, GPT-6 tomorrow). Capabilities and Router stay.

    Reproducible proof (dev): GENESIS_LLM_PROOF_PROVIDER=gemini — no code change.
    """

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory_dir = memory_dir or Path(__file__).resolve().parents[3] / "memory"
        self._planner = RoutePlanner(self._memory_dir)
        self._breaker = CircuitBreaker(self._memory_dir)

    def plan_route(
        self,
        task: str | None,
        *,
        packages: list[dict[str, Any]] | None = None,
        premium_allowed: bool = True,
        force_health_probe: bool = False,
    ) -> RoutePlan:
        registry = build_provider_registry(packages)
        rows = probe_providers(memory_dir=self._memory_dir, force=force_health_probe)
        responding = {
            r["employee_id"]
            for r in rows
            if r.get("responds") and r["employee_id"] in CLOUD_EMPLOYEES
        }
        return self._planner.plan(
            task,
            registry=registry,
            premium_allowed=premium_allowed,
            health_responding=responding,
        )

    def sort_providers(
        self,
        providers: list[Any],
        plan: RoutePlan,
    ) -> list[Any]:
        """Reorder provider instances to match router failover order."""
        by_id = {getattr(p, "provider_id", ""): p for p in providers}
        ordered: list[Any] = []
        for eid in plan.failover_order:
            p = by_id.get(eid)
            if p is not None:
                ordered.append(p)
        if self._planner.emergency_allowed(plan):
            local = by_id.get("genesis-local")
            if local is not None:
                ordered.append(local)
        for p in providers:
            if p not in ordered:
                ordered.append(p)
        return ordered

    def on_provider_success(self, provider_id: str) -> None:
        if provider_id in CLOUD_EMPLOYEES:
            self._breaker.record_success(provider_id)

    def on_provider_failure(self, provider_id: str, *, error: str = "") -> None:
        if provider_id in CLOUD_EMPLOYEES:
            self._breaker.record_failure(provider_id, error=error)

    def emergency_fallback_allowed(self, plan: RoutePlan) -> bool:
        return self._planner.emergency_allowed(plan)

    def capability_for_task(self, task: str | None) -> str:
        return task_to_capability(task)

    def proof_pin(self) -> str | None:
        return proof_provider_pin()

    def normalize_task(self, task: str | None) -> str:
        return normalize_task(task)

    def circuit_snapshot(self) -> dict[str, Any]:
        return self._breaker.snapshot()
