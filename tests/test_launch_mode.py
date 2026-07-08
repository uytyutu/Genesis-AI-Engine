"""Launch Architecture v2 — mode labels and launch law."""

from __future__ import annotations

from launcher.backend_identity import backend_runtime_compatible
from launcher.launch_mode import (
    LAUNCH_MODE_DEVELOPMENT,
    LAUNCH_MODE_OWNER,
    launch_mode_hint,
    launch_mode_label,
    normalize_launch_mode,
)


def _status(**overrides):
    base = {
        "runtime_identity": "genesis-backend-v1",
        "git_commit": "abc1234",
        "uptime_sec": 120.0,
    }
    base.update(overrides)
    return base


def test_normalize_launch_mode_defaults_to_owner():
    assert normalize_launch_mode(None) == LAUNCH_MODE_OWNER
    assert normalize_launch_mode("") == LAUNCH_MODE_OWNER
    assert normalize_launch_mode("development") == LAUNCH_MODE_DEVELOPMENT


def test_mode_labels_russian():
    assert launch_mode_label(LAUNCH_MODE_OWNER) == "Пользователь"
    assert launch_mode_label(LAUNCH_MODE_DEVELOPMENT) == "Разработка"


def test_mode_hints_never_mention_git_control():
    owner_hint = launch_mode_hint(LAUNCH_MODE_OWNER)
    dev_hint = launch_mode_hint(LAUNCH_MODE_DEVELOPMENT)
    assert "Git" in owner_hint or "git" in owner_hint.lower()
    assert "коммит" in owner_hint.lower() or "Git" in dev_hint


def test_launch_never_uses_git_commit(monkeypatch):
    ok, reason = backend_runtime_compatible(None, _status(git_commit="stale"))
    assert ok
    assert reason == "ok"


def test_launch_requires_http_status():
    ok, reason = backend_runtime_compatible(None, None)
    assert not ok
