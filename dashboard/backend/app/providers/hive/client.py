"""Hive V2 HTTP client — sole entry point for api.thehive.ai."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://api.thehive.ai"


class HiveError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, body: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


@dataclass(frozen=True)
class HiveConfig:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    timeout_s: float = 60.0

    @classmethod
    def from_env(cls) -> HiveConfig | None:
        key = (os.getenv("HIVE_API_KEY") or "").strip()
        if not key:
            return None
        base = (os.getenv("HIVE_API_URL") or DEFAULT_BASE_URL).strip().rstrip("/")
        return cls(api_key=key, base_url=base or DEFAULT_BASE_URL)

    @property
    def configured(self) -> bool:
        return bool(self.api_key.strip())


class HiveClient:
    """Thin wrapper: Authorization token <key> → /api/v2/task/sync|async."""

    def __init__(self, config: HiveConfig | None = None) -> None:
        self._config = config if config is not None else HiveConfig.from_env()

    @property
    def configured(self) -> bool:
        return self._config is not None and self._config.configured

    def _headers(self) -> dict[str, str]:
        assert self._config is not None
        return {
            "authorization": f"token {self._config.api_key}",
            "accept": "application/json",
            "content-type": "application/json",
        }

    def _url(self, path: str) -> str:
        assert self._config is not None
        return f"{self._config.base_url.rstrip('/')}/{path.lstrip('/')}"

    def task_sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post_json("api/v2/task/sync", payload)

    def task_async(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post_json("api/v2/task/async", payload)

    def task_sync_media_url(self, url: str, **extra: Any) -> dict[str, Any]:
        """Common visual path: image/video URL as form field `url` (Hive V2)."""
        if not self.configured or self._config is None:
            raise HiveError("HIVE_API_KEY is not set")
        data: dict[str, Any] = {"url": url, **extra}
        with httpx.Client(timeout=self._config.timeout_s) as client:
            resp = client.post(
                self._url("api/v2/task/sync"),
                headers={
                    "authorization": f"token {self._config.api_key}",
                    "accept": "application/json",
                },
                data=data,
            )
        return self._parse(resp)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.configured or self._config is None:
            raise HiveError("HIVE_API_KEY is not set")
        with httpx.Client(timeout=self._config.timeout_s) as client:
            resp = client.post(self._url(path), headers=self._headers(), json=payload)
        return self._parse(resp)

    @staticmethod
    def _parse(resp: httpx.Response) -> dict[str, Any]:
        text = resp.text or ""
        if resp.status_code >= 400:
            raise HiveError(
                f"Hive HTTP {resp.status_code}",
                status_code=resp.status_code,
                body=text[:2000],
            )
        try:
            data = resp.json()
        except ValueError as exc:
            raise HiveError("Hive returned non-JSON", status_code=resp.status_code, body=text[:500]) from exc
        if not isinstance(data, dict):
            return {"raw": data}
        return data
