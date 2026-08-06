"""Frontend deployment status for CEO Executive."""

from app.integration.frontend_deployment_status import (
    build_frontend_deployment_status,
    local_git_commit,
)


def test_local_commit_resolves():
    c = local_git_commit()
    assert c
    assert c != ""


def test_frontend_deployment_shape(monkeypatch):
    monkeypatch.setattr(
        "app.integration.frontend_deployment_status._http_json",
        lambda url, timeout=12.0: {
            "git_commit": "abc1234",
            "deploy_status": "SUCCESS",
        },
    )
    monkeypatch.setattr(
        "app.integration.frontend_deployment_status._http_meta_commit",
        lambda url, timeout=12.0: None,
    )
    monkeypatch.setattr(
        "app.integration.frontend_deployment_status._vercel_production_commit",
        lambda: None,
    )
    monkeypatch.setattr(
        "app.integration.frontend_deployment_status.local_git_commit",
        lambda short=True: "abc1234" if short else "abc1234ffff",
    )
    monkeypatch.setattr(
        "app.integration.frontend_deployment_status.local_git_dirty",
        lambda: False,
    )
    out = build_frontend_deployment_status()
    assert out["status"] == "in_sync"
    assert out["deploy"] == "SUCCESS"
    assert out["local_commit"] == "abc1234"
    assert out["production_commit"] == "abc1234"


def test_frontend_deployment_behind(monkeypatch):
    monkeypatch.setattr(
        "app.integration.frontend_deployment_status._http_json",
        lambda url, timeout=12.0: {"git_commit": "old9999"},
    )
    monkeypatch.setattr(
        "app.integration.frontend_deployment_status._http_meta_commit",
        lambda url, timeout=12.0: None,
    )
    monkeypatch.setattr(
        "app.integration.frontend_deployment_status._vercel_production_commit",
        lambda: None,
    )
    monkeypatch.setattr(
        "app.integration.frontend_deployment_status.local_git_commit",
        lambda short=True: "new1111" if short else "new1111ffff",
    )
    monkeypatch.setattr(
        "app.integration.frontend_deployment_status.local_git_dirty",
        lambda: False,
    )
    out = build_frontend_deployment_status()
    assert out["status"] == "behind"
    assert out["mark"] == "🔴"
    assert out["behind"] is True
