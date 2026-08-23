"""Regression: Launcher Backend URL ↔ Farm API surface (connectivity contract).

Does not start uvicorn. Asserts the fixed local ports and that Farm routes exist
on the FastAPI app object after import.
"""

from __future__ import annotations

from pathlib import Path


def test_launcher_backend_port_is_8000() -> None:
    from launcher.health import BACKEND_PORT, BACKEND_URL

    assert BACKEND_PORT == 8000
    assert "8000" in BACKEND_URL
    assert "127.0.0.1" in BACKEND_URL or "localhost" in BACKEND_URL


def test_farm_frontend_default_api_matches_launcher() -> None:
    root = Path(__file__).resolve().parents[2]
    farm_page = root / "frontend" / "app" / "farm-engine" / "page.tsx"
    api_lib = root / "frontend" / "app" / "lib" / "backendApiBase.ts"
    text = farm_page.read_text(encoding="utf-8") + "\n" + api_lib.read_text(encoding="utf-8")
    assert "getBackendApiBase" in text or "localhost:8000" in text
    assert "LAUNCHER_BACKEND_DEFAULT" in api_lib.read_text(encoding="utf-8")
    assert "http://localhost:8000" in api_lib.read_text(encoding="utf-8")


def test_backend_exposes_health_status_and_farm_opire_routes() -> None:
    from app.main import app

    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/health" in paths
    assert "/api/status" in paths
    assert "/api/farm/opire" in paths
    assert "/api/farm/opire/tick" in paths
