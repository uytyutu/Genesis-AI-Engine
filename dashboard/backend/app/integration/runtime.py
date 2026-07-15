"""Process uptime — avoids circular imports between context and mission_control."""

from __future__ import annotations

import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

RUNTIME_IDENTITY = "genesis-backend-v1"

_server_started_at: datetime | None = None
_build_time: str | None = None
_git_commit: str | None = None
_brain_paused: bool = False
_vector_ready_cache: tuple[float, bool, bool] | None = None
_VECTOR_READY_TTL_SEC = 10.0


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _resolve_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(_repo_root()), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            commit = result.stdout.strip()
            if commit:
                return commit
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def mark_server_started() -> None:
    global _server_started_at, _build_time, _git_commit
    now = datetime.now(timezone.utc)
    _server_started_at = now
    _build_time = now.isoformat()
    _git_commit = _resolve_git_commit()


def get_server_started_at() -> datetime:
    global _server_started_at
    if _server_started_at is None:
        mark_server_started()
    return _server_started_at


def set_brain_paused(value: bool) -> None:
    global _brain_paused
    _brain_paused = value


def is_brain_paused() -> bool:
    return _brain_paused


def _cloud_llm_configured() -> bool:
    """Fast path for /api/status — no provider probes on every launcher poll."""
    from app.env_loader import load_local_env

    load_local_env()
    keys = (
        "GENESIS_GROQ_API_KEY",
        "GENESIS_GEMINI_API_KEY",
        "GENESIS_OPENROUTER_API_KEY",
        "GENESIS_LLM_API_KEY",
        "GOOGLE_API_KEY",
    )
    return any(os.getenv(key, "").strip() for key in keys)


def _resolve_vector_chat_ready() -> tuple[bool, bool]:
    """Cached Vector readiness — launcher polls /api/status frequently."""
    global _vector_ready_cache
    now = time.monotonic()
    if _vector_ready_cache and now - _vector_ready_cache[0] < _VECTOR_READY_TTL_SEC:
        return _vector_ready_cache[1], _vector_ready_cache[2]

    vector_chat_ready = False
    vector_warmup_skipped = False
    try:
        from app.integration.ollama_warmup import warmup_status

        ws = warmup_status()
        vector_warmup_skipped = bool(ws.get("skipped"))
        vector_chat_ready = bool(ws.get("ready"))
        if not vector_chat_ready and (_cloud_llm_configured() or vector_warmup_skipped):
            vector_chat_ready = True
    except Exception:
        pass

    _vector_ready_cache = (now, vector_chat_ready, vector_warmup_skipped)
    return vector_chat_ready, vector_warmup_skipped


def light_system_status() -> dict:
    """Fast /api/status payload — no Brain/Kernel init."""
    started = get_server_started_at()
    uptime = max(0.0, (datetime.now(timezone.utc) - started).total_seconds())
    if _git_commit is None:
        mark_server_started()

    vector_chat_ready, vector_warmup_skipped = _resolve_vector_chat_ready()

    return {
        "name": "Virtus Core",
        "version": "0.2.0",
        "phase": "Integration Layer v0.1 (live)",
        "paused": is_brain_paused(),
        "uptime_sec": round(uptime, 1),
        "git_commit": _git_commit or "unknown",
        "build_time": _build_time or started.isoformat(),
        "process_started": started.isoformat(),
        "runtime_identity": RUNTIME_IDENTITY,
        "backend_pid": os.getpid(),
        "vector_chat_ready": vector_chat_ready,
        "vector_warmup_skipped": vector_warmup_skipped,
    }
