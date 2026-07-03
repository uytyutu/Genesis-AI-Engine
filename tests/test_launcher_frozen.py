"""Frozen exe path resolution and helper safety."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from launcher import paths


def test_path_helpers_are_callable():
    for name in ("find_project_root", "log_dir", "memory_dir", "backend_dir", "frontend_dir"):
        helper = getattr(paths, name)
        assert callable(helper), f"{name} must stay a function, not {type(helper)}"


def test_find_project_root_from_dist_dir(monkeypatch: pytest.MonkeyPatch):
    repo = Path(__file__).resolve().parent.parent
    dist = repo / "dist"
    dist.mkdir(exist_ok=True)

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(dist / "Genesis.exe"))
    monkeypatch.chdir(repo)

    root = paths.find_project_root()
    assert root == repo


def test_find_project_root_from_cwd_when_exe_outside_repo(monkeypatch: pytest.MonkeyPatch):
    repo = Path(__file__).resolve().parent.parent
    outside = repo.parent

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(outside / "Genesis.exe"))
    monkeypatch.chdir(repo)

    root = paths.find_project_root()
    assert root == repo
