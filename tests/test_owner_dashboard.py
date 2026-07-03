"""Owner dashboard API tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.main import app


def test_owner_dashboard_endpoint(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "launcher_config.json").write_text(
        '{"owner_name": "Рамиш", "first_run_complete": true}',
        encoding="utf-8",
    )
    get_integration(memory)

    client = TestClient(app)
    res = client.get("/api/owner/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert data["owner_name"] == "Рамиш"
    assert "last_launch_label" in data
    assert "daily_goal" in data
    assert "services_summary" in data
    assert "queue_pending" in data
    assert "products_count" in data
    assert "revenue_month_eur" in data
    assert "greeting" in data
    assert "recent_events" in data
    assert "tip" in data
    assert "uptime_label" in data

    reset_integration()
