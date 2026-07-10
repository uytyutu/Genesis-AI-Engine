"""Delivery Engine feature gate — disabled by default until lifecycle UI ships."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def delivery_engine_enabled(memory_dir: Path | None = None) -> bool:
    from app.integration.feature_registry import FeatureRegistry

    return FeatureRegistry(memory_dir=memory_dir).is_enabled("delivery_engine")


def delivery_rules_for_truth() -> str:
    if not delivery_engine_enabled():
        return ""
    from app.integration.delivery_engine.vector_rules import delivery_engine_rules_for_vector

    block = delivery_engine_rules_for_vector().strip()
    return f"\n{block}" if block else ""


def finalize_execution_response(
    memory_dir: Path,
    *,
    visitor_id: str,
    workspace_id: str,
    capability_id: str,
    outputs: dict[str, Any],
    goal: str,
    preview_href: str | None = None,
    primary_href: str | None = None,
    primary_label: str | None = None,
    extra_ctas: list[dict[str, Any]] | None = None,
    answer_override: str | None = None,
) -> dict[str, Any]:
    """Route execution completion through Delivery Engine when enabled."""
    if delivery_engine_enabled(memory_dir):
        from app.integration.delivery_engine import DeliveryEngine

        return DeliveryEngine(memory_dir).on_execution_complete(
            visitor_id=visitor_id,
            workspace_id=workspace_id,
            capability_id=capability_id,
            outputs=outputs,
            goal=goal,
            preview_href=preview_href,
            primary_href=primary_href,
            primary_label=primary_label,
            extra_ctas=extra_ctas,
            answer_override=answer_override,
        )

    href = preview_href or primary_href
    label = primary_label
    return {
        "answer": answer_override or "",
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": href,
        "cta_label": label,
        "cta_actions": extra_ctas,
    }
