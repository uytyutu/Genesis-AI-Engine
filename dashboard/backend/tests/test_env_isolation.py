import os
import warnings
from pathlib import Path

import pytest

from app.config import SECRET_ENV_VARS, app_env, env_config_file, is_test_env
from app.env_loader import load_local_env, read_env_local_text, warn_env_local_access


def test_pytest_runs_in_test_profile():
    assert app_env() == "test"
    assert is_test_env()
    assert env_config_file() == "dashboard/backend/.env.test"


def test_real_env_local_secrets_not_loaded():
    """Session bootstrap must not leak dashboard/backend/.env.local into os.environ."""
    local = Path(__file__).resolve().parents[1] / ".env.local"
    if not local.is_file():
        pytest.skip(".env.local absent on this machine")
    raw = local.read_text(encoding="utf-8-sig")
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key not in SECRET_ENV_VARS or not value:
            continue
        assert os.getenv(key, "") != value, f"{key} leaked from .env.local into tests"


def test_load_local_env_skips_env_local_in_test():
    load_local_env()
    assert is_test_env()
    assert env_config_file().endswith(".env.test")


def test_warn_on_env_local_read_in_test():
    local = Path(__file__).resolve().parents[1] / ".env.local"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        read_env_local_text(local)
    assert any("env.local" in str(w.message).lower() for w in caught)


def test_warn_on_env_local_load_in_test():
    local = Path(__file__).resolve().parents[1] / ".env.local"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        warn_env_local_access(local, action="load")
    assert any("env.local" in str(w.message).lower() for w in caught)
