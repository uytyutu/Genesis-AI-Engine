"""Staged launcher startup — Backend before Frontend."""

from __future__ import annotations

from launcher.startup_stages import StageAssessment, assess_startup, repair_staged


def test_stage_backend_off_frontend_off(monkeypatch):
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: False)
    monkeypatch.setattr("launcher.startup_stages.probe_backend_live", lambda: False)
    monkeypatch.setattr("launcher.startup_stages.probe_frontend_live", lambda: False)
    monkeypatch.setattr(
        "launcher.backend_repair.diagnose_backend",
        lambda *a, **k: type("D", (), {"message": "test", "can_auto_fix": True, "log_excerpt": "err"})(),
    )
    monkeypatch.setattr("launcher.backend_repair.format_backend_failure", lambda d, r: "backend.log tail")

    a = assess_startup(None)
    assert a.stage == "backend_down"
    assert "Backend не запущен" in a.message
    assert "Frontend" not in a.message or "пропущен" not in a.message


def test_stage_backend_on_frontend_off(monkeypatch):
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: False)
    monkeypatch.setattr("launcher.startup_stages.probe_backend_live", lambda: True)
    monkeypatch.setattr("launcher.startup_stages.probe_frontend_live", lambda: False)
    monkeypatch.setattr(
        "launcher.frontend_repair.diagnose_frontend",
        lambda *a, **k: type("D", (), {"message": "fe down", "can_auto_fix": True})(),
    )
    monkeypatch.setattr("launcher.frontend_repair.format_failure_message", lambda d, r: "Frontend не отвечает")

    a = assess_startup(None)
    assert a.stage == "frontend_down"
    assert a.backend_up is True


def test_stage_all_ready(monkeypatch):
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: True)
    monkeypatch.setattr("launcher.startup_stages.probe_backend_live", lambda: True)
    monkeypatch.setattr("launcher.startup_stages.probe_frontend_live", lambda: True)

    a = assess_startup(None)
    assert a.stage == "ready"
    assert "готов" in a.message.lower()


def test_repair_staged_skips_frontend_when_backend_down(monkeypatch):
    calls: list[str] = []

    def be(*_a, **_k):
        calls.append("backend")
        return False, "backend fix"

    def fe(*_a, **_k):
        calls.append("frontend")
        return True, "should not run"

    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: False)
    monkeypatch.setattr("launcher.startup_stages.probe_backend_live", lambda: False)
    monkeypatch.setattr("launcher.startup_stages.probe_frontend_live", lambda: False)
    monkeypatch.setattr("launcher.backend_repair.repair_backend", be)
    monkeypatch.setattr("launcher.frontend_repair.repair_frontend", fe)
    monkeypatch.setattr(
        "launcher.backend_repair.diagnose_backend",
        lambda *a, **k: type("D", (), {"message": "x", "can_auto_fix": True, "log_excerpt": ""})(),
    )
    monkeypatch.setattr("launcher.backend_repair.format_backend_failure", lambda d, r: "log")

    class _M:
        backend = None
        frontend = None

    ok, msg = repair_staged(_M(), None)
    assert not ok
    assert calls == ["backend"]
    assert "frontend" not in calls


def test_repair_staged_ready_no_repairs(monkeypatch):
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: True)
    monkeypatch.setattr("launcher.startup_stages.probe_backend_live", lambda: True)
    monkeypatch.setattr("launcher.startup_stages.probe_frontend_live", lambda: True)

    class _M:
        backend = None
        frontend = None

    ok, msg = repair_staged(_M(), None)
    assert ok
    assert "готов" in msg.lower()
