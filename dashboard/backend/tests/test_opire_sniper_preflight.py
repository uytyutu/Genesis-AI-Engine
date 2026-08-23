"""Opire Sniper v1 — repo preflight (mock HTTP, no live GitHub)."""

from __future__ import annotations

import json
from io import BytesIO
from urllib.error import HTTPError

from swarm.opire_issue_intel import (
    apply_sniper_to_candidate,
    parse_repo_full,
    probe_github_repo,
)


class _Resp:
    def __init__(self, payload: dict, status: int = 200):
        self.status = status
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_parse_repo_full():
    assert parse_repo_full("aueangpanit/electron-template") == (
        "aueangpanit",
        "electron-template",
    )
    assert parse_repo_full("owner/repo.git") == ("owner", "repo")
    assert parse_repo_full("") is None


def test_probe_404_unreachable(monkeypatch):
    def boom(req, timeout=10.0):  # noqa: ARG001
        raise HTTPError(
            req.full_url,
            404,
            "Not Found",
            hdrs=None,
            fp=BytesIO(b""),
        )

    monkeypatch.setattr("swarm.opire_issue_intel.urllib.request.urlopen", boom)
    out = probe_github_repo("aueangpanit", "electron-template")
    assert out["ok"] is False
    assert out["error_code"] == "repo_unreachable"
    assert out["repo_status"] == "unreachable"
    assert "404" in out["detail_ru"]


def test_probe_200_ok(monkeypatch):
    def ok(req, timeout=10.0):  # noqa: ARG001
        return _Resp({"full_name": "owner/repo", "private": False})

    monkeypatch.setattr("swarm.opire_issue_intel.urllib.request.urlopen", ok)
    out = probe_github_repo("owner", "repo")
    assert out["ok"] is True
    assert out["error_code"] is None
    assert out["repo_status"] == "ok"


def test_probe_403_rate_limit_falls_back_to_git(monkeypatch):
    def boom(req, timeout=10.0):  # noqa: ARG001
        err = HTTPError(
            req.full_url,
            403,
            "rate limit",
            hdrs={"X-RateLimit-Remaining": "0"},
            fp=BytesIO(b'{"message":"API rate limit exceeded"}'),
        )
        raise err

    monkeypatch.setattr("swarm.opire_issue_intel.urllib.request.urlopen", boom)
    monkeypatch.setattr("swarm.opire_issue_intel._github_token", lambda: "")
    monkeypatch.setattr(
        "swarm.opire_issue_intel._git_ls_remote_probe",
        lambda owner, repo, timeout=20.0: {"ok": True, "error_code": None},
    )
    out = probe_github_repo("keycloak", "keycloak")
    assert out["ok"] is True
    assert out["repo_status"] == "ok"
    assert out.get("verified_via") == "git_ls_remote"


def test_apply_sniper_rate_limit_ok_clears_stale_auth(monkeypatch):
    def boom(req, timeout=10.0):  # noqa: ARG001
        raise HTTPError(
            req.full_url,
            403,
            "Forbidden",
            hdrs={"X-RateLimit-Remaining": "0"},
            fp=BytesIO(b"API rate limit exceeded"),
        )

    monkeypatch.setattr("swarm.opire_issue_intel.urllib.request.urlopen", boom)
    monkeypatch.setattr("swarm.opire_issue_intel._github_token", lambda: "")
    monkeypatch.setattr(
        "swarm.opire_issue_intel._git_ls_remote_probe",
        lambda *a, **k: {"ok": True, "error_code": None},
    )
    row = apply_sniper_to_candidate(
        {
            "id": "opire:kc",
            "repository": "keycloak/keycloak",
            "recommendation": "SKIP",
            "blockers": ["repo_auth_required"],
        }
    )
    assert row["repo_status"] == "ok"
    assert row["recommendation"] == "TAKE"
    assert "repo_auth_required" not in (row.get("blockers") or [])


def test_probe_403_with_token_still_auth_required(monkeypatch):
    def boom(req, timeout=10.0):  # noqa: ARG001
        raise HTTPError(
            req.full_url,
            403,
            "Forbidden",
            hdrs={},
            fp=BytesIO(b'{"message":"Resource not accessible"}'),
        )

    monkeypatch.setattr("swarm.opire_issue_intel.urllib.request.urlopen", boom)
    monkeypatch.setattr("swarm.opire_issue_intel._github_token", lambda: "fake-token")
    out = probe_github_repo("owner", "private")
    assert out["error_code"] == "repo_auth_required"
    assert out["repo_status"] == "auth_required"


def test_probe_network_unknown_no_hard_code_as_unreachable(monkeypatch):
    def boom(req, timeout=10.0):  # noqa: ARG001
        raise TimeoutError("network down")

    monkeypatch.setattr("swarm.opire_issue_intel.urllib.request.urlopen", boom)
    out = probe_github_repo("owner", "repo")
    assert out["error_code"] == "repo_probe_network"
    assert out["repo_status"] == "unknown"


def test_apply_sniper_skip_on_404(monkeypatch):
    def boom(req, timeout=10.0):  # noqa: ARG001
        raise HTTPError(req.full_url, 404, "Not Found", hdrs=None, fp=BytesIO(b""))

    monkeypatch.setattr("swarm.opire_issue_intel.urllib.request.urlopen", boom)
    monkeypatch.setattr(
        "swarm.opire_issue_intel._git_ls_remote_probe",
        lambda *a, **k: {"ok": False, "error_code": "repo_unreachable", "detail": "not found"},
    )
    row = apply_sniper_to_candidate(
        {
            "id": "opire:1",
            "repository": "aueangpanit/electron-template",
            "recommendation": "TAKE",
            "blockers": [],
        }
    )
    assert row["recommendation"] == "SKIP"
    assert "repo_unreachable" in row["blockers"]
    assert row["repo_status"] == "unreachable"


