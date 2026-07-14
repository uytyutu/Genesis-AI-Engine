"""Scale AI platform adapter — connection probe and future task submission.

Template: set SCALE_API_KEY in dashboard/backend/.env.local and restart Genesis.exe.
Docs: https://scale.com/docs/api-reference/authentication
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

ENV_VAR = "SCALE_API_KEY"
DEFAULT_BASE_URL = "https://api.scale.com/v1"
PROBE_PATH = "/tasks"
CONNECT_TIMEOUT_SEC = 8.0


class ScaleAIAdapter:
    """Modular adapter — never raises; farm keeps running on network errors."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_sec: float = CONNECT_TIMEOUT_SEC,
    ) -> None:
        # Paste your key in .env.local — not in this file:
        # SCALE_API_KEY=live_your_key_here
        self._api_key = (api_key if api_key is not None else os.getenv(ENV_VAR, "")).strip()
        self._base_url = (
            base_url or os.getenv("SCALE_API_BASE_URL", DEFAULT_BASE_URL)
        ).rstrip("/")
        self._timeout = timeout_sec

    def configured(self) -> bool:
        return bool(self._api_key)

    def _status_label(self, code: str) -> str:
        return {
            "connected": "connected",
            "no_key": "no_key",
            "unauthorized": "unauthorized",
            "offline": "offline",
            "error": "error",
        }.get(code, code)

    def check_connection(self) -> dict[str, Any]:
        """Probe Scale API — safe when offline or key missing."""
        if not self.configured():
            status = "no_key"
            log_line = "Scale AI connected: no_key — add SCALE_API_KEY to .env.local"
            logger.info(log_line)
            return {
                "platform": "scale_ai",
                "configured": False,
                "connected": False,
                "status": status,
                "status_label": self._status_label(status),
                "log_line": log_line,
                "message": "Ключ не задан — внутренняя ферма работает без Scale.",
                "env_var": ENV_VAR,
            }

        url = f"{self._base_url}{PROBE_PATH}"
        headers = {"Accept": "application/json"}
        try:
            with httpx.Client(timeout=httpx.Timeout(self._timeout, connect=4.0)) as client:
                # Scale: Basic auth — API key as username, blank password.
                response = client.get(
                    url,
                    headers=headers,
                    auth=(self._api_key, ""),
                    params={"limit": 1},
                )
            if response.status_code == 200:
                status = "connected"
                detail = "API отвечает"
            elif response.status_code == 401:
                status = "unauthorized"
                detail = "Неверный ключ — проверь SCALE_API_KEY"
            elif response.status_code == 403:
                status = "unauthorized"
                detail = "Доступ запрещён — нужна роль Manager в Scale"
            else:
                status = "error"
                detail = f"HTTP {response.status_code}"
            connected = status == "connected"
            log_line = f"Scale AI connected: {status}"
            logger.info(log_line)
            return {
                "platform": "scale_ai",
                "configured": True,
                "connected": connected,
                "status": status,
                "status_label": self._status_label(status),
                "log_line": log_line,
                "message": detail,
                "http_status": response.status_code,
                "env_var": ENV_VAR,
            }
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            status = "offline"
            log_line = f"Scale AI connected: offline — {type(exc).__name__}"
            logger.warning(log_line)
            return {
                "platform": "scale_ai",
                "configured": True,
                "connected": False,
                "status": status,
                "status_label": self._status_label(status),
                "log_line": log_line,
                "message": "Нет интернета или Scale недоступен — ферма продолжит на внутренней очереди.",
                "error": type(exc).__name__,
                "env_var": ENV_VAR,
            }
        except Exception as exc:
            status = "error"
            log_line = f"Scale AI connected: error — {type(exc).__name__}"
            logger.warning(log_line)
            return {
                "platform": "scale_ai",
                "configured": True,
                "connected": False,
                "status": status,
                "status_label": self._status_label(status),
                "log_line": log_line,
                "message": str(exc)[:120],
                "error": type(exc).__name__,
                "env_var": ENV_VAR,
            }


def check_scale_ai_connection(**kwargs: Any) -> dict[str, Any]:
    """Factory helper for micro_farm_service and tests."""
    return ScaleAIAdapter(**kwargs).check_connection()
