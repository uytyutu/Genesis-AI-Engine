"""Per-API-key rate limiter (in-memory + optional persist window)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque

_DEFAULT_PER_MIN = 100
_lock = Lock()
_buckets: dict[str, Deque[float]] = defaultdict(deque)


def allow_request(key_id: str, *, limit_per_min: int | None = None) -> tuple[bool, int]:
    """Return (allowed, remaining). Sliding 60s window."""
    limit = max(1, int(limit_per_min or _DEFAULT_PER_MIN))
    now = time.time()
    window = 60.0
    with _lock:
        q = _buckets[key_id]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            return False, 0
        q.append(now)
        return True, max(0, limit - len(q))
