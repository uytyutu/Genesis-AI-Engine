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


def fetch_scale_live_tasks(*, api_key: str | None = None, limit: int = 5) -> dict[str, Any]:
    """Return real task rows from Scale when live key works."""
    adapter = ScaleAIAdapter(api_key=api_key)
    if not adapter.configured():
        return {"ok": False, "live_tasks": False, "count": 0, "message": "no_key"}
    url = f"{adapter._base_url}{PROBE_PATH}"
    try:
        with httpx.Client(timeout=httpx.Timeout(CONNECT_TIMEOUT_SEC, connect=4.0)) as client:
            response = client.get(
                url,
                headers={"Accept": "application/json"},
                auth=(adapter._api_key, ""),
                params={"limit": max(1, min(20, limit))},
            )
        if response.status_code != 200:
            return {
                "ok": False,
                "live_tasks": False,
                "http_status": response.status_code,
                "message": f"Scale tasks HTTP {response.status_code}",
            }
        body = response.json() if response.content else {}
        docs = body.get("docs") if isinstance(body, dict) else body
        count = len(docs) if isinstance(docs, list) else 0
        return {
            "ok": True,
            "live_tasks": count > 0,
            "count": count,
            "sample_ids": [str(d.get("task_id") or d.get("id") or "")[:16] for d in (docs or [])[:3]]
            if isinstance(docs, list)
            else [],
            "message": f"Scale API: {count} task(s) in queue",
        }
    except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
        return {"ok": False, "live_tasks": False, "error": type(exc).__name__}
    except Exception as exc:
        return {"ok": False, "live_tasks": False, "message": str(exc)[:120]}


def fetch_scale_balance(*, api_key: str | None = None) -> dict[str, Any]:
    """Balance when Scale exposes billing API — else honest dashboard fallback."""
    adapter = ScaleAIAdapter(api_key=api_key)
    if not adapter.configured():
        return {"ok": False, "balance_usd": None, "message": "no_key"}
    for path in ("/billing/balance", "/user/balance", "/account/balance"):
        try:
            with httpx.Client(timeout=httpx.Timeout(CONNECT_TIMEOUT_SEC, connect=4.0)) as client:
                response = client.get(
                    f"{adapter._base_url}{path}",
                    headers={"Accept": "application/json"},
                    auth=(adapter._api_key, ""),
                )
            if response.status_code == 200:
                data = response.json() if response.content else {}
                amount = (
                    data.get("balance")
                    or data.get("available_balance")
                    or data.get("amount")
                    or (data.get("data") or {}).get("balance")
                )
                if amount is not None:
                    return {
                        "ok": True,
                        "balance_usd": float(amount),
                        "currency": "USD",
                        "source": path,
                    }
        except Exception:
            continue
    return {
        "ok": False,
        "balance_usd": None,
        "message": "Баланс Scale — вывод вручную: scale.com → Billing → Withdraw на Stripe",
    }
