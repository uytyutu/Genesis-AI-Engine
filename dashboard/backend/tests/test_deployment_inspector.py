"""Deployment Inspector — Production map without memorizing hosts."""

from __future__ import annotations

from app.integration.deployment_inspector import (
    _actions,
    _classify_host,
    _explain,
    build_deployment_inspector,
)


def test_classify_vercel():
    assert _classify_host({"x-vercel-id": "fra1::abc"}, "") == "vercel"


def test_classify_aspnet():
    assert _classify_host({"x-powered-by": "ASP.NET", "cf-ray": "x"}, "") == "cloudflare_aspnet"


def test_explain_ahead():
    text = _explain(
        fe_hint="vercel",
        be_hint="railway",
        deploy={"status": "behind", "local_commit": "aaa", "production_commit": "bbb"},
        ahead=3,
        site="https://virtuscore.de",
        mismatch=True,
    )
    assert "3 коммит" in text


def test_explain_aspnet_domain():
    text = _explain(
        fe_hint="cloudflare_aspnet",
        be_hint="unknown",
        deploy={"status": "unknown"},
        ahead=None,
        site="https://virtuscore.com",
        mismatch=True,
    )
    assert "ASP.NET" in text or "телефон" in text


def test_actions_include_deploy_when_behind():
    acts = _actions(
        fe_hint="vercel",
        deploy={"status": "behind"},
        ahead=2,
        flags={"expected_host": "ovh"},
        mismatch=True,
    )
    ids = {a["id"] for a in acts}
    assert "deploy_ovh" in ids


def test_build_inspector_shape(monkeypatch):
    monkeypatch.setattr(
        "app.integration.deployment_inspector.build_frontend_deployment_status",
        lambda: {
            "id": "frontend_deployment",
            "local_commit": "abc1234",
            "production_commit": "abc1234",
            "status": "in_sync",
            "deploy": "SUCCESS",
            "production_url": "https://example.test",
        },
    )
    monkeypatch.setattr(
        "app.integration.deployment_inspector.production_site_url",
        lambda: "https://example.test",
    )
    monkeypatch.setattr(
        "app.integration.deployment_inspector.local_git_commit",
        lambda: "abc1234",
    )
    monkeypatch.setattr(
        "app.integration.deployment_inspector.local_git_dirty",
        lambda: False,
    )
    monkeypatch.setattr(
        "app.integration.deployment_inspector._probe_url",
        lambda url, **kw: {
            "url": url,
            "ok": True,
            "status_code": 200,
            "host_hint": "nginx_vps",
            "headers_sample": {},
            "error": None,
        },
    )
    monkeypatch.setattr(
        "app.integration.deployment_inspector._git_remote",
        lambda: {"url": "https://github.com/x/y.git", "branch": "main", "ok": True},
    )
    monkeypatch.setattr(
        "app.integration.deployment_inspector._resolve_dns_hint",
        lambda h: {"ok": True, "hostname": h, "ips": ["1.2.3.4"]},
    )
    monkeypatch.setattr(
        "app.integration.deployment_inspector._commits_ahead_of",
        lambda c: 0,
    )
    monkeypatch.setattr(
        "app.integration.deployment_inspector._provider_flags",
        lambda: {
            "vercel_api_configured": False,
            "railway_token_configured": False,
            "expected_host": "nginx_vps",
            "hetzner_hint": True,
        },
    )
    monkeypatch.setenv("NEXT_PUBLIC_API_URL", "https://api.example.test")

    out = build_deployment_inspector()
    assert out["id"] == "deployment_inspector"
    assert out["frontend"]["provider"] == "nginx_vps"
    assert out["production"]["points_to"] == "nginx_vps"
    assert out["explanation_ru"]
    assert isinstance(out["actions"], list)
    assert out["legacy_card"]["local_commit"] == "abc1234"
