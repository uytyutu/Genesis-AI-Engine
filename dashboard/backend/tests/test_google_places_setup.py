import os
from pathlib import Path

from app.config import env_config_file
from app.integration.google_places_service import GooglePlacesService


def test_places_setup_status_not_configured():
    status = GooglePlacesService(use_env=False).setup_status()
    assert status["configured"] is False
    assert status["autopilot_ready"] is False
    assert status["env_var"] == "GOOGLE_PLACES_API_KEY"
    assert status["primary_config_file"] == env_config_file()
    assert len(status["setup_steps"]) >= 4
    assert "Places API" in status["setup_steps"][0]["detail"]


def test_places_setup_status_configured():
    status = GooglePlacesService(api_key="test-key-abc", use_env=False).setup_status()
    assert status["configured"] is True
    assert status["autopilot_ready"] is True
    assert status["status_label"] == "Автопилот готов"


def test_env_places_example_exists():
    path = Path(__file__).resolve().parents[1] / "env.places.example"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "GOOGLE_PLACES_API_KEY" in text
