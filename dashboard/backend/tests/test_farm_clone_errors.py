"""Clone failure classification for Farm Execution Engine."""

from __future__ import annotations

from swarm.farm_execution_engine import (
    _authed_github_clone_url,
    classify_clone_error,
    git_no_credential_helper_args,
    noninteractive_git_env,
)


def test_classify_repo_not_found():
    err = classify_clone_error(
        "remote: Repository not found.\n"
        "fatal: repository 'https://github.com/aueangpanit/electron-template.git/' not found",
        repo_url="https://github.com/aueangpanit/electron-template.git",
    )
    assert err["code"] == "repo_not_found"
    assert "недоступен" in err["detail_ru"]
    assert "aueangpanit/electron-template" in err["detail_ru"]


def test_classify_auth_required():
    err = classify_clone_error("Authentication failed for https://github.com/x/y.git")
    assert err["code"] == "auth_required"


def test_authed_clone_url_hides_nothing_in_plain_builder():
    url = _authed_github_clone_url("https://github.com/owner/repo.git", "secret-token")
    assert url == "https://x-access-token:secret-token@github.com/owner/repo.git"
    assert _authed_github_clone_url("https://github.com/owner/repo.git", "") is None


def test_noninteractive_git_kills_gcm_ui():
    env = noninteractive_git_env({"GCM_INTERACTIVE": "auto", "GIT_TERMINAL_PROMPT": "1"})
    assert env["GCM_INTERACTIVE"] == "never"
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GH_PROMPT_DISABLED"] == "1"
    cmd = git_no_credential_helper_args(
        "git", "ls-remote", "--heads", "https://github.com/a/b.git"
    )
    assert cmd[:5] == ["git", "-c", "credential.helper=", "-c", "credential.helper="]
    assert "ls-remote" in cmd
