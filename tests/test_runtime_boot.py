from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from launcher import runtime_boot


def test_runtime_boot_already_ready(monkeypatch) -> None:
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: True)
    monkeypatch.setattr("launcher.processes.reconnect_managed", lambda managed, root=None: True)

    result = runtime_boot.run_runtime_boot(MagicMock(), Path("."))
    assert result.success is True
    assert result.ready is True
    assert any(p.name == "mission_control" and p.ok for p in result.phases)


def test_boot_report_written(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("launcher.paths.memory_dir", lambda root=None: tmp_path)

    result = runtime_boot.BootResult(
        success=False,
        ready=False,
        launch_ok=False,
        error="Frontend down",
        cause="Mission Control не запустился",
        phases=[runtime_boot.BootPhase("frontend", False, "HTTP 500")],
    )
    path = runtime_boot.write_boot_report(result, tmp_path)
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "Frontend down" in text
