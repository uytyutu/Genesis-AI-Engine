"""Hive provider unit tests — mocked HTTP, no live key required."""

from __future__ import annotations

import pytest

from app.providers.hive.capabilities import hive_status
from app.providers.hive.client import HiveClient, HiveConfig, HiveError
from app.providers.hive import moderation


def test_hive_config_from_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HIVE_API_KEY", raising=False)
    assert HiveConfig.from_env() is None
    assert HiveClient().configured is False


def test_hive_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HIVE_API_KEY", "test-token")
    monkeypatch.setenv("HIVE_API_URL", "https://api.thehive.ai/")
    cfg = HiveConfig.from_env()
    assert cfg is not None
    assert cfg.api_key == "test-token"
    assert cfg.base_url == "https://api.thehive.ai"


def test_task_sync_posts_token_header(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    class _Resp:
        status_code = 200
        text = '{"ok": true}'

        def json(self) -> dict:
            return {"ok": True}

    class _Client:
        def __init__(self, *a, **k) -> None:
            pass

        def __enter__(self) -> "_Client":
            return self

        def __exit__(self, *a) -> None:
            return None

        def post(self, url, headers=None, json=None, data=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return _Resp()

    monkeypatch.setattr("app.providers.hive.client.httpx.Client", _Client)
    client = HiveClient(HiveConfig(api_key="secret-key"))
    out = client.task_sync({"text_data": "hello"})
    assert out == {"ok": True}
    assert captured["url"].endswith("/api/v2/task/sync")
    assert captured["headers"]["authorization"] == "token secret-key"
    assert captured["json"]["text_data"] == "hello"


def test_task_sync_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        status_code = 401
        text = "unauthorized"

        def json(self) -> dict:
            return {"error": "unauthorized"}

    class _Client:
        def __init__(self, *a, **k) -> None:
            pass

        def __enter__(self) -> "_Client":
            return self

        def __exit__(self, *a) -> None:
            return None

        def post(self, *a, **k):
            return _Resp()

    monkeypatch.setattr("app.providers.hive.client.httpx.Client", _Client)
    client = HiveClient(HiveConfig(api_key="bad"))
    with pytest.raises(HiveError) as ei:
        client.task_sync({"text_data": "x"})
    assert ei.value.status_code == 401


def test_moderate_text_uses_client(monkeypatch: pytest.MonkeyPatch) -> None:
    client = HiveClient(HiveConfig(api_key="k"))
    monkeypatch.setattr(client, "task_sync", lambda payload: {"echo": payload})
    out = moderation.moderate_text(client, "sample")
    assert out["echo"]["text_data"] == "sample"


def test_hive_status_not_wired_to_path_a(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HIVE_API_KEY", "x")
    st = hive_status()
    assert st["configured"] is True
    assert st["wired_into_path_a"] is False
    assert "hive_moderation" in st["capabilities"]
