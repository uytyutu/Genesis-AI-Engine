"""Deployment Manager — OVH Production SSOT."""

from __future__ import annotations

from app.integration.deployment_manager import (
    DEFAULT_OVH_HOST,
    _manager_actions,
    _manager_explain,
    build_deployment_manager,
)


def test_dns_mismatch_explain():
    text = _manager_explain(
        sync_status="dns_mismatch",
        domain_host="virtuscore.com",
        domain_provider="aspnet_iis",
        dns={"ips": ["54.243.117.197", "13.223.25.84"]},
        ovh_commit=None,
        local="abc1234",
        ahead=None,
        domain_on_ovh=False,
        host=DEFAULT_OVH_HOST,
    )
    assert "не указывает на OVH" in text
    assert "телефон" in text.lower() or "старую" in text


def test_outdated_explain():
    text = _manager_explain(
        sync_status="outdated",
        domain_host="virtuscore.com",
        domain_provider="nginx_vps",
        dns={"ips": [DEFAULT_OVH_HOST]},
        ovh_commit="aaa1111",
        local="bbb2222",
        ahead=3,
        domain_on_ovh=True,
        host=DEFAULT_OVH_HOST,
    )
    assert "не обновлялся" in text
    assert "3" in text


def test_actions_prefer_dns_and_ovh():
    acts = _manager_actions(sync_status="dns_mismatch", ssh_configured=False, domain_on_ovh=False)
    ids = {a["id"] for a in acts}
    assert "update_dns_ovh" in ids
    assert "deploy_ovh" in ids
    assert "configure_ovh_ssh" in ids


def test_commit_chain_behind():
    from app.integration.deployment_manager import _build_commit_chain

    chain = _build_commit_chain(
        local="a1b2c3d",
        vercel={"commit": "a1b2c3d"},
        ovh_commit="98fd12a",
        domain={"commit": "98fd12a", "reachable": True, "host_hint": "nginx_vps"},
    )
    assert chain["summary_status"] == "production_behind"
    assert "OVH behind Local/Vercel" in chain["behind_reasons"]
    assert "a1b2c3" in chain["text"]
    assert "Production behind" in chain["text"]


def test_build_manager_shape(monkeypatch):
    monkeypatch.setenv("GENESIS_OVH_HOST", "137.74.173.134")
    monkeypatch.delenv("GENESIS_OVH_SSH", raising=False)
    monkeypatch.delenv("GENESIS_OVH_SSH_USER", raising=False)

    monkeypatch.setattr(
        "app.integration.deployment_manager.build_deployment_inspector",
        lambda: {
            "id": "deployment_inspector",
            "frontend": {"provider": "aspnet_iis", "ok": True},
            "legacy_card": {"local_commit": "deadbeef"},
        },
    )
    monkeypatch.setattr(
        "app.integration.deployment_manager.local_git_commit",
        lambda: "deadbeef",
    )
    monkeypatch.setattr(
        "app.integration.deployment_manager.local_git_dirty",
        lambda: False,
    )
    monkeypatch.setattr(
        "app.integration.deployment_manager._resolve_dns_hint",
        lambda h: {"ok": True, "hostname": h, "ips": ["54.243.117.197"]},
    )
    monkeypatch.setattr(
        "app.integration.deployment_manager._ovh_http_snapshot",
        lambda host: {
            "host": host,
            "ok": True,
            "git_commit": "unknown",
            "build_info_commit": None,
            "health": {"ok": True},
            "api_status": {"git_commit": "unknown"},
            "frontend_hint": "nginx_vps",
        },
    )
    monkeypatch.setattr(
        "app.integration.deployment_manager._domain_points_to_ovh",
        lambda dns, ovh: False,
    )
    monkeypatch.setattr(
        "app.integration.deployment_manager._tcp_open",
        lambda host, port=22, timeout=5.0: True,
    )
    monkeypatch.setattr(
        "app.integration.deployment_manager._vercel_commit_snapshot",
        lambda: {"commit": "deadbeef", "source": "mock", "ok": True, "url": "https://x.vercel.app"},
    )
    monkeypatch.setattr(
        "app.integration.deployment_manager._domain_commit_snapshot",
        lambda url: {
            "commit": None,
            "source": "domain_no_build_info",
            "ok": False,
            "reachable": True,
            "ssl_ok": True,
            "host_hint": "aspnet_iis",
        },
    )

    out = build_deployment_manager()
    assert out["id"] == "deployment_manager"
    assert out["policy"]["production"] == "ovh"
    assert out["policy"]["preview"] == "vercel"
    assert out["status"] == "dns_mismatch"
    assert out["vercel"]["not_production"] is True
    assert any(a["id"] == "update_dns_ovh" for a in out["actions"])
    assert out["commit_chain"]["rows"]
    assert out["production_health"]["items"]
    assert len(out["production_health"]["items"]) == 8
    assert out["production_health"]["ok"] is False
    assert "Publish" in out["policy"]["publish_pipeline"]
