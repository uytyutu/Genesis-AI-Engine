"""Runtime environment — development vs production vs test."""

from __future__ import annotations

import os
from typing import Final

# Mock stubs used only when APP_ENV/ENVIRONMENT=test (never real secrets).
TEST_MOCK_KEYS: Final[dict[str, str]] = {
    "GENESIS_GROQ_API_KEY": "",
    "GROQ_API_KEY": "",
    "OPENAI_API_KEY": "",
    "GENESIS_LLM_API_KEY": "",
    "GENESIS_GEMINI_API_KEY": "",
    "GOOGLE_API_KEY": "",
    "GOOGLE_PLACES_API_KEY": "",
}

SECRET_ENV_VARS: Final[tuple[str, ...]] = tuple(TEST_MOCK_KEYS.keys())


def app_env() -> str:
    """Active profile: test | development | production."""
    for var in ("APP_ENV", "ENVIRONMENT", "GENESIS_ENV"):
        raw = os.getenv(var, "").strip().lower()
        if raw in ("test", "testing"):
            return "test"
        if raw in ("development", "dev", "local"):
            return "development"
        if raw in ("production", "prod"):
            return "production"
    if os.getenv("PYTEST_CURRENT_TEST"):
        return "test"
    if os.getenv("RENDER") or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("VERCEL"):
        return "production"
    return "development"


def is_test_env() -> bool:
    return app_env() == "test"


def env_config_file() -> str:
    """Which env file load_local_env prefers for the active profile."""
    if is_test_env():
        return "dashboard/backend/.env.test"
    return "dashboard/backend/.env.local"


def get_api_key(name: str, default: str = "") -> str:
    """Resolve a secret — test profile never falls back to .env.local."""
    if is_test_env():
        return os.getenv(name, TEST_MOCK_KEYS.get(name, default)).strip()
    return os.getenv(name, default).strip()


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
