"""Cloud Dispatcher — notebook orchestrates, worker pool executes remotely."""

from __future__ import annotations

import logging
import os
from typing import Any, Callable

import httpx

logger = logging.getLogger(__name__)

ENV_MODE = "FARM_EXECUTION_MODE"
ENV_POOL_URL = "FARM_WORKER_POOL_URL"
ENV_POOL_TOKEN = "FARM_WORKER_POOL_TOKEN"
DEFAULT_MODE = "local"
REMOTE_MODE = "remote"
PROBE_TIMEOUT_SEC = 6.0
DISPATCH_TIMEOUT_SEC = 120.0


class CloudDispatcher:
    """Routes profitable work to remote pool — laptop stays command center only."""

    def __init__(self, *, env_getter: Callable[[str], str] | None = None) -> None:
        self._env = env_getter or (lambda key: os.getenv(key, "").strip())

    def mode(self) -> str:
        raw = (self._env(ENV_MODE) or DEFAULT_MODE).lower()
        return REMOTE_MODE if raw == REMOTE_MODE else DEFAULT_MODE

    def pool_url(self) -> str:
        return (self._env(ENV_POOL_URL) or "").rstrip("/")

    def pool_token(self) -> str:
        return self._env(ENV_POOL_TOKEN)

    def pool_configured(self) -> bool:
        return bool(self.pool_url())

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        token = self.pool_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def probe_pool(self) -> dict[str, Any]:
        """Health check — safe when offline."""
        if not self.pool_configured():
            return {
                "ok": False,
                "status": "not_configured",
                "message": "Задай FARM_WORKER_POOL_URL в .env.local",
                "pool_url": "",
            }
        url = f"{self.pool_url()}/api/swarm/health"
        try:
            with httpx.Client(timeout=httpx.Timeout(PROBE_TIMEOUT_SEC, connect=3.0)) as client:
                response = client.get(url, headers=self._headers())
            if response.status_code == 200:
                body = response.json() if response.content else {}
                return {
                    "ok": True,
                    "status": "online",
                    "message": "Worker pool отвечает",
                    "pool_url": self.pool_url(),
                    "node": body.get("node") or body.get("role") or "worker",
                }
            return {
                "ok": False,
                "status": "error",
                "message": f"HTTP {response.status_code}",
                "pool_url": self.pool_url(),
                "http_status": response.status_code,
            }
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            log_line = f"Cloud pool offline: {type(exc).__name__}"
            logger.warning(log_line)
            return {
                "ok": False,
                "status": "offline",
                "message": "Пул недоступен — ферма выполнит задачу локально (тест)",
                "pool_url": self.pool_url(),
                "error": type(exc).__name__,
            }
        except Exception as exc:
            logger.warning("Cloud pool probe error: %s", exc)
            return {
                "ok": False,
                "status": "error",
                "message": str(exc)[:120],
                "pool_url": self.pool_url(),
                "error": type(exc).__name__,
            }

    def should_dispatch_remote(self, *, adapter_id: str, profitable: bool = True) -> bool:
        if self.mode() != REMOTE_MODE:
            return False
        if not profitable:
            return False
        if adapter_id not in {"ai_labeling", "text_classify", "data_clean", "record_verify"}:
            return False
        return self.probe_pool().get("ok") is True

    def resolve_execution(
        self,
        *,
        adapter_id: str = "ai_labeling",
        profitable: bool = True,
    ) -> dict[str, Any]:
        pool = self.probe_pool() if self.pool_configured() else {
            "ok": False,
            "status": "not_configured",
            "message": "Локальный тест — пул не задан",
            "pool_url": "",
        }
        if self.should_dispatch_remote(adapter_id=adapter_id, profitable=profitable):
            return {
                "target": REMOTE_MODE,
                "mode": self.mode(),
                "adapter_id": adapter_id,
                "pool": pool,
                "note": "Ноутбук = пульт · исполнение на worker pool",
            }
        reason = (
            "Режим local — только тесты на ноутбуке"
            if self.mode() == DEFAULT_MODE
            else pool.get("message") or "Пул недоступен — fallback local"
        )
        return {
            "target": DEFAULT_MODE,
            "mode": self.mode(),
            "adapter_id": adapter_id,
            "pool": pool,
            "note": reason,
        }

    def dispatch_batch(
        self,
        *,
        workers: int,
        adapter_id: str = "ai_labeling",
    ) -> dict[str, Any]:
        """POST batch to remote worker pool — never raises."""
        execution = self.resolve_execution(adapter_id=adapter_id, profitable=True)
        if execution["target"] != REMOTE_MODE:
            return {
                "ok": False,
                "target": DEFAULT_MODE,
                "fallback_local": True,
                "message": execution.get("note") or "Локальное исполнение",
                "execution": execution,
            }

        url = f"{self.pool_url()}/api/swarm/execute"
        payload = {"workers": max(1, min(200, int(workers))), "adapter_id": adapter_id}
        try:
            with httpx.Client(timeout=httpx.Timeout(DISPATCH_TIMEOUT_SEC, connect=5.0)) as client:
                response = client.post(url, headers=self._headers(), json=payload)
            if response.status_code != 200:
                return {
                    "ok": False,
                    "target": REMOTE_MODE,
                    "fallback_local": True,
                    "message": f"Worker pool HTTP {response.status_code}",
                    "http_status": response.status_code,
                    "execution": execution,
                }
            data = response.json()
            data.setdefault("ok", True)
            data["target"] = REMOTE_MODE
            data["fallback_local"] = False
            data["execution"] = execution
            data["message"] = data.get("message") or f"Удалённо: {data.get('tasks_done', 0)} задач"
            logger.info("Cloud dispatch ok: %s tasks", data.get("tasks_done"))
            return data
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            logger.warning("Cloud dispatch offline: %s", type(exc).__name__)
            return {
                "ok": False,
                "target": REMOTE_MODE,
                "fallback_local": True,
                "message": "Пул offline — fallback на локальный тест",
                "error": type(exc).__name__,
                "execution": execution,
            }
        except Exception as exc:
            logger.warning("Cloud dispatch error: %s", exc)
            return {
                "ok": False,
                "target": REMOTE_MODE,
                "fallback_local": True,
                "message": str(exc)[:120],
                "error": type(exc).__name__,
                "execution": execution,
            }

    def snapshot(self) -> dict[str, Any]:
        pool = self.probe_pool() if self.pool_configured() else {
            "ok": False,
            "status": "not_configured",
            "message": "Ноутбук = пульт. Задай FARM_WORKER_POOL_URL для продакшна.",
            "pool_url": "",
        }
        return {
            "execution_mode": self.mode(),
            "local_note": "local = тесты на ноутбуке · remote = исполнение на VPS/Lambda",
            "pool_configured": self.pool_configured(),
            "pool": pool,
            "env_vars": {
                "mode": ENV_MODE,
                "pool_url": ENV_POOL_URL,
                "pool_token": ENV_POOL_TOKEN,
            },
        }
