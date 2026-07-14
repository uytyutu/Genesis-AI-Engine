"""Platform key vault — reads .env.local at runtime, never stores secrets in repo."""

from __future__ import annotations

import os
from typing import Any, Callable

ENV_FARM_LIVE = "FARM_LIVE_MODE"
DRY_RUN = "dry_run"
LIVE = "live"

# Exchange + AI keys required for farm live mode.
VAULT_ENTRIES: tuple[tuple[str, str, bool], ...] = (
    ("scale_ai", "SCALE_API_KEY", True),
    ("toloka", "TOLOKA_API_TOKEN", False),
    ("groq", "GENESIS_GROQ_API_KEY", True),
    ("groq_alt", "GROQ_API_KEY", False),
    ("gemini", "GENESIS_GEMINI_API_KEY", False),
    ("worker_pool", "FARM_WORKER_POOL_URL", False),
)


def _mask(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    if len(v) <= 6:
        return "••••"
    return f"{v[:3]}…{v[-4:]}"


class PlatformVault:
    """Secure status of platform keys — values never returned to UI/logs."""

    def __init__(self, *, env_getter: Callable[[str], str] | None = None) -> None:
        self._env = env_getter or (lambda key: os.getenv(key, "").strip())

    def farm_mode(self) -> str:
        raw = (self._env(ENV_FARM_LIVE) or DRY_RUN).lower()
        return LIVE if raw == LIVE else DRY_RUN

    def is_live(self) -> bool:
        return self.farm_mode() == LIVE

    def is_dry_run(self) -> bool:
        return not self.is_live()

    def entry_status(self, platform_id: str, env_var: str) -> dict[str, Any]:
        value = self._env(env_var)
        configured = bool(value)
        return {
            "platform_id": platform_id,
            "env_var": env_var,
            "configured": configured,
            "masked": _mask(value) if configured else "",
        }

    def snapshot(self) -> dict[str, Any]:
        seen: set[str] = set()
        platforms: list[dict[str, Any]] = []
        for platform_id, env_var, _required in VAULT_ENTRIES:
            if env_var in seen:
                continue
            seen.add(env_var)
            platforms.append(self.entry_status(platform_id, env_var))

        groq_ok = bool(self._env("GENESIS_GROQ_API_KEY") or self._env("GROQ_API_KEY"))
        scale_ok = bool(self._env("SCALE_API_KEY"))
        pool_ok = bool(self._env("FARM_WORKER_POOL_URL"))
        exchange_ok = scale_ok or bool(self._env("TOLOKA_API_TOKEN"))

        missing: list[str] = []
        if not groq_ok:
            missing.append("GENESIS_GROQ_API_KEY")
        if not exchange_ok:
            missing.append("SCALE_API_KEY или TOLOKA_API_TOKEN")
        if self._env("FARM_EXECUTION_MODE") == "remote" and not pool_ok:
            missing.append("FARM_WORKER_POOL_URL")

        live_ready = groq_ok and exchange_ok and self.is_live()
        return {
            "farm_mode": self.farm_mode(),
            "dry_run": self.is_dry_run(),
            "live_ready": live_ready,
            "storage": "dashboard/backend/.env.local (не в Git)",
            "platforms": platforms,
            "missing_for_live": missing,
            "go_live_note": (
                "Добавь ключи в .env.local → FARM_LIVE_MODE=live → перезапуск Genesis.exe"
                if not live_ready
                else "Боевой режим фермы активен — внешние API разрешены"
            ),
        }

    def assert_live_allowed(self, *, operation: str = "platform_call") -> None:
        if self.is_dry_run():
            raise PermissionError(f"farm_dry_run:{operation}")
        snap = self.snapshot()
        if snap["missing_for_live"]:
            raise PermissionError(f"farm_keys_missing:{','.join(snap['missing_for_live'])}")
