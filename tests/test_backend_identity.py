"""Launcher backend runtime identity checks."""

from __future__ import annotations

from launcher.backend_identity import (
    VALID_RUNTIME_IDENTITIES,
    backend_runtime_compatible,
    git_commit_matches,
    process_age_acceptable,
)


def _status(**overrides):
    base = {
        "runtime_identity": "genesis-backend-v1",
        "git_commit": "abc1234",
        "uptime_sec": 120.0,
    }
    base.update(overrides)
    return base


def test_compatible_when_all_fields_match(monkeypatch):
    monkeypatch.setattr("launcher.backend_identity.expected_git_commit", lambda root=None: "abc1234")
    ok, reason = backend_runtime_compatible(None, _status())
    assert ok
    assert reason == "ok"


def test_reject_missing_runtime_identity(monkeypatch):
    monkeypatch.setattr("launcher.backend_identity.expected_git_commit", lambda root=None: "abc1234")
    ok, reason = backend_runtime_compatible(None, _status(runtime_identity=None))
    assert not ok
    assert "runtime_identity" in reason


def test_reject_git_mismatch(monkeypatch):
    monkeypatch.setattr("launcher.backend_identity.expected_git_commit", lambda root=None: "deadbeef")
    ok, reason = backend_runtime_compatible(None, _status())
    assert not ok
    assert "git_commit mismatch" in reason


def test_reject_old_process(monkeypatch):
    monkeypatch.setattr("launcher.backend_identity.expected_git_commit", lambda root=None: "abc1234")
    ok, reason = backend_runtime_compatible(None, _status(uptime_sec=90000.0))
    assert not ok
    assert "too old" in reason


def test_unknown_commits_match_each_other(monkeypatch):
    monkeypatch.setattr("launcher.backend_identity.expected_git_commit", lambda root=None: "unknown")
    assert git_commit_matches(None, _status(git_commit="unknown"))


def test_runtime_identity_constant():
    assert "genesis-backend-v1" in VALID_RUNTIME_IDENTITIES
