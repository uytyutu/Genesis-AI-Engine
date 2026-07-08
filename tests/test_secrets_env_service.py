"""Tests for local .env secrets writer."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.secrets_env_service import SecretsEnvService


def test_upsert_creates_and_updates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    svc = SecretsEnvService()
    env_path = tmp_path / "backend" / ".env"
    monkeypatch.setattr(svc, "preferred_env_path", lambda: env_path)

    svc.upsert("GENESIS_LLM_API_KEY", "sk-test-key-123")
    assert env_path.is_file()
    text = env_path.read_text(encoding="utf-8")
    assert "GENESIS_LLM_API_KEY=sk-test-key-123" in text
    assert "sk-test-key-123" not in str(svc.upsert.__doc__)

    svc.upsert("GENESIS_LLM_API_KEY", "sk-new-key-456")
    text2 = env_path.read_text(encoding="utf-8")
    assert text2.count("GENESIS_LLM_API_KEY=") == 1
    assert "sk-new-key-456" in text2
    assert "sk-test-key-123" not in text2


def test_rejects_invalid_key_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    svc = SecretsEnvService()
    monkeypatch.setattr(svc, "preferred_env_path", lambda: tmp_path / ".env")
    with pytest.raises(ValueError, match="Invalid environment"):
        svc.upsert("bad-key", "value")
