"""Live GitHub helpers for Farm Engine — official REST API only.

No manual CEO ID entry. Uses GITHUB_TOKEN / GH_TOKEN when present.
Creates Draft PR, reads merge state, posts /try comment when requested.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from swarm.farm_execution_engine import _run, resolve_git_binary


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


def push_branch(src: Path, branch: str) -> dict[str, Any]:
    git = resolve_git_binary() or "git"
    # Ensure upstream remote uses HTTPS (token via env GIT_ASKPASS / credential helper if set)
    env = os.environ.copy()
    token = _github_token()
    if token:
        # Prefer x-access-token for GitHub HTTPS push without interactive prompt
        env["GIT_TERMINAL_PROMPT"] = "0"
    push = _run(
        [git, "push", "-u", "origin", branch],
        cwd=src,
        timeout=180,
        env=env,
    )
    if push["ok"]:
        return {"ok": True, "push": push}
    # Retry rewriting origin to token URL (scoped to this push only)
    if not token:
        return {
            "ok": False,
            "error": "github_token_required",
            "message_ru": (
                "Для live push/PR нужен GITHUB_TOKEN (или GH_TOKEN) в окружении Genesis. "
                "ID вручную вводить не нужно — настройте токен один раз."
            ),
            "push": push,
        }
    remote = _run([git, "remote", "get-url", "origin"], cwd=src, timeout=30)
    url = (remote.get("stdout") or "").strip()
    m = re.search(r"github\.com[/:]([^/]+)/([^/.]+)", url)
    if not m:
        return {"ok": False, "error": "bad_remote", "push": push, "remote": url}
    owner, repo = m.group(1), m.group(2).removesuffix(".git")
    authed = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
    _run([git, "remote", "set-url", "origin", authed], cwd=src, timeout=30)
    try:
        push2 = _run([git, "push", "-u", "origin", branch], cwd=src, timeout=180, env=env)
    finally:
        # Restore clean remote URL (no token in config)
        clean = f"https://github.com/{owner}/{repo}.git"
        _run([git, "remote", "set-url", "origin", clean], cwd=src, timeout=30)
    if not push2["ok"]:
        return {
            "ok": False,
            "error": "push_failed",
            "message_ru": (push2.get("stderr") or push2.get("stdout") or "git push failed")[
                :400
            ],
            "push": push2,
        }
    return {"ok": True, "push": push2}


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

    created = create_draft_pr(
        owner=owner,
        repo=repo,
        head=branch,
        title=title,
        body=body,
    )
    return created
