"""Non-fatal startup checks — log a report, never block boot."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from app.config import genesis_env
from app.env_loader import load_local_env

logger = logging.getLogger("genesis.startup")

_SECRET_KEYS = (
    "GENESIS_GROQ_API_KEY",
    "GENESIS_GEMINI_API_KEY",
    "GENESIS_OPENROUTER_API_KEY",
    "GENESIS_LLM_API_KEY",
    "OPENAI_API_KEY",
    "STRIPE_SECRET_KEY",
    "STRIPE_PUBLISHABLE_KEY",
    "STRIPE_WEBHOOK_SECRET",
)


def _check_memory(memory_dir: Path) -> dict[str, Any]:
    ok = memory_dir.is_dir()
    writable = False
    if ok:
        try:
            probe = memory_dir / ".write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            writable = True
        except OSError:
            writable = False
    return {
        "name": "memory",
        "ok": ok and writable,
        "path": str(memory_dir),
        "writable": writable,
    }


def _check_workspace(repo_root: Path) -> dict[str, Any]:
    markers = ("brain", "kernel", "agents", "dashboard")
    missing = [m for m in markers if not (repo_root / m).is_dir()]
    return {
        "name": "workspace",
        "ok": not missing,
        "missing": missing,
    }


def _check_database(memory_dir: Path) -> dict[str, Any]:
    """File-backed persistence (queue, audit, workforce JSON)."""
    return {
        "name": "database",
        "ok": memory_dir.is_dir(),
        "mode": "file-backed",
        "workforce_dir": (memory_dir / "workforce").is_dir(),
        "note": "Persistent volume recommended in cloud (GENESIS_MEMORY_DIR)",
    }


def _check_workforce() -> dict[str, Any]:
    from app.integration.genesis_ai_setup_service import GenesisAISetupService

    st = GenesisAISetupService().status()
    cloud = int(st.get("cloud_employees_ready") or 0)
    return {
        "name": "workforce",
        "ok": True,
        "tier": st.get("workforce_tier"),
        "cloud_employees_ready": cloud,
        "genesis_ready": bool(st.get("genesis_ready")),
    }


def _check_secrets() -> dict[str, Any]:
    load_local_env()
    configured = {key: bool(os.getenv(key, "").strip()) for key in _SECRET_KEYS}
    any_llm = any(
        configured.get(k)
        for k in (
            "GENESIS_GROQ_API_KEY",
            "GENESIS_GEMINI_API_KEY",
            "GENESIS_OPENROUTER_API_KEY",
            "GENESIS_LLM_API_KEY",
            "OPENAI_API_KEY",
        )
    )
    return {
        "name": "secrets",
        "ok": True,
        "llm_configured": any_llm,
        "keys_present": configured,
        "note": "Values never logged — booleans only",
    }


def _check_configuration() -> dict[str, Any]:
    cors = os.getenv("GENESIS_CORS_ORIGINS", "")
    public_url = os.getenv("GENESIS_PUBLIC_URL", "")
    memory = os.getenv("GENESIS_MEMORY_DIR", "")
    return {
        "name": "configuration",
        "ok": True,
        "genesis_env": genesis_env(),
        "cors_configured": bool(cors.strip()),
        "public_url_configured": bool(public_url.strip()),
        "memory_dir_env": bool(memory.strip()),
    }


def _check_farm_vault() -> dict[str, Any]:
    """Farm / exchange keys — booleans only, never log secret values."""
    load_local_env()
    toloka = bool(os.getenv("TOLOKA_API_TOKEN", "").strip())
    scale = bool(os.getenv("SCALE_API_KEY", "").strip())
    farm_live = (os.getenv("FARM_LIVE_MODE", "dry_run") or "dry_run").strip().lower()
    farm_exec = (os.getenv("FARM_EXECUTION_MODE", "local") or "local").strip().lower()
    pool = bool(os.getenv("FARM_WORKER_POOL_URL", "").strip())
    return {
        "name": "farm_vault",
        "ok": True,
        "env_file": "dashboard/backend/.env.local",
        "farm_live_mode": farm_live,
        "farm_execution_mode": farm_exec,
        "toloka_configured": toloka,
        "scale_configured": scale,
        "remote_pool_configured": pool,
        "note": "Toloka/Scale values never logged",
    }


def run_startup_validation(*, memory_dir: Path, repo_root: Path) -> dict[str, Any]:
    checks = [
        _check_memory(memory_dir),
        _check_workspace(repo_root),
        _check_database(memory_dir),
        _check_workforce(),
        _check_secrets(),
        _check_configuration(),
        _check_farm_vault(),
    ]
    failed = [c["name"] for c in checks if not c.get("ok")]
    report: dict[str, Any] = {
        "ok": len(failed) == 0,
        "genesis_env": genesis_env(),
        "checks": {c["name"]: c for c in checks},
        "warnings": [],
    }
    if not report["checks"]["secrets"].get("llm_configured"):
        report["warnings"].append(
            "No cloud LLM API key — Virtus Local active; set keys in host env for production workforce"
        )
    if is_cloud := bool(os.getenv("RENDER") or os.getenv("RAILWAY_ENVIRONMENT")):
        if not os.getenv("GENESIS_MEMORY_DIR"):
            report["warnings"].append(
                "Cloud host detected without GENESIS_MEMORY_DIR — data will not persist across restarts"
            )
        _ = is_cloud
    if failed:
        report["warnings"].append(f"Checks not fully OK: {', '.join(failed)}")
    return report


def log_startup_report(report: dict[str, Any]) -> None:
    lines = [f"Genesis startup validation — env={report.get('genesis_env')}"]
    for name, check in (report.get("checks") or {}).items():
        mark = "OK" if check.get("ok") else "WARN"
        lines.append(f"  [{mark}] {name}")
    for w in report.get("warnings") or []:
        lines.append(f"  [WARN] {w}")
    try:
        from app.integration.deployment_health import build_status_payload
        from pathlib import Path
        import os

        mem = os.getenv("GENESIS_MEMORY_DIR", "").strip()
        memory_dir = Path(mem).expanduser() if mem else Path(__file__).resolve().parents[2] / "memory"
        providers = (build_status_payload(memory_dir=memory_dir).get("checks") or {}).get(
            "llm_providers", {}
        )
        for pid, state in providers.items():
            if state == "ready":
                lines.append(f"  [OK] LLM provider {pid}: enabled")
            elif state == "not_configured":
                lines.append(f"  [SKIP] LLM provider {pid}: missing API key")
            else:
                lines.append(f"  [WARN] LLM provider {pid}: {state}")
    except Exception:
        pass
    farm = (report.get("checks") or {}).get("farm_vault") or {}
    if farm:
        lines.append(f"  [OK] farm_vault — file {farm.get('env_file')}")
        lines.append(
            f"       FARM_LIVE_MODE={farm.get('farm_live_mode')} "
            f"FARM_EXECUTION_MODE={farm.get('farm_execution_mode')}"
        )
        if farm.get("toloka_configured"):
            lines.append("  [OK] Toloka API token: present (Pipeline v2)")
        else:
            lines.append("  [WARN] TOLOKA_API_TOKEN is missing")
        if farm.get("scale_configured"):
            lines.append("  [OK] Scale API key: present")
        if farm.get("farm_execution_mode") == "remote" and not farm.get("remote_pool_configured"):
            lines.append("  [WARN] FARM_WORKER_POOL_URL missing — exchange OK, remote workers blocked")
    logger.info("\n".join(lines))
