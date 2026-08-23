"""Provider Gateway foundation + backend preflight."""

from __future__ import annotations

from pathlib import Path

from app.integration.provider_gateway import (
    Modality,
    ProviderGateway,
    pipeline_stages,
)
from launcher.backend_preflight import run_backend_import_preflight


def test_provider_gateway_catalog_and_fallback(tmp_path: Path) -> None:
    gw = ProviderGateway(tmp_path)
    board = gw.status_board()
    assert board["ok"] is True
    assert len(board["providers"]) >= 5
    assert "text" in board["fallback_chains"]
    assert "image" in board["fallback_chains"]
    stages = pipeline_stages()
    assert stages[0]["id"] == "interview"
    assert any(s["id"] == "provider_gateway" for s in stages)


def test_provider_connect_and_select(tmp_path: Path) -> None:
    gw = ProviderGateway(tmp_path)
    bad = gw.connect("openai_images", "short")
    assert bad["ok"] is False
    ok = gw.connect("openai_images", "sk-test-key-1234567890")
    assert ok["ok"] is True
    assert ok["connected"] is True
    picked = gw.select_provider(Modality.IMAGE)
    assert picked["ok"] is True
    assert picked["provider_id"] == "openai_images"


def test_backend_import_preflight_passes() -> None:
    pf = run_backend_import_preflight()
    assert pf.ok is True, f"{pf.message}\n{pf.detail}"
