"""Per-provider circuit breaker — fast failover without long waits."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_DEFAULT_OPEN_SEC = 300.0  # 5 min after rate limit
_ERROR_OPEN_SEC = 120.0


class CircuitBreaker:
    """Track temporarily unavailable providers (429, 402, timeout)."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        root = memory_dir or Path(__file__).resolve().parents[4] / "memory"
        self._path = root / "workforce" / "circuit_breaker.json"
        self._state: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.is_file():
            self._state = {"providers": {}}
            return
        try:
            self._state = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self._state = {"providers": {}}

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(self._state, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def is_open(self, provider_id: str) -> bool:
        row = (self._state.get("providers") or {}).get(provider_id) or {}
        until = float(row.get("open_until") or 0)
        return until > time.time()

    def record_success(self, provider_id: str) -> None:
        providers = dict(self._state.get("providers") or {})
        providers.pop(provider_id, None)
        self._state["providers"] = providers
        self._save()

    def record_failure(self, provider_id: str, *, error: str = "") -> None:
        text = (error or "").lower()
        if "429" in text or "rate" in text:
            ttl = _DEFAULT_OPEN_SEC
            reason = "rate_limited"
        elif "402" in text or "payment" in text:
            ttl = _DEFAULT_OPEN_SEC * 2
            reason = "payment_required"
        elif "401" in text or "403" in text or "invalid" in text:
            ttl = _DEFAULT_OPEN_SEC * 6
            reason = "auth_failed"
        else:
            ttl = _ERROR_OPEN_SEC
            reason = "error"
        providers = dict(self._state.get("providers") or {})
        providers[provider_id] = {
            "open_until": time.time() + ttl,
            "reason": reason,
            "last_error": (error or "")[:200],
            "at": time.time(),
        }
        self._state["providers"] = providers
        self._save()

    def snapshot(self) -> dict[str, Any]:
        now = time.time()
        out: dict[str, Any] = {}
        for pid, row in (self._state.get("providers") or {}).items():
            until = float(row.get("open_until") or 0)
            out[pid] = {
                **row,
                "is_open": until > now,
                "seconds_remaining": max(0, int(until - now)),
            }
        return out
