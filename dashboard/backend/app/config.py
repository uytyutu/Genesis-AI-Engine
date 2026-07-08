"""Runtime environment — development vs production (no behavior changes to Mind/Workforce)."""

from __future__ import annotations

import os


def genesis_env() -> str:
    explicit = os.getenv("GENESIS_ENV", "").strip().lower()
    if explicit in ("development", "dev", "local"):
        return "development"
    if explicit in ("production", "prod"):
        return "production"
    if os.getenv("RENDER") or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("VERCEL"):
        return "production"
    return "development"


def is_production() -> bool:
    return genesis_env() == "production"


def is_development() -> bool:
    return genesis_env() == "development"


def cloud_proof_mode() -> bool:
    """Runtime proof — cloud LLM only, no brief_speech / template overrides."""
    return os.getenv("GENESIS_CLOUD_PROOF", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def cloud_first_responses() -> bool:
    """When cloud answered, local template pools must not replace the draft."""
    if cloud_proof_mode():
        return True
    if os.getenv("GENESIS_ALLOW_LOCAL_TEMPLATES", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return False
    return True
