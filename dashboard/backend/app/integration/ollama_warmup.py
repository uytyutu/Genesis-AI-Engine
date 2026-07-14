"""Warm local Ollama at boot — first /site chat must not pay cold-load latency."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

logger = logging.getLogger("genesis")

_warmup_done = False
_warmup_skipped = False
_warmup_started_at: float | None = None
_warmup_elapsed_sec: float | None = None


def warmup_status() -> dict[str, object]:
    return {
        "ready": _warmup_done,
        "skipped": _warmup_skipped,
        "elapsed_sec": _warmup_elapsed_sec,
    }


def warm_ollama_if_available() -> bool:
    """Block until the real fast-lane chat path has hit Ollama once."""
    global _warmup_done, _warmup_skipped, _warmup_started_at, _warmup_elapsed_sec

    if _warmup_done or _warmup_skipped:
        return _warmup_done

    if os.getenv("GENESIS_OLLAMA_WARMUP", "1").strip() == "0":
        _warmup_skipped = True
        logger.info("Ollama warmup disabled (GENESIS_OLLAMA_WARMUP=0)")
        return False

    _warmup_started_at = time.perf_counter()
    wait_sec = float(os.getenv("GENESIS_OLLAMA_WARMUP_WAIT_SEC", "90"))

    try:
        from app.integration.genesis_brain.providers import build_provider_registry

        deadline = time.perf_counter() + wait_sec
        ollama = None
        while time.perf_counter() < deadline:
            ollama = build_provider_registry().get("ollama")
            if ollama is not None and ollama.available():
                break
            time.sleep(1.5)

        if ollama is None or not ollama.available():
            _warmup_skipped = True
            logger.info("Ollama warmup skipped — local model offline after %.0fs wait", wait_sec)
            return False

        # Use the same public fast-lane stack as /site — not a toy /api/generate prompt.
        from app.integration.genesis_ai_service import GenesisAIService

        mem = Path(__file__).resolve().parents[1] / "memory"
        svc = GenesisAIService([], memory_dir=mem)
        saw_token = False
        for event in svc.chat_stream(
            "ok",
            visitor_id="__ollama_warmup__",
            history=[],
            context={"ui_locale": "ru", "assistant_locale": "ru"},
        ):
            if event.get("type") == "token":
                saw_token = True
                break
            if event.get("type") == "done":
                saw_token = bool((event.get("answer") or "").strip())
                break

        if not saw_token:
            _warmup_skipped = True
            logger.warning("Ollama warmup produced no tokens")
            return False

        _warmup_elapsed_sec = round(time.perf_counter() - _warmup_started_at, 2)
        _warmup_done = True
        logger.info("Ollama fast-lane warmup complete (%.1fs)", _warmup_elapsed_sec or 0)
        return True
    except Exception as exc:
        _warmup_skipped = True
        _warmup_elapsed_sec = (
            round(time.perf_counter() - _warmup_started_at, 2) if _warmup_started_at else None
        )
        logger.warning("Ollama warmup skipped: %s", exc)
        return False
