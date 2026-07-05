"""Release Guardian stability gate."""

from unittest.mock import patch

from launcher.release_guardian import (
    PRODUCT_NOT_READY,
    STABILITY_HEALTH_MIN,
    evaluate_stability,
)


def test_stability_blocks_when_frontend_down(monkeypatch):
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: False)
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: False)
    with patch("launcher.release_guardian.compute_overall_health", return_value=(82, ["Frontend not ready"])):
        v = evaluate_stability()
    assert v.headline == "НЕТ"
    assert v.overall_health == 82
    assert PRODUCT_NOT_READY in v.render()
    assert any("Frontend" in r for r in v.reasons)


def test_stability_passes_at_95(monkeypatch, tmp_path):
    exe = tmp_path / "dist" / "Genesis.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"x")
    monkeypatch.setattr("launcher.release_guardian._repo_root", lambda: tmp_path)
    monkeypatch.setattr("launcher.paths.find_project_root", lambda r=None: tmp_path)
    (tmp_path / "PROJECT_STATE.md").write_text("#", encoding="utf-8")
    (tmp_path / "dashboard" / "backend" / "app").mkdir(parents=True)
    (tmp_path / "dashboard" / "backend" / "app" / "main.py").write_text("#", encoding="utf-8")
    (tmp_path / "kernel").mkdir()
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: True)
    with patch("launcher.release_guardian.compute_overall_health", return_value=(96, [])):
        v = evaluate_stability()
    assert v.headline == "ДА"
    assert v.overall_health >= STABILITY_HEALTH_MIN
