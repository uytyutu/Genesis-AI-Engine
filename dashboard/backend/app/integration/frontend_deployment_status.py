"""Frontend Deployment status for CEO Executive.

Compares local git HEAD vs production /build-info.json (and optional Vercel API).
"""

from __future__ import annotations

from urllib.parse import quote
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    # swarm/ or dashboard/backend/app/integration → repo root
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / ".git").exists() and (p / "dashboard").exists():
            return p
    return here.parents[4]


def local_git_commit(*, short: bool = True) -> str:
    root = _repo_root()
    try:
        args = ["git", "-C", str(root), "rev-parse"]
        args.append("--short" if short else "HEAD")
        args.append("HEAD")
        r = subprocess.run(args, capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def local_git_dirty() -> bool:
    root = _repo_root()
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return bool(r.stdout.strip()) if r.returncode == 0 else False
    except (OSError, subprocess.TimeoutExpired):
        return False


def production_site_url() -> str:
    return (
        os.getenv("GENESIS_PUBLIC_URL", "").strip()
        or os.getenv("NEXT_PUBLIC_SITE_URL", "").strip()
        or os.getenv("GENESIS_FRONTEND_URL", "").strip()
        or "https://virtuscore.com"
    ).rstrip("/")


def _http_json(url: str, *, timeout: float = 12.0) -> dict[str, Any] | None:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "VirtusCore-CEO-DeployCheck/1.0",
                "Cache-Control": "no-cache",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            return data if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001
        return None


def _http_meta_commit(url: str, *, timeout: float = 12.0) -> str | None:
    """Best-effort scrape of meta virtus-git-commit from HTML."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "VirtusCore-CEO-DeployCheck/1.0",
                "Cache-Control": "no-cache",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="replace")[:200_000]
        import re

        m = re.search(
            r'<meta\s+name=["\']virtus-git-commit["\']\s+content=["\']([a-f0-9]{7,40})["\']',
            html,
            re.I,
        )
        if m:
            return m.group(1)
        m = re.search(r'"gitCommit"\s*:\s*"([a-f0-9]{7,40})"', html)
        if m:
            return m.group(1)
    except Exception:  # noqa: BLE001
        return None
    return None


def _vercel_production_commit() -> dict[str, Any] | None:
    token = (os.getenv("VERCEL_TOKEN") or os.getenv("VERCEL_API_TOKEN") or "").strip()
    project = (
        os.getenv("VERCEL_PROJECT_ID")
        or os.getenv("VERCEL_PROJECT_NAME")
        or ""
    ).strip()
    team = (os.getenv("VERCEL_TEAM_ID") or "").strip()
    if not token or not project:
        return None
    try:
        q = f"https://api.vercel.com/v6/deployments?projectId={quote(project)}&limit=5&target=production"
        if team:
            q += f"&teamId={quote(team)}"
        req = urllib.request.Request(
            q,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        deps = data.get("deployments") if isinstance(data, dict) else None
        if not isinstance(deps, list) or not deps:
            return {"ok": False, "error": "no_deployments"}
        top = deps[0] if isinstance(deps[0], dict) else {}
        meta = top.get("meta") if isinstance(top.get("meta"), dict) else {}
        commit = (
            meta.get("githubCommitSha")
            or meta.get("gitlabCommitSha")
            or top.get("id")
            or ""
        )
        state = str(top.get("readyState") or top.get("state") or "")
        return {
            "ok": True,
            "commit": str(commit)[:12] if commit else None,
            "commit_full": str(commit) if commit else None,
            "state": state,
            "url": top.get("url"),
            "created": top.get("created"),
        }
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"vercel_http_{exc.code}"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__}


def build_frontend_deployment_status() -> dict[str, Any]:
    local = local_git_commit(short=True)
    local_full = local_git_commit(short=False)
    dirty = local_git_dirty()
    site = production_site_url()

    prod_commit: str | None = None
    prod_source = "none"
    deploy_state = "UNKNOWN"
    fetch_errors: list[str] = []

    info = _http_json(f"{site}/build-info.json")
    if info and (info.get("git_commit") or info.get("commit")):
        prod_commit = str(info.get("git_commit") or info.get("commit"))[:12]
        prod_source = "build-info.json"
        deploy_state = str(info.get("deploy_status") or "SUCCESS")
    else:
        if info is None:
            fetch_errors.append("build-info.json missing or unreachable")
        scraped = _http_meta_commit(site)
        if scraped:
            prod_commit = scraped[:12]
            prod_source = "html_meta"
            deploy_state = "SUCCESS"

    vercel = _vercel_production_commit()
    if vercel and vercel.get("ok") and vercel.get("commit"):
        # Prefer Vercel as deploy authority when available
        prod_commit = str(vercel["commit"])[:12]
        prod_source = "vercel_api"
        state = str(vercel.get("state") or "").upper()
        if state in ("READY", "SUCCESS"):
            deploy_state = "SUCCESS"
        elif state in ("ERROR", "CANCELED"):
            deploy_state = "FAILED"
        elif state in ("BUILDING", "QUEUED", "INITIALIZING"):
            deploy_state = "PENDING"
        else:
            deploy_state = state or "UNKNOWN"

    if not prod_commit:
        status = "unknown"
        mark = "🟡"
        detail_ru = (
            "Production commit неизвестен — нет /build-info.json и нет Vercel API. "
            "Сначала задеплойте фронт с build-info, затем сверьте телефон в инкогнито."
        )
        behind = None
    else:
        local_n = local.lower()
        prod_n = prod_commit.lower()
        match = local_n == prod_n or local_full.lower().startswith(prod_n) or prod_n.startswith(local_n)
        if match and not dirty:
            status = "in_sync"
            mark = "🟢"
            behind = False
            detail_ru = "Local и Production на одном commit."
            if deploy_state == "UNKNOWN":
                deploy_state = "SUCCESS"
        elif match and dirty:
            status = "local_dirty"
            mark = "🟡"
            behind = False
            detail_ru = "Commit совпадает, но локально есть незакоммиченные изменения."
        else:
            status = "behind"
            mark = "🔴"
            behind = True
            detail_ru = "Production is behind local (или на другом commit)."
            if deploy_state == "UNKNOWN":
                deploy_state = "PENDING"

    return {
        "id": "frontend_deployment",
        "title": "Frontend Deployment",
        "local_commit": local,
        "local_commit_full": local_full if local_full != "unknown" else None,
        "local_dirty": dirty,
        "production_commit": prod_commit,
        "production_url": site,
        "production_source": prod_source,
        "status": status,
        "mark": mark,
        "behind": behind,
        "deploy": deploy_state,
        "detail_ru": detail_ru,
        "vercel": vercel,
        "fetch_errors": fetch_errors,
        "note_ru": (
            "Если телефон показывает старую версию — сначала смотри эту карточку. "
            "Проблема почти всегда в deploy, не в браузере."
        ),
        "checklist_ru": [
            "1. Frontend build OK?",
            "2. Deploy SUCCESS?",
            "3. Production commit == Local commit?",
            "4. Телефон: инкогнито после успешного deploy",
        ],
    }
