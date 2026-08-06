"""Opire issue intelligence — read GitHub Issue body for Confidence + Planning.

Official sources only: api.opire.dev + api.github.com (public issue text).
Does not post /try or open PRs — CEO gates remain.

Opire Sniper v1: probe_github_repo — early filter for deleted/private repos.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

_ISSUE_RE = re.compile(r"github\.com/([^/]+)/([^/]+)/issues/(\d+)", re.I)
_REPO_RE = re.compile(r"^([^/\s]+)/([^/\s]+?)(?:\.git)?$", re.I)


def _github_token() -> str:
    try:
        from swarm.farm_env_bootstrap import ensure_farm_env

        ensure_farm_env()
    except Exception:  # noqa: BLE001
        pass
    return (
        os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
        or os.environ.get("GENESIS_GITHUB_TOKEN")
        or ""
    ).strip()


def _github_api_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "VirtusCore-FarmEngine/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = _github_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _http_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        return (exc.read() or b"").decode("utf-8", errors="replace")[:800]
    except Exception:  # noqa: BLE001
        return ""


def _is_github_rate_limit(exc: urllib.error.HTTPError, body: str = "") -> bool:
    headers = exc.headers or {}
    remaining = headers.get("X-RateLimit-Remaining") or headers.get(
        "x-ratelimit-remaining"
    )
    if remaining is not None and str(remaining).strip() == "0":
        return True
    low = (body or "").lower()
    return (
        "rate limit" in low
        or "api rate limit exceeded" in low
        or "secondary rate limit" in low
    )


def _git_ls_remote_probe(owner: str, repo: str, *, timeout: float = 20.0) -> dict[str, Any]:
    """Anonymous HTTPS ls-remote — works for public repos when API is rate-limited."""
    try:
        from swarm.farm_execution_engine import _run, resolve_git_binary
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error_code": "git_unavailable", "detail": str(exc)}
    git = resolve_git_binary()
    if not git:
        return {"ok": False, "error_code": "git_missing", "detail": "git not found"}
    url = f"https://github.com/{owner}/{repo}.git"
    res = _run([git, "ls-remote", "--heads", url], timeout=int(timeout))
    err = (res.get("stderr") or res.get("stdout") or "").lower()
    if res.get("ok"):
        return {"ok": True, "error_code": None, "detail": "ls-remote ok"}
    if "not found" in err or "repository not found" in err:
        return {"ok": False, "error_code": "repo_unreachable", "detail": err[:300]}
    if "authentication failed" in err or "could not read username" in err:
        return {"ok": False, "error_code": "repo_auth_required", "detail": err[:300]}
    return {"ok": False, "error_code": "repo_probe_network", "detail": err[:300] or "ls-remote failed"}


def parse_issue_ref(url: str) -> tuple[str, str, str] | None:
    m = _ISSUE_RE.search(url or "")
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3)


def parse_repo_full(repo_full: str) -> tuple[str, str] | None:
    """Parse owner/repo from Opire `repository` field."""
    raw = (repo_full or "").strip().removesuffix(".git")
    m = _REPO_RE.match(raw)
    if not m:
        return None
    return m.group(1), m.group(2)


def probe_github_repo(
    owner: str,
    repo: str,
    *,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Sniper: GET /repos/{owner}/{repo}. Token-aware. Never logs the token.

    On API 403 rate-limit (common without token), falls back to git ls-remote
    so public repos are not false-blocked as auth_required.

    error_code:
      None — ok
      repo_unreachable — 404 / deleted
      repo_auth_required — real permission denial (with token, or private)
      repo_rate_limited — API quota; git fallback failed/unavailable (do not hard-SKIP)
      repo_probe_network — transport failure (do not hard-SKIP)
      missing_repo — empty owner/repo
    """
    owner = (owner or "").strip()
    repo = (repo or "").strip().removesuffix(".git")
    auth_used = bool(_github_token())
    if not owner or not repo:
        return {
            "ok": False,
            "status": 0,
            "error_code": "missing_repo",
            "auth_used": auth_used,
            "detail_ru": "В bounty нет repository (owner/repo).",
            "repo_status": "unreachable",
        }
    url = f"https://api.github.com/repos/{owner}/{repo}"
    req = urllib.request.Request(url, headers=_github_api_headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw) if raw else {}
            return {
                "ok": True,
                "status": int(resp.status or 200),
                "error_code": None,
                "auth_used": auth_used,
                "private": bool(data.get("private")) if isinstance(data, dict) else False,
                "full_name": str(data.get("full_name") or f"{owner}/{repo}"),
                "detail_ru": "Репозиторий доступен на GitHub.",
                "repo_status": "ok",
                "verified_via": "api",
            }
    except urllib.error.HTTPError as exc:
        code = int(exc.code)
        body = _http_error_body(exc)
        if code == 404:
            # API 404 can also mean private-without-access — confirm with git for public
            git_fb = _git_ls_remote_probe(owner, repo, timeout=max(15.0, timeout))
            if git_fb.get("ok"):
                return {
                    "ok": True,
                    "status": 200,
                    "error_code": None,
                    "auth_used": auth_used,
                    "detail_ru": (
                        f"API вернул 404, но git ls-remote видит публичный {owner}/{repo}."
                    ),
                    "repo_status": "ok",
                    "verified_via": "git_ls_remote",
                }
            return {
                "ok": False,
                "status": 404,
                "error_code": "repo_unreachable",
                "auth_used": auth_used,
                "detail_ru": (
                    f"Репозиторий недоступен на GitHub: {owner}/{repo} (404).\n"
                    "Удалён, переименован или private без доступа.\n"
                    "Sniper: не Approve / не Execute — выберите другой bounty."
                ),
                "repo_status": "unreachable",
            }
        if code in (401, 403):
            rate_limited = _is_github_rate_limit(exc, body)
            # Unauthenticated 403 is almost always rate limit — verify via git
            if rate_limited or not auth_used:
                git_fb = _git_ls_remote_probe(owner, repo, timeout=max(15.0, timeout))
                if git_fb.get("ok"):
                    return {
                        "ok": True,
                        "status": 200,
                        "error_code": None,
                        "auth_used": auth_used,
                        "detail_ru": (
                            "GitHub API лимит/403 без токена — репозиторий подтверждён "
                            f"через git ls-remote ({owner}/{repo}). "
                            "Добавьте GITHUB_TOKEN в .env.local для API без лимита."
                        ),
                        "repo_status": "ok",
                        "verified_via": "git_ls_remote",
                        "api_status": code,
                        "rate_limited": rate_limited or not auth_used,
                    }
                if git_fb.get("error_code") == "repo_unreachable":
                    return {
                        "ok": False,
                        "status": 404,
                        "error_code": "repo_unreachable",
                        "auth_used": auth_used,
                        "detail_ru": (
                            f"Репозиторий не найден (git): {owner}/{repo}.\n"
                            "Sniper: выберите другой bounty."
                        ),
                        "repo_status": "unreachable",
                    }
                return {
                    "ok": False,
                    "status": code,
                    "error_code": "repo_rate_limited",
                    "auth_used": auth_used,
                    "detail_ru": (
                        f"GitHub API HTTP {code} (скорее rate limit без токена).\n"
                        f"git ls-remote тоже не подтвердил {owner}/{repo}.\n"
                        "Добавьте GITHUB_TOKEN в dashboard/backend/.env.local "
                        "и перезапустите Genesis.exe — затем Scan снова.\n"
                        "Пока статус unknown: Execute может попробовать clone."
                    ),
                    "repo_status": "unknown",
                    "rate_limited": True,
                }
            # Token was sent and still 401/403 without rate-limit markers → real auth
            return {
                "ok": False,
                "status": code,
                "error_code": "repo_auth_required",
                "auth_used": auth_used,
                "detail_ru": (
                    f"GitHub отказал в доступе к {owner}/{repo} (HTTP {code}) при наличии токена.\n"
                    "Проверьте scopes токена (public_repo / repo) в .env.local."
                ),
                "repo_status": "auth_required",
            }
        return {
            "ok": False,
            "status": code,
            "error_code": "repo_probe_http",
            "auth_used": auth_used,
            "detail_ru": f"GitHub API HTTP {code} для {owner}/{repo}.",
            "repo_status": "unknown",
        }
    except Exception as exc:  # noqa: BLE001
        # Network blip on API — still try git for public repos
        git_fb = _git_ls_remote_probe(owner, repo, timeout=max(15.0, timeout))
        if git_fb.get("ok"):
            return {
                "ok": True,
                "status": 200,
                "error_code": None,
                "auth_used": auth_used,
                "detail_ru": f"API недоступен ({exc}); репозиторий подтверждён через git.",
                "repo_status": "ok",
                "verified_via": "git_ls_remote",
            }
        return {
            "ok": False,
            "status": 0,
            "error_code": "repo_probe_network",
            "auth_used": auth_used,
            "detail_ru": f"Сеть/probe недоступны: {exc}",
            "repo_status": "unknown",
        }


