"""RC1 Health Center + Stability KPI helpers."""

from __future__ import annotations

from pathlib import Path

from launcher.health_center import (
    STABILITY_KPI,
    build_health_center_rows,
    kpi_warnings,
    last_crash_summary,
)


def test_last_crash_never(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "launcher.paths.log_dir", lambda root=None: tmp_path / "logs"
    )
    (tmp_path / "logs").mkdir()
    out = last_crash_summary(tmp_path)
    assert out["detail"] == "Never"
    assert out["mark"] == "🟢"


def test_last_crash_from_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "launcher.paths.log_dir", lambda root=None: tmp_path / "logs"
    )
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "launcher_crash.log").write_text(
        "[2026-08-08] recovery restart Frontend\n", encoding="utf-8"
    )
    out = last_crash_summary(tmp_path)
    assert "ago" in out["detail"] or "Restarted" in out["detail"] or "just" in out["detail"]


def test_health_rows_shape() -> None:
    rows = build_health_center_rows(
        backend=True,
        frontend=True,
        backend_ms=142.0,
        frontend_ms=91.0,
        vector_ready=True,
    )
    ids = {r["id"] for r in rows if "id" in r}
    assert {"backend", "frontend", "vector", "factory", "farm", "launcher"} <= ids


def test_kpi_warnings() -> None:
    warns = kpi_warnings({"startup_sec": 45.0, "dashboard_first_paint_sec": 1.0})
    assert any("Startup" in w for w in warns)
    assert not any("Dashboard" in w for w in warns)
    assert STABILITY_KPI["startup_sec"] == 20.0
