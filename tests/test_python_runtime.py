"""Python 3.12 runtime selection and backend dependency checks."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import launcher.deps as deps
from launcher.python_runtime import (
    SUPPORTED_PYTHON_LABEL,
    PythonRuntimeInfo,
    parse_python_version_text,
    unsupported_python_message,
)


def test_parse_python_version_text():
    assert parse_python_version_text("Python 3.12.8") == (3, 12, 8)
    assert parse_python_version_text("Python 3.14.6") == (3, 14, 6)


def test_unsupported_python_message():
    detected = PythonRuntimeInfo(
        argv=["py"],
        version_text="Python 3.14.6",
        major=3,
        minor=14,
    )
    msg = unsupported_python_message(detected)
    assert SUPPORTED_PYTHON_LABEL in msg
    assert "3.14" in msg
    assert "пропущена" in msg.lower() or "пропущена" in msg


def test_install_skips_when_requirements_satisfied(monkeypatch, tmp_path):
    root = tmp_path
    be = root / "dashboard" / "backend"
    be.mkdir(parents=True)
    (be / "requirements.txt").write_text("fastapi==0.115.6\n", encoding="utf-8")
    (be / "app").mkdir()
    (be / "app" / "main.py").write_text("print('x')", encoding="utf-8")

    runtime = PythonRuntimeInfo(
        argv=["py", "-3.12"],
        version_text="Python 3.12.8",
        major=3,
        minor=12,
    )
    monkeypatch.setattr(deps, "resolve_backend_python", lambda: runtime)
    monkeypatch.setattr(deps, "backend_requirements_satisfied", lambda argv, root=None: (True, ""))
    pip = MagicMock()
    monkeypatch.setattr(deps.subprocess, "run", pip)

    ok, msg = deps.install_backend_deps(root)
    assert ok
    assert "уже установлены" in msg
    pip.assert_not_called()


def test_install_refuses_wrong_python(monkeypatch):
    monkeypatch.setattr(deps, "resolve_backend_python", lambda: None)
    monkeypatch.setattr(
        deps,
        "resolve_any_python",
        lambda: PythonRuntimeInfo(["py"], "Python 3.14.6", 3, 14),
    )
    pip = MagicMock()
    monkeypatch.setattr(deps.subprocess, "run", pip)

    ok, msg = deps.install_backend_deps()
    assert not ok
    assert SUPPORTED_PYTHON_LABEL in msg
    pip.assert_not_called()


def test_install_runs_on_force_even_when_satisfied(monkeypatch, tmp_path):
    root = tmp_path
    be = root / "dashboard" / "backend"
    be.mkdir(parents=True)
    (be / "requirements.txt").write_text("fastapi==0.115.6\n", encoding="utf-8")

    runtime = PythonRuntimeInfo(["py", "-3.12"], "Python 3.12.8", 3, 12)
    monkeypatch.setattr(deps, "resolve_backend_python", lambda: runtime)
    monkeypatch.setattr(deps, "backend_requirements_satisfied", lambda argv, root=None: (True, ""))
    monkeypatch.setattr(deps, "backend_dir", lambda root=None: be)
    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        return MagicMock(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(deps.subprocess, "run", fake_run)

    ok, msg = deps.install_backend_deps(root, force=True)
    assert ok
    assert calls
    assert "pip" in calls[0]
