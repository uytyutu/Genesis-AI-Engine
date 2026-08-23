"""Deployment Manager — OVH is Production; Vercel is Preview only.

Policy (Virtus Core SSOT):
  Cursor → Git → CI/CD → OVH Cloud (Production) → virtuscore.com
  Vercel = preview / test / rollback only.
"""

from __future__ import annotations

import os
import socket
import subprocess
from typing import Any
from urllib.parse import urlparse

from app.integration.deployment_inspector import (
    _commits_ahead_of,
    _probe_url,
    _resolve_dns_hint,
    build_deployment_inspector,
    local_git_commit,
    local_git_dirty,
)
from app.integration.frontend_deployment_status import (
    _http_json,
    _http_meta_commit,
    _vercel_production_commit,
)

# Known OVH VPS from deploy/.env.example Stage-2 smoke IP.
DEFAULT_OVH_HOST = "137.74.173.134"
PRODUCTION_DOMAIN = "virtuscore.com"
EXPECTED_PROVIDER = "ovh"


def ovh_host() -> str:
    return (
        os.getenv("GENESIS_OVH_HOST", "").strip()
        or os.getenv("GENESIS_VPS_HOST", "").strip()
        or os.getenv("OVH_HOST", "").strip()
        or DEFAULT_OVH_HOST
    )


def ovh_ssh_target() -> str | None:
    """user@host for SSH, or None if not configured."""
    explicit = (os.getenv("GENESIS_OVH_SSH", "") or os.getenv("OVH_SSH", "")).strip()
    if explicit:
        return explicit
    user = (os.getenv("GENESIS_OVH_SSH_USER", "") or os.getenv("OVH_SSH_USER", "")).strip()
    host = ovh_host()
    if user and host:
        return f"{user}@{host}"
    return None


def ovh_remote_path() -> str:
    return (
        os.getenv("GENESIS_OVH_REMOTE_PATH", "").strip()
        or os.getenv("OVH_REMOTE_PATH", "").strip()
        or "/srv/genesis"
    )


