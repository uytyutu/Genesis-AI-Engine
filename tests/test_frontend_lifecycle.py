"""Frontend lifecycle — safe .next, listener PID, alive vs HTTP 200."""

from launcher.processes import ManagedProcesses, sync_state_from_ports


def test_clear_frontend_build_stops_listeners_before_delete(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(
        "launcher.process_cleanup.stop_frontend_listeners",
        lambda root, managed=None: calls.append("stop"),
    )
    monkeypatch.setattr(
        "launcher.deps.frontend_dir",
        lambda root=None: __import__("pathlib").Path("/fake/fe"),
    )
    monkeypatch.setattr(
        "launcher.deps.shutil.rmtree",
        lambda path, **kw: calls.append("rm"),
    )
    monkeypatch.setattr(
        "launcher.deps.Path.exists",
        lambda self: self.as_posix().endswith(".next"),
    )

    from launcher.deps import clear_frontend_build

    clear_frontend_build()
    assert calls == ["stop", "rm"]


def test_sync_state_from_ports_prefers_listeners(monkeypatch):
    managed = ManagedProcesses()
    saved: dict = {}

    monkeypatch.setattr(
        "launcher.process_cleanup.backend_listener_pids",
        lambda: [8001],
    )
    monkeypatch.setattr(
        "launcher.process_cleanup.frontend_listener_pids",
        lambda: [3001],
    )
    monkeypatch.setattr(
        "launcher.processes.sync_state",
        lambda be, fe, root=None: saved.update({"be": be, "fe": fe}),
    )

    sync_state_from_ports(managed, root=None)
    assert saved == {"be": 8001, "fe": 3001}


def test_wait_until_ready_restarts_alive_not_ready(monkeypatch):
    """Port listening + not HTTP 200 → repair_frontend, not 45s blind wait."""
    managed = ManagedProcesses()
    state = {"listening": True, "http200": False, "repaired": False}

    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: state["http200"])
    monkeypatch.setattr("launcher.health.probe_vector_chat_ready", lambda *a, **k: state["http200"])
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda: state["http200"])
    monkeypatch.setattr(
        "launcher.health.frontend_port_listening",
        lambda: state["listening"],
    )
    from launcher.startup_stages import StageAssessment

    monkeypatch.setattr(
        "launcher.startup_stages.assess_startup",
        lambda root=None: StageAssessment(
            stage="frontend_down",
            message="down",
            backend_up=True,
            frontend_up=False,
        ),
    )
    monkeypatch.setattr("launcher.startup_stages.failure_for_stage", lambda *a, **k: "fail")
    monkeypatch.setattr("launcher.processes.sync_state_from_ports", lambda *a, **k: None)
    monkeypatch.setattr("launcher.processes.append_log", lambda msg: None)
    monkeypatch.setattr("launcher.processes.time.sleep", lambda s: None)

    t0 = 1000.0

    def repair(m, root=None):
        state["repaired"] = True
        state["http200"] = True
        return True, "restarted"

    monkeypatch.setattr("launcher.frontend_repair.repair_frontend", repair)

    import launcher.processes as proc_mod

    tick = {"n": 0}

    def fake_time():
        tick["n"] += 1
        return t0 + min(tick["n"] * 0.5, 12.0)

    monkeypatch.setattr("launcher.processes.time.time", fake_time)

    ready, err = proc_mod.wait_until_ready(
        timeout=10,
        managed=managed,
        auto_repair=True,
    )
    assert state["repaired"] is True
    assert ready is True
    assert err == ""
