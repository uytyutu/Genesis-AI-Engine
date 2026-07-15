"""Launcher status truth — no false Backend/Frontend errors when HTTP 200."""

from __future__ import annotations

from launcher.health import ServiceHealth, check_services, owner_ready_live, overall_label


def test_check_services_running_when_both_probes_ok(monkeypatch):
    monkeypatch.setattr("launcher.health.port_open", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)

    from launcher.health import check_services_fast

    health = check_services_fast()
    assert health.overall == "running"
    assert health.backend
    assert health.frontend
    assert health.error_message == ""
    assert "Backend не отвечает" not in "\n".join(health.details)


def test_check_services_ignores_stale_frontend_exited(monkeypatch):
    monkeypatch.setattr("launcher.health.port_open", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)

    from launcher.health import check_services_fast

    health = check_services_fast(frontend_exited=True)
    assert health.overall == "running"
    assert "Frontend не отвечает" not in health.error_message


def test_slow_system_check_does_not_mark_backend_down(monkeypatch):
    monkeypatch.setattr("launcher.health.port_open", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health._get_json", lambda url, timeout=8: {"name": "Genesis"})
    monkeypatch.setattr("launcher.health._probe_url", lambda *a, **k: False)

    from launcher.health import check_services

    health = check_services(include_slow_checks=True)
    assert health.backend
    assert health.overall == "running"
    assert any("медленный" in line for line in health.details)


def test_overall_label_ready_text():
    text, color = overall_label("running")
    assert text == "✔ Virtus Core полностью готов"
    assert color == "#22c55e"


def test_repair_backend_skipped_when_live(monkeypatch):
    from launcher.processes import ManagedProcesses
    from launcher.backend_repair import repair_backend

    monkeypatch.setattr("launcher.health.owner_ready_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr(
        "launcher.backend_identity.fetch_backend_status",
        lambda timeout=8.0: {"runtime_identity": "genesis-backend-v1", "git_commit": "abc"},
    )
    monkeypatch.setattr(
        "launcher.backend_identity.backend_runtime_compatible",
        lambda root, status: (True, "ok"),
    )
    ok, msg = repair_backend(ManagedProcesses())
    assert ok
    assert "не нужен" in msg.lower() or "готов" in msg.lower()


def test_repair_staged_skipped_when_live(monkeypatch):
    from launcher.processes import ManagedProcesses
    from launcher.startup_stages import repair_staged

    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: True)
    ok, msg = repair_staged(ManagedProcesses())
    assert ok
    assert "готов" in msg.lower()


def test_twenty_sequential_status_checks_never_false_error(monkeypatch):
    """Simulate 20 launcher refresh cycles — must never show Backend-down when HTTP OK."""
    monkeypatch.setattr("launcher.health.port_open", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_vector_chat_ready", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health._get_json", lambda url, timeout=8: {"modules": []})
    monkeypatch.setattr("launcher.health._probe_url", lambda *a, **k: True)

    for _ in range(20):
        from launcher.health import check_services_fast

        health = check_services_fast(frontend_exited=True)
        assert health.overall == "running", health.error_message
        assert owner_ready_live()
        text, _ = overall_label(health.overall, health.error_message)
        assert "Backend не отвечает" not in text
        assert "Модуль не найден" not in text
