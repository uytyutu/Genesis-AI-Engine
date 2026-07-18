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

_DEFAULT_DAILY_CAP = 40
_HARD_MAX_DAILY_CAP = 100
_DEFAULT_GLOBAL_DAILY_CAP = 120
_HARD_MAX_GLOBAL_DAILY_CAP = 500
_DEFAULT_MIN_INTERVAL_SEC = 90
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


def outreach_global_daily_cap() -> int:
    """Phase world ceiling across all markets (config default or env)."""
    from app.integration.outreach_market_config import default_global_daily_cap

    raw = os.getenv("GENESIS_OUTREACH_GLOBAL_DAILY_CAP", "").strip()
    try:
        n = int(raw) if raw else default_global_daily_cap()
    except ValueError:
        n = default_global_daily_cap()
    return max(1, min(_HARD_MAX_GLOBAL_DAILY_CAP, n))


def outreach_min_interval_sec() -> int:
    """Minimum seconds between successful sends (sniper pacing)."""
    from app.integration.outreach_market_config import default_min_interval_sec

    raw = os.getenv("GENESIS_OUTREACH_MIN_INTERVAL_SEC", "").strip()
    try:
        n = int(raw) if raw else default_min_interval_sec()
    except ValueError:
        n = default_min_interval_sec()
    return max(0, min(3600, n))


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
        empty = {
            "day": _today(),
            "regions": {},
            "domains": {},
            "markets": {},
            "last_send_at": None,
        }
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
        markets = data.get("markets")
        if not isinstance(regions, dict):
            regions = {}
        if not isinstance(domains, dict):
            domains = {}
        if not isinstance(markets, dict):
            markets = {}
        if not regions and domains:
            regions = {_DEFAULT_REGION: sum(int(v or 0) for v in domains.values())}
        return {
            "day": _today(),
            "regions": regions,
            "domains": domains,
            "markets": markets,
            "last_send_at": data.get("last_send_at"),
        }

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

    def _pacing_ok(self, data: dict[str, Any]) -> tuple[bool, str]:
        interval = outreach_min_interval_sec()
        if interval <= 0:
            return True, ""
        last = data.get("last_send_at")
        if not last:
            return True, ""
        try:
            last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return True, ""
        elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
        if elapsed < interval:
            wait = int(interval - elapsed)
            return False, f"min_interval:{wait}s"
        return True, ""

    def sent_today_market(self, market: str) -> int:
        data = self._load()
        return int((data.get("markets") or {}).get(str(market).upper(), 0) or 0)

    def can_send(
        self, from_addr: str, *, region: str | None = None, market: str | None = None
    ) -> tuple[bool, str]:
        from app.integration.outreach_market_config import market_daily_cap, market_send_pool

        domain = _domain_of(from_addr)
        if not domain:
            return False, "bad_from"
        data = self._load()
        total = sum(int(v or 0) for v in (data.get("markets") or {}).values())
        if not total:
            total = sum(int(v or 0) for v in (data.get("regions") or {}).values())
        gcap = outreach_global_daily_cap()
        if total >= gcap:
            return False, f"global_cap:{total}/{gcap}"
        ok_pace, pace_why = self._pacing_ok(data)
        if not ok_pace:
            return False, pace_why
        if market:
            mcode = str(market).upper()
            mused = int((data.get("markets") or {}).get(mcode, 0) or 0)
            mcap = market_daily_cap(mcode)
            if mused >= mcap:
                return False, f"market_cap:{mcode}:{mused}/{mcap}"
            reg = market_send_pool(mcode)
        else:
            reg = _normalize_region(region) if region else self._region_for_addr(from_addr)
        used = int((data.get("regions") or {}).get(reg, 0) or 0)
        cap = outreach_daily_cap()
        if used >= cap:
            return False, f"daily_cap:{reg}:{used}/{cap}"
        return True, ""

    def record_send(
        self, from_addr: str, *, region: str | None = None, market: str | None = None
    ) -> None:
        from app.integration.outreach_market_config import market_send_pool

        domain = _domain_of(from_addr)
        if not domain:
            return
        if market:
            mcode = str(market).upper()
            reg = market_send_pool(mcode)
        else:
            mcode = None
            reg = _normalize_region(region) if region else self._region_for_addr(from_addr)
        data = self._load()
        domains = dict(data.get("domains") or {})
        regions = dict(data.get("regions") or {})
        markets = dict(data.get("markets") or {})
        domains[domain] = int(domains.get(domain, 0) or 0) + 1
        regions[reg] = int(regions.get(reg, 0) or 0) + 1
        if mcode:
            markets[mcode] = int(markets.get(mcode, 0) or 0) + 1
        data["domains"] = domains
        data["regions"] = regions
        data["markets"] = markets
        data["day"] = _today()
        data["last_send_at"] = datetime.now(timezone.utc).isoformat()
        self._save(data)

    def pick_from_address(
        self, *, region: str | None = None, market: str | None = None
    ) -> tuple[str | None, dict[str, Any]]:
        """Least-used From under market + pool + global + pacing."""
        from app.integration.outreach_market_config import market_daily_cap, market_send_pool

        pool = configured_from_pool()
        cap = outreach_daily_cap()
        gcap = outreach_global_daily_cap()
        data = self._load()
        domains = dict(data.get("domains") or {})
        regions = dict(data.get("regions") or {})
        markets = dict(data.get("markets") or {})
        total = sum(int(v or 0) for v in markets.values()) or sum(
            int(v or 0) for v in regions.values()
        )
        if total >= gcap:
            return None, {
                "ok": False,
                "reason": f"global_cap:{total}/{gcap}",
                "global_daily_cap": gcap,
                "markets": markets,
                "pool_size": len(pool),
            }
        ok_pace, pace_why = self._pacing_ok(data)
        if not ok_pace:
            return None, {"ok": False, "reason": pace_why, "global_daily_cap": gcap}

        mcode = str(market).upper() if market else None
        if mcode:
            mused = int(markets.get(mcode, 0) or 0)
            mcap = market_daily_cap(mcode)
            if mused >= mcap:
                return None, {
                    "ok": False,
                    "reason": f"market_cap:{mcode}:{mused}/{mcap}",
                    "market": mcode,
                    "daily_cap": mcap,
                }
            want = market_send_pool(mcode)
        else:
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
                "global_daily_cap": gcap,
                "filter_region": want,
                "market": mcode,
            }

        available.sort(key=lambda t: (t[0], t[1], t[2], t[3]))
        region_used, domain_used, reg, domain, addr = available[0]
        return addr, {
            "ok": True,
            "from": addr,
            "domain": domain,
            "region": reg,
            "market": mcode,
            "used_today": domain_used,
            "region_used_today": region_used,
            "market_used_today": int(markets.get(mcode, 0) or 0) if mcode else None,
            "market_daily_cap": market_daily_cap(mcode) if mcode else None,
            "daily_cap": cap,
            "global_daily_cap": gcap,
            "sent_today_total": total,
            "min_interval_sec": outreach_min_interval_sec(),
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
        gcap = outreach_global_daily_cap()
        markets_cnt = dict(data.get("markets") or {})
        from app.integration.outreach_market_config import (
            enabled_markets_sum_caps,
            list_markets,
        )

        market_rows: list[dict[str, Any]] = []
        for m in list_markets():
            code = str(m.get("code") or "").upper()
            if not code:
                continue
            used = int(markets_cnt.get(code, 0) or 0)
            mcap = int(m.get("daily_cap") or 20)
            market_rows.append(
                {
                    "code": code,
                    "flag": m.get("flag") or "",
                    "name_ru": m.get("name_ru") or code,
                    "enabled": bool(m.get("enabled")),
                    "phase": int(m.get("phase") or 0),
                    "daily_cap": mcap,
                    "used_today": used if m.get("enabled") else 0,
                    "remaining": max(0, mcap - used) if m.get("enabled") else mcap,
                    "at_cap": bool(m.get("enabled")) and used >= mcap,
                    "language": m.get("language"),
                    "timezone": m.get("timezone"),
                    "legal_profile": m.get("legal_profile"),
                    "hubs": m.get("hubs") or [],
                    "send_pool": m.get("send_pool"),
                    "cap_rationale": m.get("cap_rationale") or "",
                }
            )

        sent_today_total = sum(int(r["used_today"]) for r in market_rows if r["enabled"])
        if not sent_today_total:
            sent_today_total = sum(int(r["used_today"]) for r in region_rows)
        pool_cap_total = min(enabled_markets_sum_caps() or gcap, gcap)
        remaining_today_total = max(0, gcap - sent_today_total)

        primary = next((r for r in market_rows if r["enabled"]), None) or (
            region_rows[0] if region_rows else None
        )
        return {
            "daily_cap": cap,
            "hard_max": _HARD_MAX_DAILY_CAP,
            "global_daily_cap": gcap,
            "min_interval_sec": outreach_min_interval_sec(),
            "day": data.get("day"),
            "domain_count": len(pool),
            "region_count": region_count,
            "pool_cap_total": pool_cap_total,
            "sent_today_total": sent_today_total,
            "remaining_today_total": remaining_today_total,
            "primary_used_today": int(primary["used_today"]) if primary else 0,
            "primary_remaining": int(primary.get("remaining") or 0) if primary else cap,
            "regions": region_rows,
            "markets": market_rows,
            "domains": per_domains,
            "phase_note_ru": (
                f"Конфиг outreach_markets.json · глобальный потолок {gcap}/день · "
                f"интервал ≥{outreach_min_interval_sec()}с. "
                "Новая страна = новая запись в JSON. Approve — предохранитель."
            ),
            "sniper_note_ru": (
                "Лимиты по странам — ops из конфига (не имитация закона). "
                "KPI: ответы → разговоры → заказы."
            ),
        }
