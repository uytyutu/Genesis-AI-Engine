"""Launcher backend lifecycle checks — Git is not launch control."""

from __future__ import annotations

from launcher.backend_identity import (
    VALID_RUNTIME_IDENTITIES,
    backend_runtime_compatible,
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


def test_compatible_when_backend_responds():
    ok, reason = backend_runtime_compatible(None, _status())
    assert ok
    assert reason == "ok"


def test_git_mismatch_does_not_affect_launch():
    """Different git_commit vs repo HEAD must never block launch."""
    ok, reason = backend_runtime_compatible(
        None,
        _status(git_commit="deadbeef"),
    )
    assert ok
    assert reason == "ok"


def test_reject_missing_runtime_identity():
    ok, reason = backend_runtime_compatible(None, _status(runtime_identity=None))
    assert not ok
    assert "runtime_identity" in reason


def test_reject_old_process():
    ok, reason = backend_runtime_compatible(None, _status(uptime_sec=90000.0))
    assert not ok
    assert "too old" in reason


def test_runtime_identity_constant():
    assert "genesis-backend-v1" in VALID_RUNTIME_IDENTITIES


def test_process_age_acceptable():
    assert process_age_acceptable(_status(uptime_sec=100.0))
    assert not process_age_acceptable(_status(uptime_sec=90000.0))
