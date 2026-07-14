"""Load dashboard/backend/.env into os.environ (local dev, no extra dependency)."""

from __future__ import annotations

import os
from pathlib import Path


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


def load_local_env() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    repo_root = backend_dir.parent.parent
    candidates = (
        backend_dir / ".env",
        backend_dir / ".env.local",
        backend_dir.parent / ".env",
        repo_root / ".env",
    )
    for path in candidates:
        if not path.is_file():
            continue
        override = path.name == ".env.local" and path.parent == backend_dir
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

    _load_secrets_file(backend_dir / "secrets" / "llm.key")
    _load_secrets_file(repo_root / "secrets" / "llm.key")

    # Aliases — one key can feed the OpenAI slot in the employee chain
    if not os.getenv("GENESIS_LLM_API_KEY") and os.getenv("OPENAI_API_KEY"):
        os.environ["GENESIS_LLM_API_KEY"] = os.environ["OPENAI_API_KEY"]
