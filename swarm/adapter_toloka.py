"""Toloka Pipeline API v2 adapter — platform.toloka.ai (see api-1.json OpenAPI)."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

ENV_VAR = "TOLOKA_API_TOKEN"
DEFAULT_BASE = os.getenv("TOLOKA_API_BASE_URL", "https://platform.toloka.ai").rstrip("/")
PROJECTS_PATH = "/api/v2-beta/projects"
TIMEOUT = 8.0


class TolokaAdapter:
    """Never raises — farm keeps running."""

    def __init__(self, *, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = (api_key if api_key is not None else os.getenv(ENV_VAR, "")).strip()
        self._base = (base_url or DEFAULT_BASE).rstrip("/")

    def configured(self) -> bool:
        return bool(self._api_key)

    def _authorization(self) -> str:
        token = self._api_key
        lower = token.lower()
        if lower.startswith("apikey ") or lower.startswith("oauth "):
            return token
        return f"ApiKey {token}"

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": self._authorization(),
        }

    def _get_json(self, path: str, *, params: dict[str, Any] | None = None) -> tuple[int, Any]:
        with httpx.Client(timeout=httpx.Timeout(TIMEOUT, connect=4.0)) as client:
            response = client.get(
                f"{self._base}{path}",
                headers=self._headers(),
                params=params or {},
            )
        body: Any = {}
        if response.content:
            try:
                body = response.json()
            except ValueError:
                body = {}
        return response.status_code, body

    def _post_json(self, path: str, *, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
        with httpx.Client(timeout=httpx.Timeout(TIMEOUT, connect=4.0)) as client:
            response = client.post(
                f"{self._base}{path}",
                headers={**self._headers(), "Content-Type": "application/json"},
                json=payload or {},
            )
        body: Any = {}
        if response.content:
            try:
                body = response.json()
            except ValueError:
                body = {}
        return response.status_code, body

    def list_projects(self, *, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        if not self.configured():
            return {"ok": False, "projects": [], "message": "no_key"}
        try:
            status, body = self._get_json(PROJECTS_PATH, params={"limit": limit, "offset": offset})
            if status != 200:
                return {"ok": False, "projects": [], "message": f"HTTP {status}", "http_status": status}
            projects = body.get("projects") if isinstance(body, dict) else []
            return {"ok": True, "projects": projects if isinstance(projects, list) else [], "http_status": status}
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            return {"ok": False, "projects": [], "message": type(exc).__name__}

    def list_project_datasets(self, project_id: str, *, limit: int = 20) -> dict[str, Any]:
        if not self.configured():
            return {"ok": False, "datasets": [], "message": "no_key"}
        try:
            status, body = self._get_json(
                f"/api/v2-beta/projects/{project_id}/datasets",
                params={"limit": limit, "offset": 0},
            )
            if status != 200:
                return {"ok": False, "datasets": [], "message": f"HTTP {status}", "http_status": status}
            datasets = body.get("datasets") if isinstance(body, dict) else []
            return {"ok": True, "datasets": datasets if isinstance(datasets, list) else [], "http_status": status}
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            return {"ok": False, "datasets": [], "message": type(exc).__name__}

    def create_dataset(self, project_id: str, *, name: str) -> dict[str, Any]:
        if not self.configured():
            return {"ok": False, "message": "no_key"}
        try:
            status, body = self._post_json(
                f"/api/v2-beta/projects/{project_id}/datasets",
                payload={"name": name[:128]},
            )
            if status != 200:
                return {"ok": False, "message": f"HTTP {status}", "http_status": status, "body": body}
            dataset = body if isinstance(body, dict) else {}
            return {"ok": True, "dataset": dataset, "http_status": status}
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            return {"ok": False, "message": type(exc).__name__}

    def add_dataset_items(
        self,
        dataset_id: str,
        *,
        items: list[dict[str, Any]],
        fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not self.configured():
            return {"ok": False, "message": "no_key"}
        if not items:
            return {"ok": False, "message": "empty batch"}
        payload: dict[str, Any] = {"items": items}
        if fields:
            payload["fields"] = fields
        try:
            status, body = self._post_json(f"/api/v2-beta/datasets/{dataset_id}/items", payload=payload)
            if status != 200:
                msg = body.get("message") if isinstance(body, dict) else None
                return {
                    "ok": False,
                    "message": str(msg or f"HTTP {status}"),
                    "http_status": status,
                    "body": body,
                }
            return {"ok": True, "http_status": status, "body": body}
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            return {"ok": False, "message": type(exc).__name__}

    def list_project_pipelines(self, project_id: str, *, limit: int = 20) -> dict[str, Any]:
        if not self.configured():
            return {"ok": False, "pipelines": [], "message": "no_key"}
        try:
            status, body = self._get_json(
                f"/api/v2-beta/projects/{project_id}/pipelines",
                params={"limit": limit, "offset": 0},
            )
            if status != 200:
                return {"ok": False, "pipelines": [], "message": f"HTTP {status}", "http_status": status}
            pipelines = body.get("pipelines") if isinstance(body, dict) else []
            return {"ok": True, "pipelines": pipelines if isinstance(pipelines, list) else [], "http_status": status}
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            return {"ok": False, "pipelines": [], "message": type(exc).__name__}

    def attach_pipeline_dataset(self, pipeline_id: str, *, dataset_id: str) -> dict[str, Any]:
        if not self.configured():
            return {"ok": False, "message": "no_key"}
        try:
            status, body = self._post_json(
                f"/api/v2-beta/pipelines/{pipeline_id}/dataset",
                payload={"datasetId": dataset_id},
            )
            if status not in {200, 204}:
                msg = body.get("message") if isinstance(body, dict) else None
                return {"ok": False, "message": str(msg or f"HTTP {status}"), "http_status": status}
            return {"ok": True, "http_status": status}
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            return {"ok": False, "message": type(exc).__name__}

    def start_pipeline_run(self, pipeline_id: str) -> dict[str, Any]:
        if not self.configured():
            return {"ok": False, "message": "no_key"}
        try:
            status, body = self._post_json(f"/api/v2-beta/pipelines/{pipeline_id}/runs")
            if status != 200:
                msg = body.get("message") if isinstance(body, dict) else None
                return {"ok": False, "message": str(msg or f"HTTP {status}"), "http_status": status, "body": body}
            run = body if isinstance(body, dict) else {}
            return {"ok": True, "run": run, "http_status": status}
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            return {"ok": False, "message": type(exc).__name__}

    def get_pipeline_run(self, run_id: str) -> dict[str, Any]:
        if not self.configured():
            return {"ok": False, "message": "no_key"}
        try:
            status, body = self._get_json(f"/api/v2-beta/runs/{run_id}")
            if status != 200:
                msg = body.get("message") if isinstance(body, dict) else None
                return {"ok": False, "message": str(msg or f"HTTP {status}"), "http_status": status}
            run = body if isinstance(body, dict) else {}
            return {"ok": True, "run": run, "http_status": status}
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            return {"ok": False, "message": type(exc).__name__}

    def check_connection(self) -> dict[str, Any]:
        if not self.configured():
            return {
                "platform": "toloka",
                "configured": False,
                "connected": False,
                "status": "no_key",
                "message": "Добавь TOLOKA_API_TOKEN в .env.local (формат ApiKey …)",
                "env_var": ENV_VAR,
                "api_version": "v2-beta",
            }
        return self._probe()

    def fetch_balance(self) -> dict[str, Any]:
        """Pipeline API v2 has no wallet endpoint — CEO checks toloka.ai dashboard."""
        if not self.configured():
            return {"ok": False, "balance_usd": None, "message": "no_key"}
        probe = self._probe()
        return {
            "ok": probe.get("connected", False),
            "balance_usd": None,
            "message": "Баланс Toloka — toloka.ai → Wallet → Withdraw (Pipeline API v2 без wallet endpoint)",
            "connection": probe,
        }

    def fetch_live_tasks_hint(self) -> dict[str, Any]:
        """List projects — proves live Pipeline API data (not simulation)."""
        if not self.configured():
            return {"ok": False, "live_tasks": False, "count": 0}
        try:
            status, body = self._get_json(PROJECTS_PATH, params={"limit": 20, "offset": 0})
            if status != 200:
                return {
                    "ok": False,
                    "live_tasks": False,
                    "http_status": status,
                    "message": f"Toloka projects HTTP {status}",
                    "api_version": "v2-beta",
                }
            projects = body.get("projects") if isinstance(body, dict) else []
            if not isinstance(projects, list):
                projects = []
            active = [p for p in projects if isinstance(p, dict) and p.get("status") == "active"]
            count = len(projects)
            active_count = len(active)
            return {
                "ok": True,
                "live_tasks": count > 0,
                "count": count,
                "active_count": active_count,
                "message": f"Toloka Pipeline API: {count} project(s), {active_count} active",
                "api_version": "v2-beta",
            }
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            return {"ok": False, "live_tasks": False, "error": type(exc).__name__}
        except Exception as exc:
            return {"ok": False, "live_tasks": False, "message": str(exc)[:120]}

    def _probe(self) -> dict[str, Any]:
        try:
            status, body = self._get_json(PROJECTS_PATH, params={"limit": 1})
            if status == 200:
                projects = body.get("projects") if isinstance(body, dict) else []
                total = body.get("pagination", {}).get("total") if isinstance(body, dict) else None
                count = len(projects) if isinstance(projects, list) else 0
                return {
                    "platform": "toloka",
                    "configured": True,
                    "connected": True,
                    "status": "connected",
                    "message": "Toloka Pipeline API v2 отвечает",
                    "http_status": 200,
                    "env_var": ENV_VAR,
                    "api_version": "v2-beta",
                    "projects_visible": count,
                    "projects_total": total,
                }
            if status in {401, 403}:
                return {
                    "platform": "toloka",
                    "configured": True,
                    "connected": False,
                    "status": "unauthorized",
                    "message": "Неверный TOLOKA_API_TOKEN (нужен ApiKey из platform.toloka.ai)",
                    "http_status": status,
                    "env_var": ENV_VAR,
                    "api_version": "v2-beta",
                }
            return {
                "platform": "toloka",
                "configured": True,
                "connected": False,
                "status": "error",
                "message": f"HTTP {status}",
                "http_status": status,
                "env_var": ENV_VAR,
                "api_version": "v2-beta",
            }
        except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
            return {
                "platform": "toloka",
                "configured": True,
                "connected": False,
                "status": "offline",
                "message": str(type(exc).__name__),
                "env_var": ENV_VAR,
                "api_version": "v2-beta",
            }


def check_toloka_connection(**kwargs: Any) -> dict[str, Any]:
    return TolokaAdapter(**kwargs).check_connection()
