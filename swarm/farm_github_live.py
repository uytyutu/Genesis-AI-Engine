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
    """Ensure authenticated user has a fork of owner/repo. Creates if missing.

    Parent must be exactly owner/repo — a same-named non-fork (e.g. Genesis-AI-Engine)
    is never reused as a bounty fork.
    """
    login = github_login()
    if not login:
        return {
            "ok": False,
            "error": "github_user_required",
            "message_ru": "GITHUB_TOKEN не даёт доступ к /user — проверьте права токена.",
        }
    want = f"{owner}/{repo}".lower()
    expected_fork = f"{login}/{repo}"
    existing = _api("GET", f"https://api.github.com/repos/{login}/{repo}")
    if existing.get("ok"):
        data = existing.get("data") or {}
        parent = data.get("parent") or {}
        parent_full = str(parent.get("full_name") or "").lower()
        # Accept ONLY when parent is the bounty source (not "any fork").
        if bool(data.get("fork")) and parent_full == want:
            return {
                "ok": True,
                "fork_owner": login,
                "fork_full": str(data.get("full_name") or expected_fork),
                "fork_parent": parent_full,
                "created": False,
            }
        # Same-name non-fork or fork of something else — cannot safely reuse
        return {
            "ok": False,
            "error": "fork_name_collision",
            "message_ru": (
                f"У {login} уже есть репозиторий {login}/{repo}, но это не fork "
                f"{owner}/{repo}. Переименуйте его или удалите, затем Submit снова."
            ),
            "existing_fork": bool(data.get("fork")),
            "existing_parent": parent_full or None,
            "expected_parent": want,
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
    fork_full = str(data.get("full_name") or expected_fork)
    # Forks are async — poll until ready and parent is visible
    parent_full = ""
    for _ in range(12):
        probe = _api("GET", f"https://api.github.com/repos/{fork_full}")
        if probe.get("ok"):
            pdata = probe.get("data") or {}
            parent_full = str((pdata.get("parent") or {}).get("full_name") or "").lower()
            if parent_full == want or pdata.get("fork"):
                break
        time.sleep(1.5)
    if parent_full and parent_full != want:
        return {
            "ok": False,
            "error": "fork_parent_mismatch",
            "message_ru": (
                f"Fork {fork_full} создан, но parent={parent_full}, "
                f"ожидался {want}."
            ),
            "fork_full": fork_full,
            "fork_parent": parent_full,
        }
    return {
        "ok": True,
        "fork_owner": login,
        "fork_full": fork_full,
        "fork_parent": parent_full or want,
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


def push_branch(
    src: Path,
    branch: str,
    *,
    source_owner: str,
    source_repo: str,
) -> dict[str, Any]:
    """Push branch for a bounty using task.repository as SSOT (never dirty origin)."""
    from swarm.farm_execution_engine import (
        normalize_repo_slug,
        workspace_matches_repository,
    )

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

    source_owner = (source_owner or "").strip()
    source_repo = (source_repo or "").strip().removesuffix(".git")
    if not source_owner or not source_repo:
        return {
            "ok": False,
            "error": "missing_repository",
            "message_ru": "task.repository отсутствует — push остановлен.",
        }

    source_slug = f"{source_owner}/{source_repo}".lower()
    identity = workspace_matches_repository(src, source_slug)
    if not identity.get("ok"):
        return {
            "ok": False,
            "error": identity.get("error") or "WORKSPACE_REPOSITORY_MISMATCH",
            "message_ru": (
                f"Workspace origin={identity.get('actual')} ≠ task.repository="
                f"{source_slug}. Push остановлен (Genesis не станет fork target)."
            ),
            "expected": identity.get("expected"),
            "actual": identity.get("actual"),
        }

    # Prefer direct push only when token can write the BOUNTY source repo
    if repo_can_push(source_owner, source_repo):
        direct = _push_to_remote(
            src,
            branch,
            remote_owner=source_owner,
            remote_repo=source_repo,
            remote_name="origin",
        )
        if direct.get("ok"):
            direct["head"] = branch
            direct["upstream"] = source_slug
            return direct

    # Bounty repos are almost never writable — fork then push
    fork = ensure_user_fork(source_owner, source_repo)
    if not fork.get("ok"):
        return fork
    fork_owner = str(fork.get("fork_owner") or "")
    fork_full = str(fork.get("fork_full") or f"{fork_owner}/{source_repo}").lower()
    expected_fork = f"{fork_owner}/{source_repo}".lower()
    if fork_full != expected_fork:
        return {
            "ok": False,
            "error": "fork_target_mismatch",
            "message_ru": (
                f"Ожидался fork {expected_fork}, получен {fork_full}. Push остановлен."
            ),
            "expected_fork": expected_fork,
            "fork_full": fork_full,
        }
    # Hard stop: never push bounty work into Virtus monorepo by accident
    if (
        normalize_repo_slug(fork_full) == "uytyutu/genesis-ai-engine"
        and source_slug != "uytyutu/genesis-ai-engine"
    ):
        return {
            "ok": False,
            "error": "forbidden_push_target",
            "message_ru": (
                "Push в uytyutu/Genesis-AI-Engine запрещён для чужого bounty. "
                "Ожидался fork source_repo."
            ),
        }
    parent = str(fork.get("fork_parent") or "").lower()
    if parent and parent != source_slug:
        return {
            "ok": False,
            "error": "fork_parent_mismatch",
            "message_ru": (
                f"Fork parent={parent}, ожидался {source_slug}. Push остановлен."
            ),
        }

    pushed = _push_to_remote(
        src,
        branch,
        remote_owner=fork_owner,
        remote_repo=source_repo,
        remote_name="origin",
    )
    if not pushed.get("ok"):
        return pushed
    pushed["head"] = f"{fork_owner}:{branch}"
    pushed["fork"] = fork
    pushed["upstream"] = source_slug
    pushed["expected_fork"] = expected_fork
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
        return {
            "ok": False,
            "error": "github_token_required",
            "comment_status": "TOKEN_MISSING",
        }
    res = _api(
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
        {"body": body},
    )
    if not res.get("ok"):
        status = int(res.get("status") or 0)
        comment_status = (
            "PERMISSION_DENIED"
            if status in (401, 403)
            else str(res.get("error") or "comment_failed")
        )
        return {
            "ok": False,
            "error": res.get("error"),
            "detail": res.get("detail"),
            "comment_status": comment_status,
            "http_status": status,
        }
    data = res.get("data") or {}
    return {
        "ok": True,
        "comment_id": data.get("id"),
        "comment_url": data.get("html_url"),
        "comment_status": "POSTED",
    }


def detect_competing_prs(
    owner: str, repo: str, issue_number: str | int
) -> dict[str, Any]:
    """List open PRs that reference the bounty issue (do not mutate them)."""
    issue = str(issue_number or "").strip()
    res = _api(
        "GET",
        f"https://api.github.com/repos/{owner}/{repo}/pulls?state=open&per_page=30",
    )
    if not res.get("ok"):
        return {
            "ok": False,
            "competing_pr_detected": False,
            "error": res.get("error"),
        }
    hits: list[dict[str, Any]] = []
    needle = f"#{issue}" if issue else ""
    for pr in res.get("data") or []:
        if not isinstance(pr, dict):
            continue
        title = str(pr.get("title") or "")
        body = str(pr.get("body") or "")
        if needle and (needle in title or needle in body):
            hits.append(
                {
                    "number": pr.get("number"),
                    "url": pr.get("html_url"),
                    "title": title[:120],
                    "user": ((pr.get("user") or {}).get("login")),
                }
            )
    return {
        "ok": True,
        "competing_pr_detected": bool(hits),
        "competing_prs": hits,
        "count": len(hits),
    }


def live_submit_draft_pr(task: dict[str, Any], workspace: Path) -> dict[str, Any]:
    """Push branch + create Draft PR with /claim in body. Returns platform IDs.

    Fork source is ALWAYS task.repository — never git remote origin alone.
    """
    from swarm.farm_execution_engine import workspace_matches_repository

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

    identity = workspace_matches_repository(src, f"{owner}/{repo}")
    if not identity.get("ok"):
        return {
            "ok": False,
            "error": identity.get("error") or "WORKSPACE_REPOSITORY_MISMATCH",
            "message_ru": (
                f"Перед Submit origin={identity.get('actual')} ≠ "
                f"{owner}/{repo}. Нужен fresh clone bounty-репозитория."
            ),
            "expected": identity.get("expected"),
            "actual": identity.get("actual"),
        }

    competing = detect_competing_prs(owner, repo, str(task.get("issue_id") or ""))
    task["competing_pr_detected"] = bool(competing.get("competing_pr_detected"))
    task["competing_prs"] = competing.get("competing_prs") or []

    pr_body_path = Path(str(exec_info.get("workspace") or workspace)) / "PULL_REQUEST.md"
    if not pr_body_path.is_file():
        pr_body_path = workspace / "PULL_REQUEST.md"
    body = (
        pr_body_path.read_text(encoding="utf-8")
        if pr_body_path.is_file()
        else f"/claim #{task.get('issue_id')}\n"
    )
    title = f"fix: {str(task.get('title') or 'opire bounty')[:72]}"

    pushed = push_branch(
        src,
        branch,
        source_owner=owner,
        source_repo=repo,
    )
    if not pushed.get("ok"):
        return pushed

    # Fork flow returns head as "user:branch"; same-repo push uses bare branch
    head = str(pushed.get("head") or branch)
    expected_head_prefix = ""
    fork_meta = pushed.get("fork") or {}
    if fork_meta:
        expected_head_prefix = f"{fork_meta.get('fork_owner')}:"
        if expected_head_prefix and not head.startswith(expected_head_prefix):
            return {
                "ok": False,
                "error": "pr_head_mismatch",
                "message_ru": (
                    f"PR head={head} не соответствует fork "
                    f"{fork_meta.get('fork_full')}. Submit остановлен."
                ),
            }

    base_branch = detect_default_branch(owner, repo)
    created = create_draft_pr(
        owner=owner,
        repo=repo,
        head=head,
        title=title,
        body=body,
        base=base_branch,
    )
    if created.get("ok"):
        created["push"] = {
            "remote": pushed.get("remote"),
            "head": head,
            "fork": pushed.get("fork"),
            "upstream": pushed.get("upstream") or f"{owner}/{repo}",
            "expected_fork": pushed.get("expected_fork"),
        }
        created["base"] = f"{owner}:{base_branch}"
        created["competing_pr_detected"] = task.get("competing_pr_detected")
        created["competing_prs"] = task.get("competing_prs")
    return created
