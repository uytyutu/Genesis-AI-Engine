"""Launch Pipeline three-tier gate."""

from unittest.mock import patch

from launcher.launch_pipeline_state import (
    record_ceo_manual_verify,
    record_gui_cycles,
    record_programmatic_cycles,
)
from launcher.release_guardian import (
    READY_FOR_CEO_VERIFY,
    evaluate_launch_pipeline,
)


def test_launch_pipeline_ready_for_ceo_after_both_cycles(monkeypatch, tmp_path):
    monkeypatch.setattr("launcher.release_guardian._repo_root", lambda: tmp_path)
    monkeypatch.setattr("launcher.paths.find_project_root", lambda r=None: tmp_path)
    mem = tmp_path / "dashboard" / "backend" / "memory"
    mem.mkdir(parents=True)
    monkeypatch.setattr("launcher.paths.memory_dir", lambda r=None: mem)
    exe = tmp_path / "dist" / "Genesis.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"x")
    (tmp_path / "PROJECT_STATE.md").write_text("#", encoding="utf-8")
    (tmp_path / "dashboard" / "backend" / "app").mkdir(parents=True)
    (tmp_path / "dashboard" / "backend" / "app" / "main.py").write_text("#", encoding="utf-8")
    (tmp_path / "kernel").mkdir()

    record_programmatic_cycles(10, tmp_path)
    record_gui_cycles(10, tmp_path)

    with patch("launcher.release_guardian.compute_overall_health", return_value=(100, [])):
        monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
        monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)
        monkeypatch.setattr("launcher.health.owner_ready_live", lambda: True)
        v = evaluate_launch_pipeline(min_cycles=10)

    assert v.headline == "READY FOR CEO VERIFY"
    assert v.ship is False
    assert "READY FOR CEO VERIFY" in v.render()
    assert "CEO Desktop verify" in v.render()


def test_launch_pipeline_ships_after_ceo_confirm(monkeypatch, tmp_path):
    monkeypatch.setattr("launcher.release_guardian._repo_root", lambda: tmp_path)
    monkeypatch.setattr("launcher.paths.find_project_root", lambda r=None: tmp_path)
    mem = tmp_path / "dashboard" / "backend" / "memory"
    mem.mkdir(parents=True)
    monkeypatch.setattr("launcher.paths.memory_dir", lambda r=None: mem)
    (tmp_path / "dist" / "Genesis.exe").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "dist" / "Genesis.exe").write_bytes(b"x")
    record_programmatic_cycles(10, tmp_path)
    record_gui_cycles(10, tmp_path)
    record_ceo_manual_verify(tmp_path)

    with patch("launcher.release_guardian.compute_overall_health", return_value=(100, [])):
        monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
        monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)
        monkeypatch.setattr("launcher.health.owner_ready_live", lambda: True)
        v = evaluate_launch_pipeline(min_cycles=10)

    assert v.ship is True
    assert v.headline == "ДА"
