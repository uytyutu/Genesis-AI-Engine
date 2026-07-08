"""Deployment /health and /status payloads (cloud probes)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.config import genesis_env
from app.env_loader import load_local_env
from app.integration.genesis_brain.brain import BRAIN_VERSION
from app.integration.runtime import light_system_status


def build_health_payload() -> dict[str, Any]:
    return {"status": "ok", "service": "genesis-api"}


def _llm_provider_status() -> dict[str, Any]:
    load_local_env()
    from app.integration.genesis_brain.providers import build_provider_registry

    registry = build_provider_registry()
    providers: dict[str, str] = {}
    for pid in ("groq", "gemini", "openrouter", "ollama", "openai", "genesis-local"):
        try:
            p = registry.get(pid)
            providers[pid] = "ready" if p and p.available() else "not_configured"
        except Exception:
            providers[pid] = "offline"
    return providers


def _genesis_mind_status() -> dict[str, Any]:
    try:
        from app.integration.genesis_brain.brain import BRAIN_VERSION as bv

        return {"ok": True, "brain_version": bv, "pipeline": "genesis-mind-v3"}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}


def _workforce_status() -> dict[str, Any]:
    from app.integration.genesis_ai_setup_service import GenesisAISetupService

    st = GenesisAISetupService().status()
    return {
        "ok": True,
        "tier": st.get("workforce_tier"),
        "cloud_employees_ready": st.get("cloud_employees_ready"),
        "llm_configured": st.get("llm_configured"),
    }


def _memory_status(memory_dir: Path) -> dict[str, Any]:
    ok = memory_dir.is_dir()
    writable = False
    if ok:
        try:
            probe = memory_dir / ".health_probe"
            probe.write_text("1", encoding="utf-8")
            probe.unlink(missing_ok=True)
            writable = True
        except OSError:
            pass
    return {"ok": ok and writable, "path": str(memory_dir), "writable": writable}


def _database_status(memory_dir: Path) -> dict[str, Any]:
    wf = memory_dir / "workforce"
    return {
        "ok": memory_dir.is_dir(),
        "mode": "file-backed",
        "workforce_store": wf.is_dir(),
    }


def build_status_payload(*, memory_dir: Path) -> dict[str, Any]:
    base = light_system_status()
    checks = {
        "backend": {"ok": True, "paused": base.get("paused", False)},
        "genesis_mind": _genesis_mind_status(),
        "workforce": _workforce_status(),
        "database": _database_status(memory_dir),
        "memory": _memory_status(memory_dir),
        "llm_providers": _llm_provider_status(),
    }
    degraded = any(
        not (c.get("ok") if isinstance(c, dict) else True)
        for c in checks.values()
        if isinstance(c, dict) and "ok" in c
    )
    return {
        "status": "degraded" if degraded else "ok",
        "genesis_env": genesis_env(),
        "version": base.get("version", "0.2.0"),
        "brain_version": BRAIN_VERSION,
        "uptime_sec": base.get("uptime_sec"),
        "public_url": os.getenv("GENESIS_PUBLIC_URL", ""),
        "checks": checks,
    }