def probe_candidate_repo(cand: dict[str, Any], *, timeout: float = 10.0) -> dict[str, Any]:
    """Resolve owner/repo from candidate fields and run Sniper probe."""
    repo_full = str(cand.get("repository") or "").strip()
    parsed = parse_repo_full(repo_full)
    if not parsed:
        ref = parse_issue_ref(str(cand.get("url") or cand.get("issue_url") or ""))
        if ref:
            parsed = (ref[0], ref[1])
    if not parsed:
        return probe_github_repo("", "", timeout=timeout)
    return probe_github_repo(parsed[0], parsed[1], timeout=timeout)


def apply_sniper_to_candidate(
    cand: dict[str, Any],
    *,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Mutate a copy: set repo_status / blockers / SKIP when hard-unreachable."""
    row = dict(cand)
    probe = probe_candidate_repo(row, timeout=timeout)
    row["repo_probe"] = {
        "ok": probe.get("ok"),
        "status": probe.get("status"),
        "error_code": probe.get("error_code"),
        "auth_used": probe.get("auth_used"),
        "repo_status": probe.get("repo_status"),
        "verified_via": probe.get("verified_via"),
        "rate_limited": probe.get("rate_limited"),
    }
    row["repo_status"] = probe.get("repo_status") or "unknown"
    code = probe.get("error_code")
    # Hard SKIP only for definitive dead repos — NOT rate-limit / unknown
    if code in ("repo_unreachable", "missing_repo"):
        blockers = sorted(set(list(row.get("blockers") or []) + [str(code)]))
        row["blockers"] = blockers
        row["recommendation"] = "SKIP"
        row["sniper_detail_ru"] = probe.get("detail_ru") or ""
    elif code == "repo_auth_required":
        # Real private/forbidden with token — skip TAKE, but message is clear
        blockers = sorted(set(list(row.get("blockers") or []) + [str(code)]))
        row["blockers"] = blockers
        row["recommendation"] = "SKIP"
        row["sniper_detail_ru"] = probe.get("detail_ru") or ""
    elif code == "repo_rate_limited":
        # Keep candidate; surface hint, do not SKIP
        row["sniper_detail_ru"] = probe.get("detail_ru") or ""
        # Drop stale auth_required from earlier bad probes
        row["blockers"] = [
            b
            for b in (row.get("blockers") or [])
            if b not in ("repo_auth_required", "repo_unreachable")
        ]
    elif probe.get("ok"):
        # Clear stale blockers from previous false 403 classifications
        row["blockers"] = [
            b
            for b in (row.get("blockers") or [])
            if b
            not in (
                "repo_auth_required",
                "repo_unreachable",
                "repo_rate_limited",
                "missing_repo",
            )
        ]
        if row.get("recommendation") == "SKIP" and not row["blockers"]:
            row["recommendation"] = "TAKE"
    return row


def fetch_github_issue(
    owner: str,
    repo: str,
    number: str,
    *,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Public GitHub issue JSON. Uses GITHUB_TOKEN/GH_TOKEN if present (rate limits)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
    req = urllib.request.Request(url, headers=_github_api_headers())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http_{exc.code}", "body": "", "title": ""}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "body": "", "title": ""}
    if not isinstance(data, dict):
        return {"ok": False, "error": "invalid_payload", "body": "", "title": ""}
    return {
        "ok": True,
        "error": None,
        "title": str(data.get("title") or ""),
        "body": str(data.get("body") or ""),
        "state": str(data.get("state") or ""),
        "labels": [
            str(x.get("name") or "")
            for x in (data.get("labels") or [])
            if isinstance(x, dict)
        ],
        "html_url": str(data.get("html_url") or ""),
    }


def fetch_issue_from_url(issue_url: str, *, timeout: float = 20.0) -> dict[str, Any]:
    ref = parse_issue_ref(issue_url)
    if not ref:
        return {"ok": False, "error": "bad_issue_url", "body": "", "title": ""}
    owner, repo, number = ref
    out = fetch_github_issue(owner, repo, number, timeout=timeout)
    out["owner"] = owner
    out["repo"] = repo
    out["number"] = number
    return out


def analyze_issue_text(title: str, body: str) -> dict[str, Any]:
    """Heuristic requirements extract for Confidence Engine (no LLM required)."""
    text = f"{title}\n{body or ''}"
    low = text.lower()
    signals: list[str] = []
    blockers: list[str] = []

    if re.search(r"hcaptcha|recaptcha|captcha|anti.?bot", low):
        blockers.append("forbidden_captcha_or_tos_evasion")
    if re.search(r"burn.?address|chainparams|op_return|ravencoin fork", low):
        signals.append("crypto_chain_params")
    if re.search(r"\bfix\b|bug|race|leak|stale|error|typo|crash", low):
        signals.append("bugfix")
    if re.search(r"rewrite|migrate|wayland|web platform export|rcs support", low):
        signals.append("large_feature")
    if re.search(r"test|pytest|jest|spec|ci", low):
        signals.append("tests_mentioned")
    if re.search(r"acceptance|criteria|должен|must |should ", low):
        signals.append("has_acceptance_criteria")
    if len(body or "") > 400:
        signals.append("detailed_description")
    elif body and len(body) < 40:
        signals.append("thin_description")

    # Rough scope from checklist-like lines
    checklist = len(re.findall(r"^\s*[-*]\s+\[[ xX]\]", body or "", re.M))
    req_lines = len(re.findall(r"^\s*[-*]\s+\S", body or "", re.M))

    return {
        "signals": signals,
        "blockers": blockers,
        "checklist_items": checklist,
        "bullet_requirements": req_lines,
        "body_chars": len(body or ""),
        "summary_ru": (
            "Есть критерии приёмки в описании."
            if "has_acceptance_criteria" in signals or checklist
            else (
                "Описание подробное."
                if "detailed_description" in signals
                else "Описание короткое — риск недопонимания требований."
            )
        ),
    }


def build_ceo_action_links(
    *,
    issue_url: str,
    repo_full: str,
    issue_id: str,
) -> dict[str, str]:
    repo_url = f"https://github.com/{repo_full}" if repo_full else ""
    return {
        "issue": issue_url or "",
        "repository": repo_url,
        "opire_dashboard": "https://app.opire.dev",
        "opire_docs_commands": "https://docs.opire.dev/overview/commands",
        "try_comment_text": "/try",
        "claim_pr_text": f"/claim #{issue_id}" if issue_id else "/claim",
        "new_pr_hint": (
            f"{repo_url}/compare" if repo_url else "https://github.com"
        ),
    }
