"""Tests for Mission Control startup diagnosis."""

from __future__ import annotations

from launcher.frontend_repair import (
    diagnose_frontend,
    frontend_log_indicates_error,
    frontend_log_indicates_ready,
)
from launcher.paths import find_project_root


def test_frontend_log_ready_marker(monkeypatch):
    monkeypatch.setattr(
        "launcher.frontend_repair.read_frontend_log_tail",
        lambda root, chars=8000: "▲ Next.js\n- Local:        http://localhost:3000\n✓ Ready in 4.2s\n",
    )
    assert frontend_log_indicates_ready(None)
    assert not frontend_log_indicates_error(None)


def test_frontend_log_build_error(monkeypatch):
    monkeypatch.setattr(
        "launcher.frontend_repair.read_frontend_log_tail",
        lambda root, chars=8000: "Failed to compile\nSyntax error: unexpected token\n",
    )
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: False)
    monkeypatch.setattr("launcher.deps.find_node", lambda: "node")
    monkeypatch.setattr("launcher.deps.find_npm", lambda: "npm")
    monkeypatch.setattr("launcher.deps.frontend_deps_ready", lambda root=None: True)
    assert frontend_log_indicates_error(None)
    diag = diagnose_frontend(None, frontend_exited=True)
    assert diag.can_auto_fix
    assert "Frontend" in diag.message


def test_diagnose_missing_node(monkeypatch):
    monkeypatch.setattr("launcher.deps.find_node", lambda: None)
    monkeypatch.setattr("launcher.deps.find_npm", lambda: None)
    diag = diagnose_frontend(None)
    assert diag.issue == "node_missing"
    assert not diag.can_auto_fix


def test_port_conflict_is_auto_fixable(monkeypatch):
    monkeypatch.setattr("launcher.deps.find_node", lambda: "node")
    monkeypatch.setattr("launcher.deps.find_npm", lambda: "npm")
    monkeypatch.setattr("launcher.deps.frontend_deps_ready", lambda root=None: True)
    monkeypatch.setattr(
        "launcher.frontend_repair.read_frontend_log_tail",
        lambda root, chars=8000: "Error: listen EADDRINUSE: address already in use :::3000\n",
    )
    monkeypatch.setattr(
        "launcher.frontend_repair.extract_frontend_error",
        lambda root: ("Порт 3000 уже занят", ["Error: listen EADDRINUSE: address already in use :::3000"]),
    )
    diag = diagnose_frontend(None, frontend_exited=True)
    assert diag.can_auto_fix
    assert "3000" in diag.message


def test_diagnose_missing_build(monkeypatch):
    monkeypatch.setattr("launcher.deps.find_node", lambda: "node")
    monkeypatch.setattr("launcher.deps.find_npm", lambda: "npm")
    monkeypatch.setattr("launcher.frontend_repair.frontend_build_ready", lambda root=None: False)
    monkeypatch.setattr("launcher.frontend_repair.frontend_deps_ready", lambda root=None: True)
    monkeypatch.setattr(
        "launcher.frontend_repair.read_frontend_log_tail",
        lambda root, chars=8000: "ENOENT routes-manifest.json\n",
    )
    root = find_project_root()
    diag = diagnose_frontend(root, frontend_exited=True)
    assert diag.issue == "missing_build"
    assert diag.can_auto_fix


def _fake_genesis_root(tmp_path) -> Path:
    (tmp_path / "PROJECT_STATE.md").write_text("# test", encoding="utf-8")
    (tmp_path / "dashboard").mkdir()
    (tmp_path / "kernel").mkdir()
    fe = tmp_path / "dashboard" / "frontend"
    fe.mkdir(parents=True)
    (fe / "package.json").write_text("{}", encoding="utf-8")
    be = tmp_path / "dashboard" / "backend" / "app"
    be.mkdir(parents=True)
    (be / "main.py").write_text("# test", encoding="utf-8")
    return tmp_path


def test_diagnose_stale_build(monkeypatch, tmp_path):
    monkeypatch.setattr("launcher.deps.find_node", lambda: "node")
    monkeypatch.setattr("launcher.deps.find_npm", lambda: "npm")
    monkeypatch.setattr("launcher.deps.frontend_deps_ready", lambda root=None: True)
    root = _fake_genesis_root(tmp_path)
    nxt = root / "dashboard" / "frontend" / ".next"
    nxt.mkdir(parents=True)
    (nxt / "routes-manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "launcher.frontend_repair.read_frontend_log_tail",
        lambda root, chars=8000: "Error: Cannot find module './885.js'\n",
    )
    diag = diagnose_frontend(root, frontend_exited=True)
    assert diag.can_auto_fix
    assert diag.issue == "missing_build"


def test_frontend_build_integrity(tmp_path):
    from launcher.deps import frontend_build_integrity, frontend_build_ready

    root = _fake_genesis_root(tmp_path)
    nxt = root / "dashboard" / "frontend" / ".next"
    nxt.mkdir(parents=True)
    (nxt / "routes-manifest.json").write_text("{}", encoding="utf-8")
    assert frontend_build_ready(root)
    assert not frontend_build_integrity(root)
