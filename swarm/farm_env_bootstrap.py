"""Load Farm Engine secrets from dashboard/backend/.env.local into process env.

Does not print values. Safe no-op if file missing.
"""

from __future__ import annotations

import os
from pathlib import Path

_LOADED = False

_KEYS_OF_INTEREST = (
    "GROQ_API_KEY",
    "GENESIS_GROQ_API_KEY",
    "GENESIS_GROQ_BASE_URL",
    "GENESIS_GROQ_MODEL",
    "OPENAI_API_KEY",
    "GENESIS_LLM_API_KEY",
    "GENESIS_LLM_BASE_URL",
    "GENESIS_LLM_MODEL",
    "FARM_ENGINEER_MODEL",
    "FARM_CODEX_MODEL",
    "FARM_EXECUTOR",
    "FARM_AUTO_RESEARCH",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GENESIS_GITHUB_TOKEN",
)


def _candidate_env_files() -> list[Path]:
    here = Path(__file__).resolve()
    root = here.parents[1]  # repo root (swarm/..)
    return [
        root / "dashboard" / "backend" / ".env.local",
        root / "dashboard" / "backend" / ".env",
        root / ".env.local",
        root / ".env",
    ]


def ensure_farm_env(*, force: bool = False) -> dict[str, bool]:
    """Populate os.environ from .env.local for keys Farm needs. Returns which were set."""
    global _LOADED
    found: dict[str, bool] = {k: bool(os.environ.get(k)) for k in _KEYS_OF_INTEREST}
    if _LOADED and not force:
        return found

    for path in _candidate_env_files():
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in _KEYS_OF_INTEREST:
                continue
            if val and not os.environ.get(key):
                os.environ[key] = val
                found[key] = True
    _LOADED = True
    return found
