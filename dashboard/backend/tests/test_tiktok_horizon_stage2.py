"""TikTok Horizon Stage 2 — official OAuth multi-account (no publish)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modules.tiktok_horizon import HorizonService, STAGE1_CAPABILITIES
from modules.tiktok_horizon.token_vault import seal_secret, unseal_secret
from modules.tiktok_horizon.visibility import (
    is_commercial_surface_forbidden,
    visibility_policy,
)


def _patch_features(tmp_path: Path, monkeypatch, *, enabled: bool = False):
    features = tmp_path / "features.json"
    features.write_text(
        json.dumps(
            {
                "tiktok_enabled": enabled,
                "media_engine_enabled": False,
                "tiktok_horizon": {
                    "visibility": "INTERNAL_OWNER",
                    "owner_internal_only": True,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "app.integration.feature_flags_service._FEATURES",
        features,
    )
    monkeypatch.setattr(
        "modules.tiktok_factory.gate._FEATURES_PATH",
        features,
    )
    return features


def test_visibility_internal_owner_blocks_commercial_surfaces(tmp_path: Path, monkeypatch):
    _patch_features(tmp_path, monkeypatch)
    policy = visibility_policy()
    assert policy["visibility"] == "INTERNAL_OWNER"
    assert policy["owner_internal_only"] is True
    assert "owner" in policy["allowed_roles"]
    assert "client" in policy["denied_roles"]
    for surface in ("products", "services", "site", "client", "order", "marketplace"):
        assert is_commercial_surface_forbidden(surface)


def test_token_vault_roundtrip(monkeypatch):
    monkeypatch.setenv("TIKTOK_TOKEN_SECRET", "test-horizon-secret-key")
    sealed = seal_secret("act.example_token_value")
    assert sealed.startswith("hz1.")
    assert "act.example" not in sealed
    assert unseal_secret(sealed) == "act.example_token_value"


def test_multi_account_oauth_upsert_and_disconnect(tmp_path: Path, monkeypatch):
    _patch_features(tmp_path, monkeypatch, enabled=False)
    monkeypatch.setenv("TIKTOK_TOKEN_SECRET", "test-horizon-secret-key")
    monkeypatch.setenv("TIKTOK_CLIENT_KEY", "ck_test")
    monkeypatch.setenv("TIKTOK_CLIENT_SECRET", "cs_test")

    svc = HorizonService(tmp_path / "mem")

    def fake_exchange(*, code: str, redirect_uri: str):
        return {
            "ok": True,
            "open_id": f"oid-{code}",
            "access_token": f"act-{code}",
            "refresh_token": f"rft-{code}",
            "expires_in": 3600,
            "refresh_expires_in": 86400,
            "scopes": ["user.info.basic"],
        }

    def fake_profile(*, access_token: str):
        suffix = access_token.replace("act-", "")
        return {
            "ok": True,
            "open_id": f"oid-{suffix}",
            "display_name": f"Name {suffix}",
            "username": f"user_{suffix}",
            "avatar_url": None,
        }

    monkeypatch.setattr(svc.oauth, "exchange_code", fake_exchange)
    monkeypatch.setattr(svc.oauth, "fetch_user_profile", fake_profile)
    monkeypatch.setattr(svc.oauth, "revoke", lambda **kwargs: {"ok": True})

    # Simulate two OAuth callbacks (multi-account)
    state1 = svc.oauth.create_state()
    a1 = svc.complete_oauth(
        code="acc1",
        state=state1,
        public_api_base="http://localhost:8000",
    )["account"]
    state2 = svc.oauth.create_state()
    a2 = svc.complete_oauth(
        code="acc2",
        state=state2,
        public_api_base="http://localhost:8000",
    )["account"]

    listed = svc.list_accounts()
    assert len(listed) == 2
    assert a1["status"] == "connected"
    assert a2["username"] == "user_acc2"
    # Public payload must never leak raw tokens
    raw_dump = json.dumps(listed)
    assert "act-acc" not in raw_dump
    assert "rft-acc" not in raw_dump
    assert a1["tokens"]["has_access_token"] is True

    # Reconnect same open_id upserts
    state3 = svc.oauth.create_state()
    a1b = svc.complete_oauth(
        code="acc1",
        state=state3,
        public_api_base="http://localhost:8000",
    )["account"]
    assert a1b["id"] == a1["id"]
    assert len(svc.list_accounts()) == 2

    disconnected = svc.disconnect_account(a1["id"])
    assert disconnected["status"] == "disconnected"
    assert disconnected["tokens"]["has_access_token"] is False

    dash = svc.dashboard()
    assert dash["stage"] == 2
    assert dash["capabilities"]["tiktok_oauth"] is True
    assert dash["capabilities"]["video_publish"] is False
    assert STAGE1_CAPABILITIES["auto_publish"] is False


def test_oauth_requires_credentials(tmp_path: Path, monkeypatch):
    _patch_features(tmp_path, monkeypatch)
    monkeypatch.delenv("TIKTOK_CLIENT_KEY", raising=False)
    monkeypatch.delenv("TIKTOK_CLIENT_SECRET", raising=False)
    svc = HorizonService(tmp_path / "mem")
    with pytest.raises(ValueError, match="tiktok_oauth_not_configured"):
        svc.begin_oauth(public_api_base="http://localhost:8000")


def test_sync_refreshes_profile(tmp_path: Path, monkeypatch):
    _patch_features(tmp_path, monkeypatch)
    monkeypatch.setenv("TIKTOK_TOKEN_SECRET", "test-horizon-secret-key")
    monkeypatch.setenv("TIKTOK_CLIENT_KEY", "ck")
    monkeypatch.setenv("TIKTOK_CLIENT_SECRET", "cs")
    svc = HorizonService(tmp_path / "mem")

    monkeypatch.setattr(
        svc.oauth,
        "exchange_code",
        lambda **kw: {
            "ok": True,
            "open_id": "oid-x",
            "access_token": "act-x",
            "refresh_token": "rft-x",
            "expires_in": 3600,
            "refresh_expires_in": 9999,
            "scopes": ["user.info.basic"],
        },
    )
    monkeypatch.setattr(
        svc.oauth,
        "fetch_user_profile",
        lambda **kw: {
            "ok": True,
            "open_id": "oid-x",
            "display_name": "Synced",
            "username": "synced_user",
            "avatar_url": None,
        },
    )
    monkeypatch.setattr(
        svc.oauth,
        "refresh_access_token",
        lambda **kw: {
            "ok": True,
            "open_id": "oid-x",
            "access_token": "act-new",
            "refresh_token": "rft-new",
            "expires_in": 3600,
            "refresh_expires_in": 9999,
            "scopes": ["user.info.basic"],
        },
    )
    state = svc.oauth.create_state()
    acc = svc.complete_oauth(
        code="x",
        state=state,
        public_api_base="http://localhost:8000",
    )["account"]
    synced = svc.sync_account(acc["id"])
    assert synced["username"] == "synced_user"
    assert synced["last_sync_at"]
