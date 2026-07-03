"""Tests for launcher path resolution."""

from pathlib import Path

import pytest

from launcher.deps import frontend_deps_ready
from launcher.paths import backend_dir, find_project_root, frontend_dir


def test_find_project_root_from_repo():
    root = find_project_root(Path(__file__).resolve().parent.parent)
    assert (root / "PROJECT_STATE.md").exists()
    assert (root / "dashboard").is_dir()


def test_backend_and_frontend_dirs():
    root = find_project_root()
    assert backend_dir(root).name == "backend"
    assert frontend_dir(root).name == "frontend"
    assert (backend_dir(root) / "app" / "main.py").exists()


def test_frontend_deps_ready_detects_next():
    root = find_project_root()
    fe = frontend_dir(root)
    ready = frontend_deps_ready(root)
    assert ready == (fe / "node_modules" / "next").is_dir()


def test_frontend_dir_has_package_json():
    root = find_project_root()
    fe = frontend_dir(root)
    assert (fe / "package.json").is_file()


def test_validate_layout_ok():
    from launcher.paths import validate_layout

    ok, msg = validate_layout(find_project_root())
    assert ok
    assert "frontend" in msg.lower()


def test_is_genesis_root_requires_frontend_package():
    from launcher.paths import _is_genesis_root

    repo = find_project_root()
    assert _is_genesis_root(repo)


def test_frontend_build_marker():
    from launcher.deps import frontend_build_marker, frontend_build_ready

    root = find_project_root()
    marker = frontend_build_marker(root)
    assert marker.name == "routes-manifest.json"
    assert marker.parent.name == ".next"
    # On dev machines build may or may not exist — function must not crash
    frontend_build_ready(root)
