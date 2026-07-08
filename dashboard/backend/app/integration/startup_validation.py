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


def run_startup_validation(*, memory_dir: Path, repo_root: Path) -> dict[str, Any]:
    checks = [
        _check_memory(memory_dir),
        _check_workspace(repo_root),
        _check_database(memory_dir),
        _check_workforce(),
        _check_secrets(),
        _check_configuration(),
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
            "No cloud LLM API key — Genesis Local active; set keys in host env for production workforce"
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
    logger.info("\n".join(lines))
