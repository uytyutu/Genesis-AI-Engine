"""Unified LLM Router — Rule #0: design the Router, never a specific model."""

from app.integration.llm_router.audit import audit_infrastructure, infrastructure_report_table
from app.integration.llm_router.capabilities import (
    CAPABILITY_PRIORITY,
    LLMCapability,
    capability_chain,
    task_to_capability,
)
from app.integration.llm_router.proof import proof_provider_label, proof_provider_pin
from app.integration.llm_router.router import LLMRouter

__all__ = [
    "LLMRouter",
    "LLMCapability",
    "CAPABILITY_PRIORITY",
    "audit_infrastructure",
    "infrastructure_report_table",
    "capability_chain",
    "task_to_capability",
    "proof_provider_pin",
    "proof_provider_label",
]
