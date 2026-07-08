"""Persist local secrets into .env files (same paths as env_loader). Never log values."""

from __future__ import annotations

import os
import re
from pathlib import Path

_ENV_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


class SecretsEnvService:
    def __init__(self) -> None:
        self._backend_dir = Path(__file__).resolve().parents[2]
        self._repo_root = self._backend_dir.parent.parent

    def env_candidates(self) -> tuple[Path, ...]:
        return (
            self._backend_dir / ".env",
            self._backend_dir.parent / ".env",
            self._repo_root / ".env",
        )

    def preferred_env_path(self) -> Path:
        local = self._backend_dir / ".env.local"
        if local.is_file():
            return local
        for path in self.env_candidates():
            if path.is_file():
                return path
        return local

    def local_write_allowed(self) -> bool:
        """Local dev only — production secrets belong in host env vars."""
        from app.config import is_production

        if is_production():
            return False
        if os.getenv("GENESIS_ALLOW_LOCAL_SECRETS", "").strip() == "1":
            return True
        if os.getenv("RENDER") or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("VERCEL"):
            return False
        return True

    def upsert(self, key: str, value: str) -> Path:
        if not _ENV_KEY_RE.match(key):
            raise ValueError("Invalid environment variable name")
        if "\n" in value or "\r" in value:
            raise ValueError("Invalid secret value")
        path = self.preferred_env_path()
        lines: list[str] = []
        if path.is_file():
            lines = path.read_text(encoding="utf-8").splitlines()
        found = False
        out: list[str] = []
        prefix = f"{key}="
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(prefix) or stripped.startswith(f"{key} ="):
                out.append(f"{key}={value}")
                found = True
            else:
                out.append(line)
        if not found:
            if out and out[-1].strip():
                out.append("")
            out.append("# Genesis AI — configured via Setup Wizard")
            out.append(f"{key}={value}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        os.environ[key] = value
        return path

    def env_file_label(self) -> str:
        path = self.preferred_env_path()
        try:
            return str(path.relative_to(self._repo_root))
        except ValueError:
            return str(path)
