"""Payment monitor — exchange balances via vault keys (never from repo configs)."""

from __future__ import annotations

import os
from typing import Any, Callable

from swarm.adapter_scale_ai import fetch_scale_balance, fetch_scale_live_tasks
from swarm.adapter_toloka import TolokaAdapter
from swarm.platform_vault import PlatformVault

ENV_SCALE_KEY = "SCALE_API_KEY"
ENV_TOLOKA_KEY = "TOLOKA_API_TOKEN"


class PaymentMonitor:
    """Poll Scale + Toloka balances and live task availability."""

    def __init__(
        self,
        vault: PlatformVault | None = None,
        *,
        env_getter: Callable[[str], str] | None = None,
    ) -> None:
        self._vault = vault or PlatformVault(env_getter=env_getter)
        self._env = env_getter or (lambda k: os.getenv(k, "").strip())

    def _key(self, env_var: str) -> str:
        return self._vault.secret(env_var)

    def scan_scale(self) -> dict[str, Any]:
        key = self._key(ENV_SCALE_KEY)
        balance = fetch_scale_balance(api_key=key or None)
        tasks = fetch_scale_live_tasks(api_key=key or None)
        return {
            "platform": "scale_ai",
            "configured": bool(key),
            "connected": bool(tasks.get("ok") or balance.get("ok")),
            "balance_usd": balance.get("balance_usd"),
            "balance_note": balance.get("message"),
            "live_tasks": tasks.get("live_tasks", False),
            "task_count": tasks.get("count", 0),
            "tasks_message": tasks.get("message"),
            "withdraw_note": "Вывод: scale.com → Billing → Withdraw → твой Stripe (вручную)",
        }

    def scan_toloka(self) -> dict[str, Any]:
        key = self._key(ENV_TOLOKA_KEY)
        adapter = TolokaAdapter(api_key=key or None)
        conn = adapter.check_connection()
        balance = adapter.fetch_balance()
        tasks = adapter.fetch_live_tasks_hint()
        return {
            "platform": "toloka",
            "configured": bool(key),
            "connected": bool(conn.get("connected")),
            "status": conn.get("status"),
            "balance_usd": balance.get("balance_usd"),
            "balance_note": balance.get("message"),
            "live_tasks": tasks.get("live_tasks", False),
            "task_count": tasks.get("count", 0),
            "tasks_message": tasks.get("message"),
            "withdraw_note": "Вывод: toloka.ai → Wallet → Withdraw → Stripe (вручную)",
        }

    def scan_all(self) -> dict[str, Any]:
        vault = self._vault.snapshot()
        scale = self.scan_scale()
        toloka = self.scan_toloka()
        any_live = bool(scale.get("live_tasks") or toloka.get("live_tasks"))
        any_balance = scale.get("balance_usd") is not None or toloka.get("balance_usd") is not None
        return {
            "farm_mode": vault.get("farm_mode"),
            "execution_mode": vault.get("execution_mode"),
            "live_ready": vault.get("live_ready"),
            "key_source": vault.get("storage"),
            "any_live_tasks": any_live,
            "any_balance_api": any_balance,
            "scale": scale,
            "toloka": toloka,
            "ceo_note": (
                "Genesis не выводит на Stripe автоматически — только алерт когда пора зайти на биржу."
            ),
        }
