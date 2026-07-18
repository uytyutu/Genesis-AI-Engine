"""Sniper outreach daily caps + multi-domain from-address rotation."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Safe sniper defaults (DE B2B). Hard ceiling avoids spam-scale misconfig.
_DEFAULT_DAILY_CAP = 10
_HARD_MAX_DAILY_CAP = 70
_DEFAULT_FROM_NAME = "Virtus Core"


def outreach_daily_cap() -> int:
    raw = os.getenv("GENESIS_OUTREACH_DAILY_CAP", "").strip()
    try:
        n = int(raw) if raw else _DEFAULT_DAILY_CAP
    except ValueError:
        n = _DEFAULT_DAILY_CAP
    return max(1, min(_HARD_MAX_DAILY_CAP, n))


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _domain_of(from_addr: str) -> str:
    # "Name <email@domain.de>" or bare email
    m = re.search(r"[\w.+-]+@([\w.-]+\.\w+)", from_addr or "", re.I)
    if m:
        return m.group(1).lower()
    try:
        host = urlparse(f"mailto:{from_addr}").path.split("@")[-1]
        return host.lower()
    except Exception:
        return ""


def configured_from_addresses() -> list[str]:
    """Pool of From addresses. Multi-domain via GENESIS_OUTREACH_FROM_DOMAINS.

    Format (comma-separated):
      Virtus Core <hello@ram-service.de>, Virtus <hi@ram-solutions.de>
    Falls back to GENESIS_EMAIL_FROM.
    """
    raw = os.getenv("GENESIS_OUTREACH_FROM_DOMAINS", "").strip()
    pool: list[str] = []
    if raw:
        for part in raw.split(","):
            addr = part.strip()
            if addr and "@" in addr:
                pool.append(addr)
    if not pool:
        single = os.getenv("GENESIS_EMAIL_FROM", "").strip()
        if single:
            pool.append(single)
    return pool


class OutreachSendQuota:
    """Per-domain daily counters stored under memory/outreach_send_quota.json."""

    def __init__(self, memory_dir: Path | None) -> None:
        self._memory = memory_dir

    def _path(self) -> Path | None:
        if not self._memory:
            return None
        return Path(self._memory) / "outreach_send_quota.json"

    def _load(self) -> dict[str, Any]:
        path = self._path()
        if not path or not path.is_file():
            return {"day": _today(), "domains": {}}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"day": _today(), "domains": {}}
        if not isinstance(data, dict):
            return {"day": _today(), "domains": {}}
        if data.get("day") != _today():
            return {"day": _today(), "domains": {}}
        domains = data.get("domains")
        if not isinstance(domains, dict):
            domains = {}
        return {"day": _today(), "domains": domains}

    def _save(self, data: dict[str, Any]) -> None:
        path = self._path()
        if not path:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def sent_today(self, domain: str | None = None) -> int:
        data = self._load()
        domains: dict = data.get("domains") or {}
        if domain:
            return int(domains.get(domain.lower(), 0) or 0)
        return sum(int(v or 0) for v in domains.values())

    def can_send(self, from_addr: str) -> tuple[bool, str]:
        domain = _domain_of(from_addr)
        if not domain:
            return False, "bad_from"
        used = self.sent_today(domain)
        cap = outreach_daily_cap()
        if used >= cap:
            return False, f"daily_cap:{domain}:{used}/{cap}"
        return True, ""

    def record_send(self, from_addr: str) -> None:
        domain = _domain_of(from_addr)
        if not domain:
            return
        data = self._load()
        domains = dict(data.get("domains") or {})
        domains[domain] = int(domains.get(domain, 0) or 0) + 1
        data["domains"] = domains
        data["day"] = _today()
        self._save(data)

    def pick_from_address(self) -> tuple[str | None, dict[str, Any]]:
        """Least-used domain under daily cap (round-robin by count)."""
        pool = configured_from_addresses()
        cap = outreach_daily_cap()
        data = self._load()
        domains = dict(data.get("domains") or {})
        available: list[tuple[int, str, str]] = []
        for addr in pool:
            domain = _domain_of(addr)
            used = int(domains.get(domain, 0) or 0)
            if used < cap:
                available.append((used, domain, addr))
        if not available:
            return None, {
                "ok": False,
                "reason": "all_domains_at_cap",
                "daily_cap": cap,
                "domains": domains,
                "pool_size": len(pool),
            }
        available.sort(key=lambda t: (t[0], t[1]))
        _used, domain, addr = available[0]
        return addr, {
            "ok": True,
            "from": addr,
            "domain": domain,
            "used_today": _used,
            "daily_cap": cap,
            "pool_size": len(pool),
        }

    def health(self) -> dict[str, Any]:
        pool = configured_from_addresses()
        cap = outreach_daily_cap()
        data = self._load()
        domains = dict(data.get("domains") or {})
        per = []
        for addr in pool:
            domain = _domain_of(addr)
            used = int(domains.get(domain, 0) or 0)
            per.append(
                {
                    "from": addr,
                    "domain": domain,
                    "used_today": used,
                    "remaining": max(0, cap - used),
                    "at_cap": used >= cap,
                }
            )
        return {
            "daily_cap": cap,
            "hard_max": _HARD_MAX_DAILY_CAP,
            "day": data.get("day"),
            "domains": per,
            "sniper_note_ru": (
                "Снайпер: 5–10 писем/день на старт, макс. 50–70 на домен. "
                "Масштаб — через дополнительные домены (GENESIS_OUTREACH_FROM_DOMAINS), не через спам."
            ),
        }
