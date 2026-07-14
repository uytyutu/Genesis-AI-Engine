from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.integration.swarm_bridge import ensure_swarm_importable


@pytest.fixture
def dispatcher():
    ensure_swarm_importable()
    from swarm.cloud_dispatcher import CloudDispatcher

    return CloudDispatcher()


def test_dispatcher_defaults_local(dispatcher):
    snap = dispatcher.snapshot()
    assert snap["execution_mode"] == "local"
    assert snap["pool_configured"] is False


def test_dispatcher_remote_without_pool_falls_back(monkeypatch):
    monkeypatch.setenv("FARM_EXECUTION_MODE", "remote")
    from swarm.cloud_dispatcher import CloudDispatcher

    d = CloudDispatcher(env_getter=lambda k: __import__("os").environ.get(k, ""))
    result = d.dispatch_batch(workers=5)
    assert result["fallback_local"] is True
    assert result["target"] == "local"


def test_probe_pool_online(dispatcher, monkeypatch):
    monkeypatch.setenv("FARM_WORKER_POOL_URL", "http://worker.test:8100")
    from swarm.cloud_dispatcher import CloudDispatcher

    d = CloudDispatcher(env_getter=lambda k: __import__("os").environ.get(k, ""))

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"ok": true}'
    mock_response.json.return_value = {"ok": True, "node": "vps-1"}

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = mock_response

    with patch("swarm.cloud_dispatcher.httpx.Client", return_value=mock_client):
        probe = d.probe_pool()

    assert probe["ok"] is True
    assert probe["status"] == "online"


def test_dispatch_remote_success(monkeypatch):
    monkeypatch.setenv("FARM_EXECUTION_MODE", "remote")
    monkeypatch.setenv("FARM_WORKER_POOL_URL", "http://worker.test:8100")

    health = MagicMock(status_code=200, content=b"{}", json=lambda: {"ok": True})
    execute = MagicMock(
        status_code=200,
        json=lambda: {"tasks_done": 3, "earned_eur": 0.15, "llm_cost_eur": 0.003},
    )

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = health
    mock_client.post.return_value = execute

    from swarm.cloud_dispatcher import CloudDispatcher

    d = CloudDispatcher(env_getter=lambda k: __import__("os").environ.get(k, ""))
    with patch("swarm.cloud_dispatcher.httpx.Client", return_value=mock_client):
        result = d.dispatch_batch(workers=10)

    assert result["ok"] is True
    assert result["target"] == "remote"
    assert result["tasks_done"] == 3
    assert result["fallback_local"] is False


def test_dispatch_offline_no_crash(monkeypatch):
    monkeypatch.setenv("FARM_EXECUTION_MODE", "remote")
    monkeypatch.setenv("FARM_WORKER_POOL_URL", "http://worker.test:8100")

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.side_effect = httpx.NetworkError("offline")

    from swarm.cloud_dispatcher import CloudDispatcher

    d = CloudDispatcher(env_getter=lambda k: __import__("os").environ.get(k, ""))
    with patch("swarm.cloud_dispatcher.httpx.Client", return_value=mock_client):
        result = d.dispatch_batch(workers=5)

    assert result["ok"] is False
    assert result["fallback_local"] is True


def test_priority_manager_includes_cloud(tmp_path):
    ensure_swarm_importable()
    from swarm.priority_manager import PriorityManager

    pm = PriorityManager(tmp_path)
    snap = pm.snapshot()
    assert "cloud_dispatcher" in snap
    assert snap["cloud_dispatcher"]["execution_mode"] == "local"
