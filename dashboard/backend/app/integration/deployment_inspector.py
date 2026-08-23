"""Deployment Inspector — Virtus Core finds where Production actually lives.

Does not require the CEO to remember Vercel vs Railway vs Hetzner.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

from app.integration.frontend_deployment_status import (
    build_frontend_deployment_status,
    local_git_commit,
    local_git_dirty,
    production_site_url,
    _repo_root,
)


def _probe_url(url: str, *, timeout: float = 10.0) -> dict[str, Any]:
    out: dict[str, Any] = {
        "url": url,
        "ok": False,
        "status_code": None,
        "host_hint": "unknown",
        "headers_sample": {},
        "error": None,
    }
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "VirtusCore-DeploymentInspector/1.0",
                "Cache-Control": "no-cache",
                "Accept": "*/*",
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            headers = {k.lower(): v for k, v in (resp.headers.items() if resp.headers else [])}
            body = resp.read(8000)
            out["ok"] = 200 <= int(code) < 400
            out["status_code"] = int(code)
            out["headers_sample"] = {
                k: headers[k]
                for k in (
                    "server",
                    "x-powered-by",
                    "x-vercel-id",
                    "x-vercel-cache",
                    "cf-ray",
                    "cf-cache-status",
                    "via",
                    "x-railway-edge",
                    "x-railway-request-id",
                )
                if k in headers
            }
            out["host_hint"] = _classify_host(headers, body[:2000].decode("utf-8", errors="replace"))
            # build-info only if JSON
            ctype = (headers.get("content-type") or "").lower()
            if "json" in ctype:
                try:
                    data = json.loads(body.decode("utf-8", errors="replace"))
                    if isinstance(data, dict):
                        out["json"] = data
                except Exception:  # noqa: BLE001
                    pass
    except urllib.error.HTTPError as exc:
        out["status_code"] = exc.code
        out["error"] = f"http_{exc.code}"
        headers = {k.lower(): v for k, v in (exc.headers.items() if exc.headers else [])}
        out["headers_sample"] = {
            k: headers[k]
            for k in ("server", "x-powered-by", "x-vercel-id", "cf-ray")
            if k in headers
        }
        out["host_hint"] = _classify_host(headers, "")
    except Exception as exc:  # noqa: BLE001
        out["error"] = type(exc).__name__
    return out


def _classify_host(headers: dict[str, str], body_snip: str) -> str:
    if headers.get("x-vercel-id") or "vercel" in (headers.get("server") or "").lower():
        return "vercel"
    if headers.get("x-railway-edge") or headers.get("x-railway-request-id"):
        return "railway"
    if headers.get("cf-ray") or headers.get("cf-cache-status"):
        # Cloudflare in front — look deeper
        powered = (headers.get("x-powered-by") or "").lower()
        server = (headers.get("server") or "").lower()
        if "asp.net" in powered or "microsoft" in server:
            return "cloudflare_aspnet"
        if "vercel" in body_snip.lower():
            return "vercel_via_cloudflare"
        return "cloudflare"
    powered = (headers.get("x-powered-by") or "").lower()
    if "asp.net" in powered:
        return "aspnet_iis"
    if "express" in powered or "next" in powered:
        return "node"
    server = (headers.get("server") or "").lower()
    if "nginx" in server:
        return "nginx_vps"
    if "apache" in server:
        return "apache_vps"
    if "caddy" in server:
        return "caddy_vps"
    return "unknown"


def _git_remote() -> dict[str, Any]:
    root = _repo_root()
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        url = r.stdout.strip() if r.returncode == 0 else ""
    except Exception:  # noqa: BLE001
        url = ""
    try:
        b = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        branch = b.stdout.strip() if b.returncode == 0 else "unknown"
    except Exception:  # noqa: BLE001
        branch = "unknown"
    return {"url": url or None, "branch": branch, "ok": bool(url)}


def _commits_ahead_of(prod_commit: str | None) -> int | None:
    if not prod_commit or prod_commit in ("unknown",):
        return None
    root = _repo_root()
    try:
        # How many local commits since production SHA (best-effort)
        r = subprocess.run(
            ["git", "-C", str(root), "rev-list", "--count", f"{prod_commit}..HEAD"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if r.returncode == 0 and r.stdout.strip().isdigit():
            return int(r.stdout.strip())
    except Exception:  # noqa: BLE001
        return None
    return None


def _resolve_dns_hint(hostname: str) -> dict[str, Any]:
    try:
        infos = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
        ips = sorted({i[4][0] for i in infos})
        return {"ok": True, "hostname": hostname, "ips": ips[:8]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "hostname": hostname, "error": type(exc).__name__}


def _provider_flags() -> dict[str, Any]:
    vercel_linked = bool(
        (os.getenv("VERCEL_TOKEN") or os.getenv("VERCEL_API_TOKEN") or "").strip()
        and (os.getenv("VERCEL_PROJECT_ID") or os.getenv("VERCEL_PROJECT_NAME") or "").strip()
    )
    railway_token = bool((os.getenv("RAILWAY_TOKEN") or "").strip())
    expected = (
        os.getenv("GENESIS_EXPECTED_PRODUCTION_HOST", "").strip().lower()
        or os.getenv("VIRTUS_EXPECTED_HOST", "").strip().lower()
        or "ovh"  # SSOT: OVH Cloud is Production; Vercel is Preview only
    )
    ovh_host = (
        os.getenv("GENESIS_OVH_HOST", "").strip()
        or os.getenv("GENESIS_VPS_HOST", "").strip()
        or os.getenv("OVH_HOST", "").strip()
        or "137.74.173.134"
    )
    return {
        "vercel_api_configured": vercel_linked,
        "railway_token_configured": railway_token,
        "expected_host": expected or "ovh",
        "ovh_host": ovh_host,
        "hetzner_hint": bool(
            (os.getenv("HETZNER_HOST") or os.getenv("GENESIS_VPS_HOST") or "").strip()
        ),
        "ovh_configured": True,
    }


def build_deployment_inspector() -> dict[str, Any]:
    """Full Production map for CEO Executive."""
    deploy = build_frontend_deployment_status()
    site = production_site_url()
    parsed = urlparse(site)
    host = parsed.hostname or ""

    frontend_probe = _probe_url(site)
    build_info_probe = _probe_url(f"{site}/build-info.json")
    # Prefer JSON commit from build-info if real JSON
    bi = build_info_probe.get("json") if isinstance(build_info_probe.get("json"), dict) else None
    if bi and (bi.get("git_commit") or bi.get("commit")):
        deploy["production_commit"] = str(bi.get("git_commit") or bi.get("commit"))[:12]
        deploy["production_source"] = "build-info.json"
        deploy["deploy"] = str(bi.get("deploy_status") or deploy.get("deploy") or "SUCCESS")

    api_url = (
        os.getenv("NEXT_PUBLIC_API_URL", "").strip()
        or os.getenv("GENESIS_API_PUBLIC_URL", "").strip()
        or ""
    ).rstrip("/")
    if api_url:
        backend_probe = _probe_url(f"{api_url}/api/status")
        from app.integration.frontend_deployment_status import _http_json

        status_json = _http_json(f"{api_url}/api/status")
        if status_json:
            backend_probe["git_commit"] = status_json.get("git_commit")
            backend_probe["runtime"] = status_json.get("runtime_identity")
    else:
        backend_probe = {
            "url": None,
            "ok": False,
            "host_hint": "not_configured",
            "error": "NEXT_PUBLIC_API_URL missing",
        }

    flags = _provider_flags()
    remote = _git_remote()
    dns = _resolve_dns_hint(host) if host else {"ok": False}
    ahead = _commits_ahead_of(deploy.get("production_commit"))

    fe_hint = frontend_probe.get("host_hint") or "unknown"
    be_hint = backend_probe.get("host_hint") or "unknown"

    # Domain → host mapping narrative
    domain_points_to = fe_hint
    expected = flags.get("expected_host")
    mismatch = False
    if expected and domain_points_to and expected not in domain_points_to:
        mismatch = True

    # Classic: domain on Vercel/ASP while local is newer
    if deploy.get("status") == "behind" or (isinstance(ahead, int) and ahead > 0):
        mismatch = True
    if fe_hint in ("vercel", "vercel_via_cloudflare", "cloudflare_aspnet", "aspnet_iis"):
        if deploy.get("status") in ("behind", "unknown"):
            mismatch = True

    status = "ok"
    mark = "🟢"
    if mismatch or deploy.get("status") == "behind":
        status = "mismatch"
        mark = "⚠"
    elif deploy.get("status") == "unknown" or not frontend_probe.get("ok"):
        status = "unknown"
        mark = "🟡"
    elif deploy.get("status") == "in_sync":
        status = "ok"
        mark = "🟢"

    explanation = _explain(
        fe_hint=fe_hint,
        be_hint=be_hint,
        deploy=deploy,
        ahead=ahead,
        site=site,
        mismatch=mismatch,
    )
    actions = _actions(
        fe_hint=fe_hint,
        deploy=deploy,
        ahead=ahead,
        flags=flags,
        mismatch=mismatch,
    )

    return {
        "id": "deployment_inspector",
        "title": "Deployment Inspector",
        "mark": mark,
        "status": status,
        "production": {
            "domain": host or site,
            "url": site,
            "points_to": domain_points_to,
            "expected": expected or "auto-detect",
            "dns": dns,
        },
        "frontend": {
            "provider": fe_hint,
            "ok": bool(frontend_probe.get("ok")),
            "preview_only": fe_hint == "vercel" and "preview" in site,
            "production_found": bool(frontend_probe.get("ok")),
            "commit": deploy.get("production_commit"),
            "probe": frontend_probe,
            "build_info": build_info_probe,
        },
        "backend": {
            "provider": be_hint,
            "ok": bool(backend_probe.get("ok")),
            "url": api_url or None,
            "commit": backend_probe.get("git_commit"),
            "probe": backend_probe,
        },
        "git": {
            **remote,
            "local_commit": local_git_commit(),
            "local_dirty": local_git_dirty(),
            "commits_ahead_of_production": ahead,
        },
        "providers_configured": flags,
        "legacy_card": deploy,
        "explanation_ru": explanation,
        "actions": actions,
        "note_ru": (
            "Inspector сам определяет, где Production. "
            "Если телефон показывает старую версию — почти всегда mismatch domain→host или deploy not published."
        ),
    }


def _explain(
    *,
    fe_hint: str,
    be_hint: str,
    deploy: dict[str, Any],
    ahead: int | None,
    site: str,
    mismatch: bool,
) -> str:
    if ahead and ahead > 0:
        return (
            f"Локальная сборка новее Production на {ahead} коммит(ов). "
            "Production не обновлён — телефон не может показать новую версию."
        )
    if deploy.get("status") == "behind":
        return (
            f"Local commit {deploy.get('local_commit')} ≠ Production "
            f"{deploy.get('production_commit')}. Сначала Deploy to Production."
        )
    if fe_hint in ("cloudflare_aspnet", "aspnet_iis"):
        return (
            f"Основной домен ({site}) указывает на ASP.NET/Cloudflare-хостинг, "
            "а не на свежий Next.js deploy. Поэтому телефон открывает старую (или чужую) сборку."
        )
    if fe_hint in ("vercel", "vercel_via_cloudflare") and deploy.get("status") == "unknown":
        return (
            "Домен похож на Vercel, но /build-info.json не найден — "
            "либо старый деплой без build-info, либо не тот проект."
        )
    if not mismatch and deploy.get("status") == "in_sync":
        return "Frontend Production синхронизирован с Local. Можно проверять телефон в инкогнито."
    if be_hint in ("unknown", "not_configured") or not deploy:
        return (
            "Не удалось однозначно определить Production. "
            "Проверьте GENESIS_PUBLIC_URL / NEXT_PUBLIC_API_URL и DNS."
        )
    return (
        f"Frontend → {fe_hint}, Backend → {be_hint}. "
        "Сверьте Domain и Expected; при сомнении — Deploy to Production."
    )


def _actions(
    *,
    fe_hint: str,
    deploy: dict[str, Any],
    ahead: int | None,
    flags: dict[str, Any],
    mismatch: bool,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if deploy.get("status") in ("behind", "unknown") or (ahead and ahead > 0):
        actions.append(
            {
                "id": "deploy_ovh",
                "label": "Deploy to OVH",
                "priority": 1,
                "detail_ru": (
                    "Production = OVH. git pull + docker compose up -d --build "
                    "(scripts/deploy_ovh.sh). Vercel — только Preview."
                ),
            }
        )
        actions.append(
            {
                "id": "sync_frontend",
                "label": "Sync Frontend",
                "priority": 2,
                "detail_ru": "Убедитесь, что OVH commit == Local после деплоя.",
            }
        )
    if fe_hint in ("cloudflare_aspnet", "aspnet_iis", "cloudflare", "vercel", "vercel_via_cloudflare") and mismatch:
        actions.append(
            {
                "id": "update_dns",
                "label": "Update DNS → OVH",
                "priority": 1,
                "detail_ru": (
                    "Домен должен указывать на OVH Production, не на Vercel/AWS/старый хост."
                ),
            }
        )
        actions.append(
            {
                "id": "switch_domain",
                "label": "Switch Domain",
                "priority": 2,
                "detail_ru": "Либо DNS → OVH, либо смените GENESIS_PUBLIC_URL на OVH URL.",
            }
        )
    if flags.get("expected_host") == "ovh" and fe_hint.startswith("vercel"):
        actions.append(
            {
                "id": "vercel_is_preview",
                "label": "Keep Vercel as Preview",
                "priority": 3,
                "detail_ru": "Не путайте Vercel READY с Production. Клиенты → virtuscore.com → OVH.",
            }
        )
    if not actions:
        actions.append(
            {
                "id": "verify_incognito",
                "label": "Verify on phone (incognito)",
                "priority": 3,
                "detail_ru": "Production OK — проверьте сайт в режиме инкогнито на телефоне.",
            }
        )
    actions.sort(key=lambda a: int(a.get("priority") or 9))
    return actions
