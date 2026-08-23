"""Apify owner status — credentials from env, no fake Actor runs."""

from __future__ import annotations

from app.integration.apify_service import (
    check_apify_connection,
    credentials_snapshot,
    owner_apify_panel,
)
from swarm.platform_registry import list_platforms, platform_status


def test_credentials_aliases(monkeypatch):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    monkeypatch.setenv("APIFY_KEY", "apify_api_test_key_1234")
    monkeypatch.setenv("APIFY_ID", "userABCDEF12345")
    snap = credentials_snapshot()
    assert snap["configured"] is True
    assert snap["has_token"] is True
    assert snap["has_user_id"] is True
    assert snap["token_env"] == "APIFY_KEY"
    assert snap["user_id_env"] == "APIFY_ID"
    assert snap["token_masked"] == "…1234"


def test_platform_status_apify_aliases(monkeypatch):
    monkeypatch.delenv("APIFY_KEY", raising=False)
    monkeypatch.setenv("APIFY_TOKEN", "tok")
    status, label = platform_status("APIFY_KEY", "APIFY_KEY")
    assert status == "active"
    assert "ключ" in label.lower() or "Ключ" in label


def test_list_platforms_includes_apify(monkeypatch):
    monkeypatch.setenv("APIFY_KEY", "apify_api_xxxxx")
    platforms = list_platforms()
    apify = next(p for p in platforms if p["id"] == "apify")
    assert apify["connected"] is True
    assert apify.get("client_visible") is False
    assert apify["category"] == "actors"


def test_check_without_key(monkeypatch):
    monkeypatch.delenv("APIFY_KEY", raising=False)
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    out = check_apify_connection()
    assert out["connected"] is False
    assert out["configured"] is False
    assert out["product_line"]["client_visible"] is False
    assert out["product_line"]["actors"][0]["id"] == "vc_website_auditor"


def test_owner_panel_shape(monkeypatch):
    monkeypatch.delenv("APIFY_KEY", raising=False)
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    panel = owner_apify_panel()
    assert panel["owner_only"] is True
    assert panel["surface"] == "mission_control"
    assert "apify" in panel
