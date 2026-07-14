"""Circuit breaker for exchange APIs (Toloka, Scale) — Safe Mode after repeated failures."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

DEFAULT_FAILURE_THRESHOLD = 5
DEFAULT_OPEN_SECONDS = 900.0  # 15 min


class ExchangeCircuitBreaker:
    """Opens after N consecutive API failures — stops spamming 403/404/5xx."""

    def __init__(
        self,
        memory_dir: Path,
        *,
        exchange_id: str = "toloka",
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
        open_seconds: float = DEFAULT_OPEN_SECONDS,
    ) -> None:
        self._path = memory_dir / "exchange_circuit_breaker.json"
        self._exchange_id = exchange_id
        self._threshold = max(1, int(failure_threshold))
        self._open_seconds = float(open_seconds)

    def _load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return {"exchanges": {}}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"exchanges": {}}
        except (json.JSONDecodeError, OSError):
            return {"exchanges": {}}

    def _save(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _row(self, data: dict[str, Any]) -> dict[str, Any]:
        exchanges = data.setdefault("exchanges", {})
        row = exchanges.get(self._exchange_id)
        if not isinstance(row, dict):
            row = {}
            exchanges[self._exchange_id] = row
        return row

    def is_open(self) -> bool:
        row = self._row(self._load())
        until = float(row.get("open_until") or 0)
        if until > time.time():
            return True
        return False

    def safe_mode(self) -> bool:
        return self.is_open()

    def record_success(self) -> None:
        data = self._load()
        row = self._row(data)
        row["consecutive_failures"] = 0
        row.pop("open_until", None)
        row.pop("safe_mode_reason", None)
        row["last_success_at"] = time.time()
        self._save(data)

    def record_failure(self, *, error: str = "", http_status: int | None = None) -> bool:
        """Returns True if breaker just opened (entered Safe Mode)."""
        data = self._load()
        row = self._row(data)
        fails = int(row.get("consecutive_failures") or 0) + 1
        row["consecutive_failures"] = fails
        row["last_failure_at"] = time.time()
        row["last_error"] = (error or "")[:240]
        if http_status is not None:
            row["last_http_status"] = http_status
        opened = False
        if fails >= self._threshold:
            row["open_until"] = time.time() + self._open_seconds
            row["safe_mode_reason"] = f"{fails} ошибок подряд — Safe Mode {int(self._open_seconds // 60)} мин"
            opened = True
        self._save(data)
        return opened

    def snapshot(self) -> dict[str, Any]:
        data = self._load()
        row = self._row(data)
        until = float(row.get("open_until") or 0)
        now = time.time()
        return {
            "exchange_id": self._exchange_id,
            "safe_mode": until > now,
            "is_open": until > now,
            "consecutive_failures": int(row.get("consecutive_failures") or 0),
            "failure_threshold": self._threshold,
            "seconds_remaining": max(0, int(until - now)) if until > now else 0,
            "safe_mode_reason": row.get("safe_mode_reason"),
            "last_error": row.get("last_error"),
            "last_http_status": row.get("last_http_status"),
        }
