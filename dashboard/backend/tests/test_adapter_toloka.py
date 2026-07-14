from unittest.mock import MagicMock, patch

from app.integration.swarm_bridge import ensure_swarm_importable


def test_toloka_v2_auth_header_apikey_prefix():
    ensure_swarm_importable()
    from swarm.adapter_toloka import TolokaAdapter

    adapter = TolokaAdapter(api_key="secret-token")
    assert adapter._authorization() == "ApiKey secret-token"

    adapter2 = TolokaAdapter(api_key="ApiKey already-prefixed")
    assert adapter2._authorization() == "ApiKey already-prefixed"


def test_toloka_probe_list_projects_success():
    ensure_swarm_importable()
    from swarm.adapter_toloka import TolokaAdapter

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"projects":[{"id":"pp.x","status":"active"}],"pagination":{"total":1}}'
    mock_response.json.return_value = {
        "projects": [{"id": "pp.x", "status": "active"}],
        "pagination": {"total": 1},
    }

    with patch("swarm.adapter_toloka.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = TolokaAdapter(api_key="tok").check_connection()

    assert result["connected"] is True
    assert result["api_version"] == "v2-beta"
    call_args = mock_client.return_value.__enter__.return_value.get.call_args
    assert "/api/v2-beta/projects" in call_args[0][0]
    assert call_args[1]["headers"]["Authorization"] == "ApiKey tok"


def test_toloka_live_tasks_counts_active_projects():
    ensure_swarm_importable()
    from swarm.adapter_toloka import TolokaAdapter

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"{}"
    mock_response.json.return_value = {
        "projects": [
            {"id": "1", "status": "active"},
            {"id": "2", "status": "draft"},
        ],
        "pagination": {"total": 2},
    }

    with patch("swarm.adapter_toloka.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = TolokaAdapter(api_key="tok").fetch_live_tasks_hint()

    assert result["ok"] is True
    assert result["live_tasks"] is True
    assert result["count"] == 2
    assert result["active_count"] == 1
