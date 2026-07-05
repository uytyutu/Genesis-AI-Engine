from __future__ import annotations

import json
from pathlib import Path

from launcher import dogfooding


def test_today_summary_and_trend(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(dogfooding.paths, "memory_dir", lambda root=None: tmp_path)

    sid, t0 = dogfooding.begin_launch_session(tmp_path)
    dogfooding.record_launch_success(sid, t0, root=tmp_path, browser_sec=1.1)
    dogfooding.record_warning("test warning", root=tmp_path)

    summary = dogfooding.today_summary(tmp_path)
    assert summary["launch_attempts"] == 1
    assert summary["launch_successes"] == 1
    assert summary["warnings"] == 1
    assert summary["reliability_pct"] == 99.2

    trend = dogfooding.stability_trend(days=7, root=tmp_path)
    assert len(trend) == 7
    assert trend[-1][1] == 99.2


def test_reliability_budget(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(dogfooding.paths, "memory_dir", lambda root=None: tmp_path)

    sid, t0 = dogfooding.begin_launch_session(tmp_path)
    dogfooding.record_launch_failure(sid, t0, root=tmp_path, error="boom", critical=True)

    budget = dogfooding.reliability_budget(root=tmp_path)
    assert budget["critical_errors"] == 1
    assert budget["remaining"] == 1
    assert budget["exceeded"] is False
