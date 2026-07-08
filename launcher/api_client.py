"""Fetch live data from Genesis backend for Launcher."""

from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import urlopen

API = "http://127.0.0.1:8000"


def _fetch(path: str, timeout: float = 4.0) -> dict | None:
    try:
        with urlopen(f"{API}{path}", timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, OSError, json.JSONDecodeError, TimeoutError):
        return None


def fetch_owner_dashboard() -> dict | None:
    return _fetch("/api/owner/dashboard")


def fetch_mission_control(timeout: float = 8.0) -> dict | None:
    return _fetch("/api/owner/mission-control", timeout=timeout)


def fetch_system_check() -> dict | None:
    return _fetch("/api/owner/system-check")
