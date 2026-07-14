"""Pytest bootstrap — isolate tests from dashboard/backend/.env.local."""

from __future__ import annotations

import os

# Must run before test modules import app.* (pytest loads conftest first).
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("ENVIRONMENT", "test")

from app.env_loader import apply_test_env_defaults, clear_secret_env, load_local_env


def pytest_configure(config) -> None:
    clear_secret_env()
    apply_test_env_defaults()
    load_local_env()
