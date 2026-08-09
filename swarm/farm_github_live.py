"""Live GitHub helpers for Farm Engine — official REST API only.

No manual CEO ID entry. Uses GITHUB_TOKEN / GH_TOKEN when present.
Creates Draft PR, reads merge state, posts /try comment when requested.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from swarm.farm_execution_engine import (
    _run,
    git_no_credential_helper_args,
    noninteractive_git_env,
    resolve_git_binary,
)


def _github_token() -> str:
    return (
        os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
        or os.environ.get("GENESIS_GITHUB_TOKEN")
        or ""
    ).strip()


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "VirtusCore-FarmEngine/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = _github_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _api(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=github_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8")
            body = json.loads(raw) if raw else {}
            return {"ok": True, "status": resp.status, "data": body, "error": None}
    except urllib.error.HTTPError as exc:
        err_body = ""
        try:
            err_body = exc.read().decode("utf-8")[:800]
        except Exception:
            pass
        return {
            "ok": False,
            "status": exc.code,
            "data": {},
            "error": f"http_{exc.code}",
            "detail": err_body,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "status": 0, "data": {}, "error": str(exc), "detail": ""}


def parse_repo(repo_full: str) -> tuple[str, str] | None:
    parts = (repo_full or "").strip().split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return parts[0], parts[1]


def detect_default_branch(owner: str, repo: str) -> str:
    res = _api("GET", f"https://api.github.com/repos/{owner}/{repo}")
    if res.get("ok"):
        return str((res.get("data") or {}).get("default_branch") or "main")
    return "main"


def github_login() -> str | None:
    res = _api("GET", "https://api.github.com/user")
    if not res.get("ok"):
        return None
    login = str((res.get("data") or {}).get("login") or "").strip()
    return login or None


def repo_can_push(owner: str, repo: str) -> bool:
    res = _api("GET", f"https://api.github.com/repos/{owner}/{repo}")
    if not res.get("ok"):
        return False
    perms = (res.get("data") or {}).get("permissions") or {}
    return bool(perms.get("push") or perms.get("admin") or perms.get("maintain"))


def ensure_user_fork(owner: str, repo: str) -> dict[str, Any]:
    """Ensure authenticated user has a fork of owner/repo. Creates if missing."""
    login = github_login()
    if not login:
        return {
            "ok": False,
            "error": "github_user_required",
            "message_ru": "GITHUB_TOKEN не даёт доступ к /user — проверьте права токена.",
        }
    existing = _api("GET", f"https://api.github.com/repos/{login}/{repo}")
    if existing.get("ok"):
        data = existing.get("data") or {}
        parent = data.get("parent") or {}
        parent_full = str(parent.get("full_name") or "")
        if parent_full.lower() == f"{owner}/{repo}".lower() or data.get("fork"):
            return {
                "ok": True,
                "fork_owner": login,
                "fork_full": str(data.get("full_name") or f"{login}/{repo}"),
                "created": False,
            }
        # Same-name non-fork — cannot safely reuse
        return {
            "ok": False,
            "error": "fork_name_collision",
            "message_ru": (
                f"У {login} уже есть репозиторий {login}/{repo}, но это не fork "
                f"{owner}/{repo}. Переименуйте его или удалите, затем Submit снова."
            ),
        }

    created = _api(
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/forks",
        {},
    )
    if not created.get("ok"):
        detail = str(created.get("detail") or "")
        scope_hint = ""
        if "Resource not accessible" in detail or created.get("status") == 403:
            scope_hint = (
                " Токену не хватает права создать fork: для classic PAT — scope "
                "`public_repo` (или `repo`); для fine-grained — Permission "
                "«Administration: Read and write» на создание репозиториев "
                "в аккаунте + доступ к публичным репозиториям. "
                "Обновите GITHUB_TOKEN в dashboard/backend/.env.local и "
                "перезапустите backend."
            )
        return {
            "ok": False,
            "error": created.get("error") or "fork_failed",
            "message_ru": (
                f"Не удалось создать fork {owner}/{repo}: "
                f"{detail[:220]}{scope_hint}"
            ),
            "detail": created.get("detail"),
        }
    data = created.get("data") or {}
    fork_full = str(data.get("full_name") or f"{login}/{repo}")
    # Forks are async — poll until ready (or accept 202 + short wait)
    for _ in range(12):
        probe = _api("GET", f"https://api.github.com/repos/{fork_full}")
        if probe.get("ok"):
            break
        time.sleep(1.5)
    return {
        "ok": True,
        "fork_owner": login,
        "fork_full": fork_full,
        "created": True,
    }


def _push_to_remote(
    src: Path,
    branch: str,
    *,
    remote_owner: str,
    remote_repo: str,
    remote_name: str = "origin",
) -> dict[str, Any]:
    """Push branch to github remote_owner/remote_repo (token auth, no token left in config)."""
    import base64

    git = resolve_git_binary() or "git"
    env = noninteractive_git_env()
    token = _github_token()
    if token:
        env["GIT_TERMINAL_PROMPT"] = "0"
    if not token:
        return {
            "ok": False,
            "error": "github_token_required",
            "message_ru": (
                "Для live push/PR нужен GITHUB_TOKEN (или GH_TOKEN) в окружении Genesis. "
                "ID вручную вводить не нужно — настройте токен один раз."
            ),
        }

    clean = f"https://github.com/{remote_owner}/{remote_repo}.git"
    have = _run(
        git_no_credential_helper_args(git, "remote", "get-url", remote_name),
        cwd=src,
        timeout=15,
        env=env,
    )
    if have.get("ok"):
        _run(
            git_no_credential_helper_args(git, "remote", "set-url", remote_name, clean),
            cwd=src,
            timeout=15,
            env=env,
        )
    else:
        _run(
            git_no_credential_helper_args(git, "remote", "add", remote_name, clean),
            cwd=src,
            timeout=15,
            env=env,
        )

    basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    push = _run(
        git_no_credential_helper_args(
            git,
            "-c",
            f"http.extraHeader=Authorization: Basic {basic}",
            "push",
            "-u",
            remote_name,
            branch,
        ),
        cwd=src,
        timeout=180,
        env=env,
    )
    if not push.get("ok"):
        authed = f"https://x-access-token:{token}@github.com/{remote_owner}/{remote_repo}.git"
        _run(
            git_no_credential_helper_args(git, "remote", "set-url", remote_name, authed),
            cwd=src,
            timeout=30,
            env=env,
        )
        try:
            push = _run(
                git_no_credential_helper_args(git, "push", "-u", remote_name, branch),
                cwd=src,
                timeout=180,
                env=env,
            )
        finally:
            _run(
                git_no_credential_helper_args(git, "remote", "set-url", remote_name, clean),
                cwd=src,
                timeout=30,
                env=env,
            )
    if not push.get("ok"):
        return {
            "ok": False,
            "error": "push_failed",
            "message_ru": (push.get("stderr") or push.get("stdout") or "git push failed")[
                :400
            ],
            "push": push,
            "remote": f"{remote_owner}/{remote_repo}",
        }
    return {
        "ok": True,
        "push": push,
        "remote": f"{remote_owner}/{remote_repo}",
        "head_owner": remote_owner,
    }


def push_branch(src: Path, branch: str) -> dict[str, Any]:
    """Push to origin; if no write access, fork under the token user and push there."""
    git = resolve_git_binary() or "git"
    env = noninteractive_git_env()
    token = _github_token()
    if token:
        env["GIT_TERMINAL_PROMPT"] = "0"
    if not token:
        return {
            "ok": False,
            "error": "github_token_required",
            "message_ru": (
                "Для live push/PR нужен GITHUB_TOKEN (или GH_TOKEN) в окружении Genesis. "
                "ID вручную вводить не нужно — настройте токен один раз."
            ),
        }

    remote = _run(
        git_no_credential_helper_args(git, "remote", "get-url", "origin"),
        cwd=src,
        timeout=30,
        env=env,
    )
    url = (remote.get("stdout") or "").strip()
    m = re.search(r"github\.com[/:]([^/]+)/([^/.]+)", url)
    if not m:
        return {"ok": False, "error": "bad_remote", "remote": url}
    owner, repo = m.group(1), m.group(2).removesuffix(".git")

    # Prefer direct push when token has write access
    if repo_can_push(owner, repo):
        direct = _push_to_remote(
            src, branch, remote_owner=owner, remote_repo=repo, remote_name="origin"
        )
        if direct.get("ok"):
            direct["head"] = branch  # same-repo PR head
            return direct

    # Bounty repos are almost never writable — fork then push
    fork = ensure_user_fork(owner, repo)
    if not fork.get("ok"):
        return fork
    fork_owner = str(fork.get("fork_owner") or "")
    pushed = _push_to_remote(
        src,
        branch,
        remote_owner=fork_owner,
        remote_repo=repo,
        remote_name="origin",
    )
    if not pushed.get("ok"):
        return pushed
    pushed["head"] = f"{fork_owner}:{branch}"
    pushed["fork"] = fork
    pushed["upstream"] = f"{owner}/{repo}"
    return pushed


def create_draft_pr(
    *,
    owner: str,
    repo: str,
    head: str,
    title: str,
    body: str,
    base: str | None = None,
) -> dict[str, Any]:
    if not _github_token():
        return {
            "ok": False,
            "error": "github_token_required",
            "message_ru": (
                "GITHUB_TOKEN не задан — Farm не может создать PR через API. "
                "Добавьте токен в .env (один раз), без ручного ввода PR URL."
            ),
        }
    base_branch = base or detect_default_branch(owner, repo)
    res = _api(
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        {
            "title": title[:200],
            "head": head,
            "base": base_branch,
            "body": body,
            "draft": True,
        },
    )
    if not res.get("ok"):
        # Retry non-draft if drafts disabled
        if res.get("status") == 422:
            res2 = _api(
                "POST",
                f"https://api.github.com/repos/{owner}/{repo}/pulls",
                {
                    "title": title[:200],
                    "head": head,
                    "base": base_branch,
                    "body": body,
                    "draft": False,
                },
            )
            res = res2
    if not res.get("ok"):
        return {
            "ok": False,
            "error": res.get("error") or "pr_create_failed",
            "detail": res.get("detail"),
            "message_ru": (
                f"GitHub API не создал PR ({res.get('error')}). "
                f"{(res.get('detail') or '')[:300]}"
            ),
        }
    data = res.get("data") or {}
    return {
        "ok": True,
        "pr_number": data.get("number"),
        "pr_id": str(data.get("number") or ""),
        "pr_url": data.get("html_url"),
        "pr_node_id": data.get("node_id"),
        "draft": bool(data.get("draft")),
        "base": base_branch,
        "head": head,
    }


def get_pull(owner: str, repo: str, number: int | str) -> dict[str, Any]:
    res = _api("GET", f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}")
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error"), "detail": res.get("detail")}
    data = res.get("data") or {}
    merged = bool(data.get("merged"))
    return {
        "ok": True,
        "pr_number": data.get("number"),
        "pr_url": data.get("html_url"),
        "state": data.get("state"),
        "merged": merged,
        "merge_sha": data.get("merge_commit_sha") if merged else None,
        "draft": bool(data.get("draft")),
        "title": data.get("title"),
    }


def post_issue_comment(owner: str, repo: str, issue_number: str, body: str) -> dict[str, Any]:
    """Official Opire /try as a new issue comment (requires token)."""
    if not _github_token():
        return {"ok": False, "error": "github_token_required"}
    res = _api(
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
        {"body": body},
    )
    if not res.get("ok"):
        return {
            "ok": False,
            "error": res.get("error"),
            "detail": res.get("detail"),
        }
    data = res.get("data") or {}
    return {
        "ok": True,
        "comment_id": data.get("id"),
        "comment_url": data.get("html_url"),
    }


def live_submit_draft_pr(task: dict[str, Any], workspace: Path) -> dict[str, Any]:
    """Push branch + create Draft PR with /claim in body. Returns platform IDs."""
    repo_full = str(task.get("repository") or "")
    parsed = parse_repo(repo_full)
    if not parsed:
        return {"ok": False, "error": "missing_repository"}
    owner, repo = parsed
    exec_info = task.get("execution") or {}
    branch = str(exec_info.get("branch") or "")
    src = workspace / "src"
    if not src.is_dir():
        # workspace may be the src parent path stored as workspace
        ws = Path(str(exec_info.get("workspace") or workspace))
        src = ws / "src" if (ws / "src").is_dir() else ws
    if not branch:
        return {"ok": False, "error": "missing_branch", "message_ru": "Нет branch в execution."}
    if not src.is_dir():
        return {
            "ok": False,
            "error": "missing_workspace",
            "message_ru": f"Workspace не найден: {src}",
        }

    pr_body_path = Path(str(exec_info.get("workspace") or workspace)) / "PULL_REQUEST.md"
    if not pr_body_path.is_file():
        pr_body_path = workspace / "PULL_REQUEST.md"
    body = (
        pr_body_path.read_text(encoding="utf-8")
        if pr_body_path.is_file()
        else f"/claim #{task.get('issue_id')}\n"
    )
    title = f"fix: {str(task.get('title') or 'opire bounty')[:72]}"

    pushed = push_branch(src, branch)
    if not pushed.get("ok"):
        return pushed

    # Fork flow returns head as "user:branch"; same-repo push uses bare branch
    head = str(pushed.get("head") or branch)
    created = create_draft_pr(
        owner=owner,
        repo=repo,
        head=head,
        title=title,
        body=body,
    )
    if created.get("ok"):
        created["push"] = {
            "remote": pushed.get("remote"),
            "head": head,
            "fork": pushed.get("fork"),
            "upstream": pushed.get("upstream"),
        }
    return created
