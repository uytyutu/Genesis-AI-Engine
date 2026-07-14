from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.integration.swarm_bridge import ensure_swarm_importable


@pytest.fixture
def scale_adapter():
    ensure_swarm_importable()
    from swarm.adapter_scale_ai import ScaleAIAdapter

    return ScaleAIAdapter


def test_scale_no_key(scale_adapter):
    result = scale_adapter(api_key="").check_connection()
    assert result["status"] == "no_key"
    assert result["connected"] is False
    assert "Scale AI connected: no_key" in result["log_line"]


def test_scale_connected_200(scale_adapter, monkeypatch):
    monkeypatch.setenv("SCALE_API_KEY", "live_test_key")

    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = mock_response

    with patch("swarm.adapter_scale_ai.httpx.Client", return_value=mock_client):
        result = scale_adapter().check_connection()

    assert result["status"] == "connected"
    assert result["connected"] is True
    assert result["log_line"] == "Scale AI connected: connected"


def test_scale_unauthorized(scale_adapter):
    mock_response = MagicMock()
    mock_response.status_code = 401

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = mock_response

    with patch("swarm.adapter_scale_ai.httpx.Client", return_value=mock_client):
        result = scale_adapter(api_key="bad_key").check_connection()

    assert result["status"] == "unauthorized"
    assert result["connected"] is False
    assert "Scale AI connected: unauthorized" in result["log_line"]


def test_scale_offline_no_crash(scale_adapter):
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.side_effect = httpx.NetworkError("no internet")

    with patch("swarm.adapter_scale_ai.httpx.Client", return_value=mock_client):
        result = scale_adapter(api_key="live_test").check_connection()

    assert result["status"] == "offline"
    assert result["connected"] is False
    assert "offline" in result["log_line"]


@pytest.fixture
def farm_memory(tmp_path):
    return tmp_path / "memory"


def test_farm_start_includes_scale_probe(farm_memory, monkeypatch):
    from app.integration.business_mode_service import BusinessModeService
    from app.integration.finance_service import FinanceService
    from app.integration.micro_farm_service import MicroFarmService
    from app.integration.opportunity_service import OpportunityService

    monkeypatch.delenv("SCALE_API_KEY", raising=False)
    farm = MicroFarmService(
        OpportunityService(farm_memory),
        FinanceService(farm_memory),
        business_mode=BusinessModeService(farm_memory),
        memory_dir=farm_memory,
    )
    start = farm.start_swarm(workers=2)
    assert "scale_ai" in start
    assert start["scale_ai"]["status"] == "no_key"
    assert start.get("ok") is True
    assert farm._load_state()["running"] is True
