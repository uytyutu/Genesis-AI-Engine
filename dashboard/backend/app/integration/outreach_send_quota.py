"""Regional outreach caps + From-address rotation (DE / CIS / US).

Planning model (not spam): each market region has its own daily pool
(GENESIS_OUTREACH_DAILY_CAP, hard max 100). Scale = more regions with
their own warmed domains — not raising one domain past the ceiling.

From pool format (GENESIS_OUTREACH_FROM_DOMAINS), comma-separated:
  de:Virtus Core <hello@de-domain.de>,
  cis:Virtus <hi@cis-domain.com>,
  us:Virtus <hello@us-domain.com>

Untagged addresses default to region ``de`` (backward compatible).
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_DEFAULT_DAILY_CAP = 10
_HARD_MAX_DAILY_CAP = 100
_DEFAULT_REGION = "de"

# Known market regions for CEO panel (order fixed).
OUTREACH_REGIONS: tuple[str, ...] = ("de", "cis", "us")
_REGION_LABEL_RU: dict[str, str] = {
    "de": "Германия",
    "cis": "СНГ",
    "us": "Америка",
}


def outreach_daily_cap() -> int:
    """Per-region daily send cap (shared by all From domains in that region)."""
    raw = os.getenv("GENESIS_OUTREACH_DAILY_CAP", "").strip()
    try:
        n = int(raw) if raw else _DEFAULT_DAILY_CAP
    except ValueError:
        n = _DEFAULT_DAILY_CAP
    return max(1, min(_HARD_MAX_DAILY_CAP, n))


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _domain_of(from_addr: str) -> str:
    m = re.search(r"[\w.+-]+@([\w.-]+\.\w+)", from_addr or "", re.I)
    if m:
        return m.group(1).lower()
    try:
        host = urlparse(f"mailto:{from_addr}").path.split("@")[-1]
        return host.lower()
    except Exception:
        return ""


def _normalize_region(raw: str | None) -> str:
    code = (raw or "").strip().lower()
    if code in ("de", "cis", "us"):
        return code
    # Aliases
    if code in ("germany", "de-de", "deu"):
        return "de"
    if code in ("sng", "ua", "ru", "kz", "by", "cis-eu"):
        return "cis"
    if code in ("usa", "america", "en-us", "na"):
        return "us"
    return _DEFAULT_REGION


def parse_from_entry(part: str) -> tuple[str, str] | None:
    """Parse ``region:Name <email@x>`` or bare ``Name <email@x>`` → (region, addr)."""
    raw = (part or "").strip()
    if not raw or "@" not in raw:
        return None
    region = _DEFAULT_REGION
    addr = raw
    if ":" in raw:
        # region:rest — only if left side looks like a region tag (no @)
        left, right = raw.split(":", 1)
        if "@" not in left and left.strip():
            region = _normalize_region(left)
            addr = right.strip()
    if not addr or "@" not in addr:
        return None
    return region, addr


def configured_from_pool() -> list[dict[str, str]]:
    """List of {region, from, domain} from env."""
    raw = os.getenv("GENESIS_OUTREACH_FROM_DOMAINS", "").strip()
    pool: list[dict[str, str]] = []
    if raw:
        for part in raw.split(","):
            parsed = parse_from_entry(part)
            if not parsed:
                continue
            region, addr = parsed
            domain = _domain_of(addr)
            if not domain:
                continue
            pool.append({"region": region, "from": addr, "domain": domain})
    if not pool:
        single = os.getenv("GENESIS_EMAIL_FROM", "").strip()
        if single and "@" in single:
            domain = _domain_of(single)
            if domain:
                pool.append(
                    {"region": _DEFAULT_REGION, "from": single, "domain": domain}
                )
    return pool


def configured_from_addresses() -> list[str]:
    """Bare From strings (compat)."""
    return [p["from"] for p in configured_from_pool()]


def region_label_ru(code: str) -> str:
    return _REGION_LABEL_RU.get(code, code.upper())


class OutreachSendQuota:
    """Per-region daily counters (+ per-domain usage for rotation)."""

    def __init__(self, memory_dir: Path | None) -> None:
        self._memory = memory_dir

    def _path(self) -> Path | None:
        if not self._memory:
            return None
        return Path(self._memory) / "outreach_send_quota.json"

    def _load(self) -> dict[str, Any]:
        path = self._path()
        empty = {"day": _today(), "regions": {}, "domains": {}}
        if not path or not path.is_file():
            return empty
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return empty
        if not isinstance(data, dict):
            return empty
        if data.get("day") != _today():
            return empty
        regions = data.get("regions")
        domains = data.get("domains")
        if not isinstance(regions, dict):
            regions = {}
        if not isinstance(domains, dict):
            domains = {}
        # Legacy files: only domains — fold into default region for today.
        if not regions and domains:
            regions = {_DEFAULT_REGION: sum(int(v or 0) for v in domains.values())}
        return {"day": _today(), "regions": regions, "domains": domains}

    def _save(self, data: dict[str, Any]) -> None:
        path = self._path()
        if not path:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _region_for_addr(self, from_addr: str, pool: list[dict[str, str]] | None = None) -> str:
        pool = pool if pool is not None else configured_from_pool()
        domain = _domain_of(from_addr)
        for item in pool:
            if item["from"] == from_addr or item["domain"] == domain:
                return item["region"]
        return _DEFAULT_REGION

    def sent_today(self, domain: str | None = None) -> int:
        data = self._load()
        if domain:
            return int((data.get("domains") or {}).get(domain.lower(), 0) or 0)
        return sum(int(v or 0) for v in (data.get("regions") or {}).values())

    def sent_today_region(self, region: str) -> int:
        data = self._load()
        return int((data.get("regions") or {}).get(_normalize_region(region), 0) or 0)

    def can_send(self, from_addr: str, *, region: str | None = None) -> tuple[bool, str]:
        domain = _domain_of(from_addr)
        if not domain:
            return False, "bad_from"
        reg = _normalize_region(region) if region else self._region_for_addr(from_addr)
        used = self.sent_today_region(reg)
        cap = outreach_daily_cap()
        if used >= cap:
            return False, f"daily_cap:{reg}:{used}/{cap}"
        return True, ""

    def record_send(self, from_addr: str, *, region: str | None = None) -> None:
        domain = _domain_of(from_addr)
        if not domain:
            return
        reg = _normalize_region(region) if region else self._region_for_addr(from_addr)
        data = self._load()
        domains = dict(data.get("domains") or {})
        regions = dict(data.get("regions") or {})
        domains[domain] = int(domains.get(domain, 0) or 0) + 1
        regions[reg] = int(regions.get(reg, 0) or 0) + 1
        data["domains"] = domains
        data["regions"] = regions
        data["day"] = _today()
        self._save(data)

    def pick_from_address(
        self, *, region: str | None = None
    ) -> tuple[str | None, dict[str, Any]]:
        """Least-used From under its region cap. Optional region filter (de|cis|us)."""
        pool = configured_from_pool()
        cap = outreach_daily_cap()
        data = self._load()
        domains = dict(data.get("domains") or {})
        regions = dict(data.get("regions") or {})
        want = _normalize_region(region) if region else None

        available: list[tuple[int, int, str, str, str]] = []
        for item in pool:
            reg = item["region"]
            if want and reg != want:
                continue
            domain = item["domain"]
            region_used = int(regions.get(reg, 0) or 0)
            if region_used >= cap:
                continue
            domain_used = int(domains.get(domain, 0) or 0)
            available.append((region_used, domain_used, reg, domain, item["from"]))

        if not available:
            return None, {
                "ok": False,
                "reason": "all_regions_at_cap" if not want else f"region_at_cap:{want}",
                "daily_cap": cap,
                "regions": regions,
                "pool_size": len(pool),
                "filter_region": want,
            }

        # Prefer colder regions, then colder domains (fair share across markets).
        available.sort(key=lambda t: (t[0], t[1], t[2], t[3]))
        region_used, domain_used, reg, domain, addr = available[0]
        return addr, {
            "ok": True,
            "from": addr,
            "domain": domain,
            "region": reg,
            "used_today": domain_used,
            "region_used_today": region_used,
            "daily_cap": cap,
            "pool_size": len(pool),
        }

    def health(self) -> dict[str, Any]:
        pool = configured_from_pool()
        cap = outreach_daily_cap()
        data = self._load()
        domains_cnt = dict(data.get("domains") or {})
        regions_cnt = dict(data.get("regions") or {})

        # Regions that have at least one From configured.
        configured_regions = sorted({p["region"] for p in pool}, key=lambda r: (
            OUTREACH_REGIONS.index(r) if r in OUTREACH_REGIONS else 99,
            r,
        ))

        region_rows: list[dict[str, Any]] = []
        for reg in configured_regions or ([_DEFAULT_REGION] if domains_cnt else []):
            used = int(regions_cnt.get(reg, 0) or 0)
            # If legacy-only domains and no region keys yet, sum domains for default.
            if used == 0 and reg == _DEFAULT_REGION and not regions_cnt and domains_cnt:
                used = sum(int(v or 0) for v in domains_cnt.values())
            addrs = [p for p in pool if p["region"] == reg]
            domain_rows = []
            for p in addrs:
                d_used = int(domains_cnt.get(p["domain"], 0) or 0)
                domain_rows.append(
                    {
                        "from": p["from"],
                        "domain": p["domain"],
                        "used_today": d_used,
                        "region": reg,
                    }
                )
            region_rows.append(
                {
                    "region": reg,
                    "label_ru": region_label_ru(reg),
                    "used_today": used,
                    "remaining": max(0, cap - used),
                    "at_cap": used >= cap,
                    "daily_cap": cap,
                    "domains": domain_rows,
                }
            )

        # Flat domain list for older UI bits.
        per_domains = []
        for p in pool:
            reg = p["region"]
            used = int(domains_cnt.get(p["domain"], 0) or 0)
            region_used = int(regions_cnt.get(reg, 0) or 0)
            per_domains.append(
                {
                    "from": p["from"],
                    "domain": p["domain"],
                    "region": reg,
                    "used_today": used,
                    "remaining": max(0, cap - region_used),
                    "at_cap": region_used >= cap,
                }
            )

        region_count = len(region_rows)
        pool_cap_total = cap * max(region_count, 1) if region_rows else cap
        sent_today_total = sum(int(r["used_today"]) for r in region_rows)
        remaining_today_total = sum(int(r["remaining"]) for r in region_rows) if region_rows else cap

        primary = region_rows[0] if region_rows else None
        return {
            "daily_cap": cap,
            "hard_max": _HARD_MAX_DAILY_CAP,
            "day": data.get("day"),
            "domain_count": len(pool),
            "region_count": region_count,
            "pool_cap_total": pool_cap_total,
            "sent_today_total": sent_today_total,
            "remaining_today_total": remaining_today_total,
            "primary_used_today": int(primary["used_today"]) if primary else 0,
            "primary_remaining": int(primary["remaining"]) if primary else cap,
            "regions": region_rows,
            "domains": per_domains,
            "sniper_note_ru": (
                "По 100 писем/день на рынок после прогрева: Германия · СНГ · Америка "
                "(отдельные From-домены с тегом de:/cis:/us:). "
                "Это не спам — три независимых пула. Warm-up каждого домена обязателен."
            ),
        }