def test_apply_sniper_keeps_take_on_ok(monkeypatch):
    def ok(req, timeout=10.0):  # noqa: ARG001
        return _Resp({"full_name": "owner/repo", "private": False})

    monkeypatch.setattr("swarm.opire_issue_intel.urllib.request.urlopen", ok)
    row = apply_sniper_to_candidate(
        {
            "id": "opire:2",
            "repository": "owner/repo",
            "recommendation": "TAKE",
            "blockers": [],
        }
    )
    assert row["recommendation"] == "TAKE"
    assert row["repo_status"] == "ok"
    assert "repo_unreachable" not in (row.get("blockers") or [])


def test_apply_sniper_network_does_not_force_skip(monkeypatch):
    def boom(req, timeout=10.0):  # noqa: ARG001
        raise OSError("dns")

    monkeypatch.setattr("swarm.opire_issue_intel.urllib.request.urlopen", boom)
    monkeypatch.setattr(
        "swarm.opire_issue_intel._git_ls_remote_probe",
        lambda *a, **k: {"ok": False, "error_code": "repo_probe_network", "detail": "dns"},
    )
    row = apply_sniper_to_candidate(
        {
            "id": "opire:3",
            "repository": "owner/repo",
            "recommendation": "TAKE",
            "blockers": [],
        }
    )
    assert row["recommendation"] == "TAKE"
    assert row["repo_status"] == "unknown"


def test_scan_excludes_already_active_ids(monkeypatch):
    from swarm import opire_farm

    fake_candidates = [
        {
            "id": "opire:old",
            "native_id": "old",
            "repository": "owner/old",
            "url": "https://github.com/owner/old/issues/1",
            "recommendation": "TAKE",
            "blockers": [],
            "overall_confidence_pct": 90,
            "reward_usd": 50,
        },
        {
            "id": "opire:new",
            "native_id": "new",
            "repository": "owner/new",
            "url": "https://github.com/owner/new/issues/2",
            "recommendation": "TAKE",
            "blockers": [],
            "overall_confidence_pct": 88,
            "reward_usd": 80,
        },
    ]

    class FakeMgr:
        def scan(self, **kwargs):  # noqa: ARG002
            return {
                "ok": True,
                "candidates": list(fake_candidates),
                "scanned": 2,
                "filtered_out": 0,
                "threshold": 72,
                "catalog": [],
            }

    monkeypatch.setattr(
        "swarm.farm_connectors.manager.ConnectorManager",
        lambda *a, **k: FakeMgr(),
    )
    monkeypatch.setattr(
        "swarm.opire_issue_intel.apply_sniper_to_candidate",
        lambda cand, timeout=10.0: {**cand, "repo_status": "ok", "recommendation": "TAKE"},
    )

    out = opire_farm.scan_opire(
        limit=10,
        enrich_top=0,
        sniper_top=5,
        exclude_ids={"opire:old", "old"},
    )
    ids = [c["id"] for c in out.get("candidates") or []]
    assert "opire:old" not in ids
    assert "opire:new" in ids
    assert out.get("excluded_already_active") == 1


def test_scan_opire_sniper_backfills_past_dead_repo(monkeypatch):
    from swarm import opire_farm

    fake_candidates = [
        {
            "id": "opire:dead",
            "repository": "aueangpanit/electron-template",
            "url": "https://github.com/aueangpanit/electron-template/issues/1",
            "recommendation": "TAKE",
            "blockers": [],
            "overall_confidence_pct": 90,
            "reward_usd": 100,
        },
        {
            "id": "opire:live",
            "repository": "owner/good-repo",
            "url": "https://github.com/owner/good-repo/issues/2",
            "recommendation": "TAKE",
            "blockers": [],
            "overall_confidence_pct": 88,
            "reward_usd": 80,
        },
    ]

    class FakeMgr:
        def scan(self, **kwargs):  # noqa: ARG002
            return {
                "ok": True,
                "candidates": list(fake_candidates),
                "scanned": 2,
                "filtered_out": 0,
                "threshold": 72,
                "catalog": [],
            }

    def sniper(cand, timeout=10.0):  # noqa: ARG001
        row = dict(cand)
        if "electron-template" in str(row.get("repository") or ""):
            row["recommendation"] = "SKIP"
            row["blockers"] = ["repo_unreachable"]
            row["repo_status"] = "unreachable"
        else:
            row["recommendation"] = "TAKE"
            row["repo_status"] = "ok"
            row["blockers"] = []
        return row

    monkeypatch.setattr(
        "swarm.farm_connectors.manager.ConnectorManager",
        lambda *a, **k: FakeMgr(),
    )
    monkeypatch.setattr(
        "swarm.opire_issue_intel.apply_sniper_to_candidate",
        sniper,
    )

    out = opire_farm.scan_opire(limit=10, enrich_top=0, sniper_top=5)
    ids = [c["id"] for c in out.get("candidates") or []]
    assert "opire:dead" not in ids
    assert "opire:live" in ids
    assert out.get("sniper_skipped", 0) >= 1