def _tcp_open(host: str, port: int = 22, timeout: float = 5.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _ssh_probe(target: str, remote_path: str) -> dict[str, Any]:
    """Non-interactive SSH: connectivity + remote git HEAD (best-effort)."""
    out: dict[str, Any] = {
        "target": target,
        "ok": False,
        "reachable": False,
        "remote_commit": None,
        "remote_path": remote_path,
        "error": None,
    }
    try:
        # BatchMode: never prompt for password/passphrase.
        base = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=8",
            "-o",
            "StrictHostKeyChecking=accept-new",
            target,
        ]
        ping = subprocess.run(
            [*base, "echo", "ok"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if ping.returncode != 0:
            out["error"] = (ping.stderr or ping.stdout or "ssh_failed").strip()[:240]
            return out
        out["reachable"] = True
        # Prefer git in repo; fall back to docker inspect label if present.
        cmd = (
            f"cd {remote_path} 2>/dev/null && git rev-parse --short HEAD 2>/dev/null "
            f"|| cd {remote_path}/deploy 2>/dev/null && git -C .. rev-parse --short HEAD 2>/dev/null "
            f"|| echo unknown"
        )
        g = subprocess.run(
            [*base, "bash", "-lc", cmd],
            capture_output=True,
            text=True,
            timeout=20,
        )
        commit = (g.stdout or "").strip().splitlines()[-1] if g.stdout else ""
        if commit and commit != "unknown":
            out["remote_commit"] = commit[:12]
        out["ok"] = True
    except subprocess.TimeoutExpired:
        out["error"] = "ssh_timeout"
    except FileNotFoundError:
        out["error"] = "ssh_binary_missing"
    except Exception as exc:  # noqa: BLE001
        out["error"] = type(exc).__name__
    return out


def _ovh_http_snapshot(host: str) -> dict[str, Any]:
    """HTTP probes against OVH IP / hostname (pre-DNS or direct)."""
    bases = [f"http://{host}", f"https://{host}"]
    snap: dict[str, Any] = {
        "host": host,
        "health": None,
        "api_status": None,
        "frontend_hint": None,
        "build_info_commit": None,
        "git_commit": None,
        "ok": False,
    }
    for base in bases:
        health = _probe_url(f"{base}/health")
        if health.get("ok"):
            snap["health"] = health
            snap["ok"] = True
            status = _http_json(f"{base}/api/status")
            if status:
                snap["api_status"] = status
                snap["git_commit"] = status.get("git_commit")
            site = _probe_url(f"{base}/site") or _probe_url(f"{base}/")
            snap["frontend_hint"] = (site or {}).get("host_hint")
            bi = _probe_url(f"{base}/build-info.json")
            js = bi.get("json") if isinstance(bi.get("json"), dict) else None
            if js:
                snap["build_info_commit"] = str(js.get("git_commit") or js.get("commit") or "")[:12]
            break
    return snap


def _domain_points_to_ovh(dns: dict[str, Any], ovh: str) -> bool:
    ips = dns.get("ips") if isinstance(dns, dict) else None
    if not ips:
        return False
    # Resolve OVH host to IPs and intersect
    try:
        ovh_ips = {i[4][0] for i in socket.getaddrinfo(ovh, 80, type=socket.SOCK_STREAM)}
    except OSError:
        ovh_ips = {ovh} if _looks_like_ip(ovh) else set()
    return bool(set(ips) & ovh_ips)


def _looks_like_ip(s: str) -> bool:
    parts = s.split(".")
    return len(parts) == 4 and all(p.isdigit() for p in parts)


def _norm_commit(c: str | None) -> str | None:
    if not c or c in ("unknown", "none", ""):
        return None
    return str(c).strip()[:12]


def _commits_match(a: str | None, b: str | None) -> bool | None:
    """True/False if both known; None if either unknown."""
    aa, bb = _norm_commit(a), _norm_commit(b)
    if not aa or not bb:
        return None
    return aa == bb or aa.startswith(bb) or bb.startswith(aa)


def _mark_commit(local: str | None, other: str | None) -> str:
    m = _commits_match(local, other)
    if other is None:
        return "❓"
    if m is True:
        return "✅"
    if m is False:
        return "❌"
    return "❓"


def _vercel_commit_snapshot() -> dict[str, Any]:
    """Preview/test deploy commit (not Production)."""
    out: dict[str, Any] = {
        "commit": None,
        "source": "none",
        "state": None,
        "url": None,
        "ok": False,
    }
    api = _vercel_production_commit()
    if api and api.get("ok") and api.get("commit"):
        out["commit"] = _norm_commit(str(api["commit"]))
        out["source"] = "vercel_api"
        out["state"] = api.get("state")
        out["url"] = api.get("url")
        out["ok"] = True
        return out
    preview = (
        os.getenv("VERCEL_PREVIEW_URL", "").strip()
        or os.getenv("GENESIS_VERCEL_URL", "").strip()
        or "https://genesis-ai-engine.vercel.app"
    ).rstrip("/")
    info = _http_json(f"{preview}/build-info.json")
    if info and (info.get("git_commit") or info.get("commit")):
        out["commit"] = _norm_commit(str(info.get("git_commit") or info.get("commit")))
        out["source"] = "vercel_build_info"
        out["url"] = preview
        out["ok"] = True
        return out
    meta = _http_meta_commit(preview)
    if meta:
        out["commit"] = _norm_commit(meta)
        out["source"] = "vercel_html_meta"
        out["url"] = preview
        out["ok"] = True
        return out
    if api and not api.get("ok"):
        out["error"] = api.get("error")
    return out


def _domain_commit_snapshot(public_url: str) -> dict[str, Any]:
    """What virtuscore.com (customer domain) actually serves."""
    site = public_url.rstrip("/")
    out: dict[str, Any] = {
        "commit": None,
        "source": "none",
        "url": site,
        "ok": False,
        "ssl_ok": False,
        "reachable": False,
    }
    # SSL / reachability
    https = site if site.startswith("https://") else f"https://{urlparse(site).netloc or site}"
    probe = _probe_url(https if "://" in https else f"https://{https}")
    out["reachable"] = bool(probe.get("ok"))
    out["ssl_ok"] = bool(probe.get("ok")) and https.startswith("https://")
    out["host_hint"] = probe.get("host_hint")

    info = _http_json(f"{site}/build-info.json")
    if info and (info.get("git_commit") or info.get("commit")):
        out["commit"] = _norm_commit(str(info.get("git_commit") or info.get("commit")))
        out["source"] = "domain_build_info"
        out["ok"] = True
        return out
    meta = _http_meta_commit(site)
    if meta:
        out["commit"] = _norm_commit(meta)
        out["source"] = "domain_html_meta"
        out["ok"] = True
        return out
    # HTML returned for build-info → old host without Virtus build-info
    bi = _probe_url(f"{site}/build-info.json")
    if bi.get("ok") and not bi.get("json"):
        out["source"] = "domain_no_build_info"
        out["error"] = "build-info not JSON (likely legacy host)"
    return out


def _build_commit_chain(
    *,
    local: str,
    vercel: dict[str, Any],
    ovh_commit: str | None,
    domain: dict[str, Any],
) -> dict[str, Any]:
    v_c = vercel.get("commit")
    d_c = domain.get("commit")
    rows = [
        {"id": "local", "label": "Local", "commit": _norm_commit(local) or "unknown", "mark": "·"},
        {
            "id": "vercel",
            "label": "Vercel",
            "commit": v_c or "unknown",
            "mark": _mark_commit(local, v_c),
            "role": "preview",
        },
        {
            "id": "ovh",
            "label": "OVH",
            "commit": ovh_commit or "unknown",
            "mark": _mark_commit(local, ovh_commit),
            "role": "production",
        },
        {
            "id": "domain",
            "label": "Domain",
            "commit": d_c or "unknown",
            "mark": _mark_commit(local, d_c) if d_c else (
                "❌" if domain.get("host_hint") not in (None, "nginx_vps", "caddy_vps", "node") else "❓"
            ),
            "role": "customer",
        },
    ]
    # Domain should match OVH when DNS correct
    domain_matches_ovh = _commits_match(ovh_commit, d_c)
    local_matches_ovh = _commits_match(local, ovh_commit)
    local_matches_vercel = _commits_match(local, v_c)

    behind_parts: list[str] = []
    if local_matches_vercel is True and local_matches_ovh is False:
        behind_parts.append("OVH behind Local/Vercel")
    if domain_matches_ovh is False and ovh_commit and d_c:
        behind_parts.append("Domain ≠ OVH")
    if not d_c and domain.get("reachable"):
        behind_parts.append("Domain has no Virtus build-info (legacy host)")

    summary_status = "aligned"
    if behind_parts:
        summary_status = "production_behind"
    elif local_matches_ovh is None or (d_c is None and not domain.get("ok")):
        summary_status = "incomplete"

    text_lines = [
        f"Local:        {rows[0]['commit']}",
        f"Vercel:       {rows[1]['commit']} {rows[1]['mark']}",
        f"OVH:          {rows[2]['commit']} {rows[2]['mark']}",
        f"Domain:       {rows[3]['commit']} {rows[3]['mark']}",
    ]
    if summary_status == "production_behind":
        text_lines.append("Status:")
        text_lines.append("Production behind by 1+ deployment.")
        text_lines.extend(f"· {p}" for p in behind_parts)
    elif summary_status == "aligned" and local_matches_ovh and domain_matches_ovh:
        text_lines.append("Status: All aligned ✅")
    else:
        text_lines.append(f"Status: {summary_status}")

    return {
        "rows": rows,
        "text": "\n".join(text_lines),
        "summary_status": summary_status,
        "behind_reasons": behind_parts,
        "local_matches_vercel": local_matches_vercel,
        "local_matches_ovh": local_matches_ovh,
        "domain_matches_ovh": domain_matches_ovh,
    }


def _production_health(
    *,
    domain_host: str,
    domain_on_ovh: bool,
    dns: dict[str, Any],
    ovh_ok: bool,
    ovh_http: dict[str, Any],
    domain_snap: dict[str, Any],
    ovh_commit: str | None,
    local: str,
    chain: dict[str, Any],
) -> dict[str, Any]:
    """Executive Production Health checklist."""
    api_ok = bool(ovh_http.get("api_status") or (ovh_http.get("health") or {}).get("ok"))
    fe_ok = bool(ovh_http.get("ok"))
    ssl = bool(domain_snap.get("ssl_ok"))
    build = bool(domain_snap.get("commit") or ovh_commit)
    latest = _commits_match(local, ovh_commit) is True and (
        domain_on_ovh and (_commits_match(ovh_commit, domain_snap.get("commit")) in (True, None))
    )
    # If domain not on OVH, latest cannot be green
    if not domain_on_ovh:
        latest = False

    items = [
        {"id": "domain", "label": "Domain", "ok": bool(domain_host), "detail": domain_host},
        {
            "id": "dns",
            "label": "DNS",
            "ok": domain_on_ovh,
            "detail": "→ OVH" if domain_on_ovh else f"→ {(dns.get('ips') or ['?'])[:2]}",
        },
        {"id": "ovh", "label": "OVH", "ok": ovh_ok, "detail": ovh_host()},
        {"id": "backend", "label": "Backend", "ok": api_ok, "detail": "/health|/api/status"},
        {"id": "frontend", "label": "Frontend", "ok": fe_ok, "detail": "OVH HTTP"},
        {"id": "ssl", "label": "SSL", "ok": ssl if domain_on_ovh else False, "detail": "HTTPS"},
        {
            "id": "build",
            "label": "Build",
            "ok": build and domain_on_ovh,
            "detail": domain_snap.get("commit") or ovh_commit or "unknown",
        },
        {
            "id": "latest_commit",
            "label": "Latest Commit",
            "ok": bool(latest),
            "detail": f"local={local} ovh={ovh_commit or 'unknown'}",
        },
    ]
    for it in items:
        it["mark"] = "🟢" if it["ok"] else "🔴"
    all_ok = all(bool(i["ok"]) for i in items)
    return {
        "title": "Production Health",
        "ok": all_ok,
        "mark": "🟢" if all_ok else "🔴",
        "items": items,
        "note_ru": (
            "Все зелёные — клиенты видят актуальную версию на OVH. "
            "Любой красный — сначала инфраструктура, не код."
            if not all_ok
            else "Production Health OK — Domain → OVH → Latest Commit."
        ),
        "commit_chain_status": chain.get("summary_status"),
    }


def _is_aws_like(ips: list[str] | None) -> bool:
    # Heuristic from live probe: virtuscore.com → 54.x / 13.x (AWS ELB region)
    if not ips:
        return False
    return any(ip.startswith(("54.", "13.", "3.", "18.", "52.")) for ip in ips)


def build_deployment_manager() -> dict[str, Any]:
    """CEO report: where Production is, OVH sync, and what to do next."""
    inspector = build_deployment_inspector()
    local = local_git_commit()
    dirty = local_git_dirty()
    host = ovh_host()
    ssh_target = ovh_ssh_target()
    remote_path = ovh_remote_path()

    domain = PRODUCTION_DOMAIN
    public_url = (
        os.getenv("GENESIS_PUBLIC_URL", "").strip()
        or os.getenv("NEXT_PUBLIC_SITE_URL", "").strip()
        or f"https://{domain}"
    )
    parsed = urlparse(public_url if "://" in public_url else f"https://{public_url}")
    domain_host = parsed.hostname or domain

    dns = _resolve_dns_hint(domain_host)
    ovh_http = _ovh_http_snapshot(host)
    ssh = (
        _ssh_probe(ssh_target, remote_path)
        if ssh_target
        else {
            "target": None,
            "ok": False,
            "reachable": False,
            "remote_commit": None,
            "error": "GENESIS_OVH_SSH or GENESIS_OVH_SSH_USER not set",
            "configured": False,
        }
    )
    if ssh_target:
        ssh["configured"] = True
    else:
        ssh["port22_open"] = _tcp_open(host, 22)

    # Effective production commit on OVH (prefer SSH git, then API status, then build-info)
    ovh_commit = (
        ssh.get("remote_commit")
        or (None if (ovh_http.get("git_commit") in (None, "unknown")) else ovh_http.get("git_commit"))
        or ovh_http.get("build_info_commit")
        or None
    )
    if isinstance(ovh_commit, str):
        ovh_commit = ovh_commit[:12] if ovh_commit != "unknown" else None

    ahead = _commits_ahead_of(ovh_commit) if ovh_commit else None
    domain_on_ovh = _domain_points_to_ovh(dns, host)
    domain_provider = inspector.get("frontend", {}).get("provider") or "unknown"

    vercel_snap = _vercel_commit_snapshot()
    domain_snap = _domain_commit_snapshot(public_url if "://" in public_url else f"https://{domain_host}")
    # Prefer inspector host_hint when domain probe is vague
    if not domain_snap.get("host_hint"):
        domain_snap["host_hint"] = domain_provider

    commit_chain = _build_commit_chain(
        local=local,
        vercel=vercel_snap,
        ovh_commit=ovh_commit,
        domain=domain_snap,
    )

    # Status machine
    if not ovh_http.get("ok") and not ssh.get("reachable"):
        sync_status = "ovh_unreachable"
        mark = "🔴"
    elif not domain_on_ovh:
        sync_status = "dns_mismatch"
        mark = "⚠"
    elif ovh_commit and local and ovh_commit != local[: len(ovh_commit)] and (
        ahead is None or ahead > 0
    ):
        sync_status = "outdated"
        mark = "⚠"
    elif ovh_commit and local and (
        ovh_commit == local or local.startswith(ovh_commit) or ovh_commit.startswith(local)
    ):
        sync_status = "in_sync"
        mark = "🟢"
    elif ovh_http.get("ok") and not ovh_commit:
        sync_status = "ovh_commit_unknown"
        mark = "🟡"
    else:
        sync_status = "review"
        mark = "🟡"

    if commit_chain.get("summary_status") == "production_behind" and sync_status in (
        "in_sync",
        "review",
        "ovh_commit_unknown",
    ):
        # Chain is more specific when Local≈Vercel but OVH/Domain lag
        sync_status = "outdated"
        mark = "⚠"

    explanation = _manager_explain(
        sync_status=sync_status,
        domain_host=domain_host,
        domain_provider=domain_provider,
        dns=dns,
        ovh_commit=ovh_commit,
        local=local,
        ahead=ahead,
        domain_on_ovh=domain_on_ovh,
        host=host,
    )
    if commit_chain.get("behind_reasons"):
        explanation = explanation + " · " + "; ".join(commit_chain["behind_reasons"])

    actions = _manager_actions(
        sync_status=sync_status,
        ssh_configured=bool(ssh_target),
        domain_on_ovh=domain_on_ovh,
    )

    auto_deploy = (
        os.getenv("GENESIS_OVH_AUTO_DEPLOY", "").strip().lower() in ("1", "true", "yes")
    )

    ovh_ok = bool(ovh_http.get("ok") or ssh.get("reachable"))
    production_health = _production_health(
        domain_host=domain_host,
        domain_on_ovh=domain_on_ovh,
        dns=dns,
        ovh_ok=ovh_ok,
        ovh_http=ovh_http,
        domain_snap=domain_snap,
        ovh_commit=ovh_commit,
        local=local,
        chain=commit_chain,
    )

    return {
        "id": "deployment_manager",
        "title": "Deployment Manager",
        "policy": {
            "production": "ovh",
            "preview": "vercel",
            "chain_ru": "Cursor → Git → Deploy → OVH → virtuscore.com",
            "vercel_role_ru": "Только Preview / тестовые сборки / проверка перед публикацией",
            "publish_pipeline": [
                "Publish",
                "Build OK",
                "Tests OK",
                "Quality Gates PASS",
                "Deploy to OVH",
                "Health Check",
                "Production OK",
            ],
            "auto_deploy_enabled": auto_deploy,
            "auto_deploy_note_ru": (
                "Авто-деплой выключен. Публикация — осознанный Publish → gates → OVH, "
                "не после каждого сохранения файла."
            ),
        },
        "mark": mark,
        "status": sync_status,
        "production_server": {
            "provider": "OVH Cloud",
            "host": host,
            "ok": ovh_ok,
            "http": ovh_http,
            "ssh": ssh,
            "path": remote_path,
            "frontend_version": ovh_commit or "unknown",
        },
        "local": {
            "commit": local,
            "dirty": dirty,
            "commits_ahead_of_ovh": ahead,
        },
        "domain": {
            "name": domain_host,
            "points_to_provider": domain_provider,
            "points_to_ovh": domain_on_ovh,
            "dns": dns,
            "expected": EXPECTED_PROVIDER,
            "aws_like": _is_aws_like(dns.get("ips") if isinstance(dns, dict) else None),
            "commit": domain_snap.get("commit"),
            "commit_source": domain_snap.get("source"),
        },
        "vercel": {
            "role": "preview",
            "not_production": True,
            "commit": vercel_snap.get("commit"),
            "source": vercel_snap.get("source"),
            "url": vercel_snap.get("url"),
            "ok": vercel_snap.get("ok"),
            "note_ru": "Успешный Vercel deploy ≠ Production. Клиенты смотрят virtuscore.com → должен быть OVH.",
        },
        "commit_chain": commit_chain,
        "production_health": production_health,
        "comparison": {
            "production_commit": ovh_commit or "unknown",
            "local_commit": local,
            "vercel_commit": vercel_snap.get("commit") or "unknown",
            "domain_commit": domain_snap.get("commit") or "unknown",
            "status": sync_status.upper() if sync_status != "in_sync" else "IN_SYNC",
        },
        "explanation_ru": explanation,
        "actions": actions,
        "inspector": inspector,
        "note_ru": (
            "OVH — единственный Production. Если телефон показывает старую версию — "
            "сначала DNS (virtuscore.com → OVH), затем Deploy to OVH."
        ),
    }


def _manager_explain(
    *,
    sync_status: str,
    domain_host: str,
    domain_provider: str,
    dns: dict[str, Any],
    ovh_commit: str | None,
    local: str,
    ahead: int | None,
    domain_on_ovh: bool,
    host: str,
) -> str:
    if sync_status == "dns_mismatch":
        ips = ", ".join((dns.get("ips") or [])[:4]) if isinstance(dns, dict) else "?"
        aws = _is_aws_like(dns.get("ips") if isinstance(dns, dict) else None)
        extra = (
            " Сейчас домен похож на AWS/Kestrel (старый сайт), не на OVH."
            if aws
            else f" Сейчас провайдер домена: {domain_provider}."
        )
        return (
            f"Основной домен {domain_host} не указывает на OVH ({host}). "
            f"DNS IP: {ips or 'unknown'}.{extra} "
            "Поэтому телефон открывает старую версию, даже если Vercel уже обновился."
        )
    if sync_status == "outdated":
        n = f" на {ahead} коммит(ов)" if ahead else ""
        return (
            f"OVH не обновлялся после последнего commit. "
            f"Production (OVH): {ovh_commit or 'unknown'} · Local: {local}{n}."
        )
    if sync_status == "ovh_unreachable":
        return (
            f"OVH host {host} недоступен по HTTP/SSH. "
            "Проверьте VPS, firewall и GENESIS_OVH_HOST."
        )
    if sync_status == "ovh_commit_unknown":
        return (
            f"OVH отвечает ({host}), но git commit неизвестен "
            "(API git_commit=unknown, нет /build-info.json). "
            "Нужен SSH (GENESIS_OVH_SSH) или свежий deploy с build-info."
        )
    if sync_status == "in_sync" and domain_on_ovh:
        return "Production Server: OVH · Domain → OVH · версии совпадают. Production OK."
    return (
        f"Статус: {sync_status}. Domain→{domain_provider}, OVH commit={ovh_commit or 'unknown'}, "
        f"Local={local}."
    )


def _manager_actions(
    *,
    sync_status: str,
    ssh_configured: bool,
    domain_on_ovh: bool,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if not domain_on_ovh:
        actions.append(
            {
                "id": "update_dns_ovh",
                "label": "Update DNS → OVH",
                "priority": 1,
                "detail_ru": (
                    "A/AAAA записи virtuscore.com → IP OVH VPS. "
                    "Пока DNS на AWS/старый хост — клиенты не увидят новый Virtus Core."
                ),
            }
        )
    if sync_status in ("outdated", "ovh_commit_unknown", "review", "dns_mismatch"):
        actions.append(
            {
                "id": "deploy_ovh",
                "label": "Deploy to OVH",
                "priority": 1 if sync_status == "outdated" else 2,
                "detail_ru": (
                    "На сервере: cd deploy && git pull && docker compose up -d --build. "
                    "Или scripts/deploy_ovh.sh после настройки SSH."
                ),
            }
        )
    if not ssh_configured:
        actions.append(
            {
                "id": "configure_ovh_ssh",
                "label": "Configure OVH SSH",
                "priority": 2,
                "detail_ru": (
                    "Задайте GENESIS_OVH_SSH=user@host или GENESIS_OVH_SSH_USER + "
                    "GENESIS_OVH_HOST, ключ в ssh-agent. Тогда Manager прочитает commit по SSH."
                ),
            }
        )
    actions.append(
        {
            "id": "keep_vercel_preview",
            "label": "Keep Vercel as Preview only",
            "priority": 3,
            "detail_ru": "Не направляйте virtuscore.com на Vercel. Preview — для проверки перед OVH.",
        }
    )
    if sync_status == "in_sync" and domain_on_ovh:
        actions.append(
            {
                "id": "verify_phone",
                "label": "Verify on phone (incognito)",
                "priority": 3,
                "detail_ru": "Production OK — проверьте virtuscore.com в инкогнито.",
            }
        )
    actions.sort(key=lambda a: int(a.get("priority") or 9))
    return actions
