"""Load dashboard/backend env files into os.environ (local dev, no extra dependency)."""

from __future__ import annotations

import os
import warnings
from pathlib import Path

from app.config import SECRET_ENV_VARS, TEST_MOCK_KEYS, is_test_env


def _apply_env_line(key: str, value: str, *, override: bool = False) -> None:
    """Skip empty values — empty .env must not block a later secrets file."""
    if not key or not value:
        return
    existing = os.environ.get(key, "")
    if override or not existing:
        os.environ[key] = value


def _load_secrets_file(path: Path) -> None:
    if not path.is_file():
        return
    raw = path.read_text(encoding="utf-8").strip()
    if not raw or raw.startswith("#"):
        return
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            _apply_env_line(key.strip(), value.strip().strip('"').strip("'"))
        elif line.startswith("sk-") or len(line) > 12:
            _apply_env_line("GENESIS_LLM_API_KEY", line)


def _load_env_file(path: Path, *, override: bool = False) -> None:
    if not path.is_file():
        return
    if path.name == ".env.local" and is_test_env():
        warn_env_local_access(path, action="load")
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        _apply_env_line(
            key.strip(),
            value.strip().strip('"').strip("'"),
            override=override,
        )


def warn_env_local_access(path: Path, *, action: str = "read") -> None:
    """Warn when test code touches real .env.local instead of fixtures."""
    if not is_test_env():
        return
    if path.name != ".env.local":
        return
    warnings.warn(
        f"Test {action} on .env.local ({path}) — use .env.test, conftest fixtures, "
        "or constructor api_keys instead.",
        UserWarning,
        stacklevel=3,
    )


def read_env_local_text(path: Path) -> str:
    """Read .env.local with test guard — prefer load_local_env()."""
    warn_env_local_access(path, action="read")
    if is_test_env():
        return ""
    return path.read_text(encoding="utf-8-sig")


def clear_secret_env() -> None:
    """Remove real API keys from os.environ (pytest session bootstrap)."""
    for key in SECRET_ENV_VARS:
        os.environ.pop(key, None)


def apply_test_env_defaults() -> None:
    """Stub secrets in test profile — empty unless a test overrides via monkeypatch."""
    os.environ["APP_ENV"] = "test"
    os.environ["ENVIRONMENT"] = "test"
    for key, value in TEST_MOCK_KEYS.items():
        os.environ.setdefault(key, value)


def load_local_env() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    repo_root = backend_dir.parent.parent

    if is_test_env():
        clear_secret_env()
        apply_test_env_defaults()
        _load_env_file(backend_dir / ".env.test", override=True)
        _apply_key_aliases()
        return

    candidates = (
        backend_dir / ".env",
        backend_dir / ".env.local",
        backend_dir.parent / ".env",
        repo_root / ".env",
    )
    for path in candidates:
        override = path.name == ".env.local" and path.parent == backend_dir
        _load_env_file(path, override=override)

    _load_secrets_file(backend_dir / "secrets" / "llm.key")
    _load_secrets_file(repo_root / "secrets" / "llm.key")

    _apply_key_aliases()


def _apply_key_aliases() -> None:
    """Aliases — one key can feed the OpenAI/Groq slots in the employee chain."""
    if not os.getenv("GENESIS_LLM_API_KEY") and os.getenv("OPENAI_API_KEY"):
        os.environ["GENESIS_LLM_API_KEY"] = os.environ["OPENAI_API_KEY"]
    if not os.getenv("GENESIS_GROQ_API_KEY") and os.getenv("GROQ_API_KEY"):
        os.environ["GENESIS_GROQ_API_KEY"] = os.environ["GROQ_API_KEY"]
