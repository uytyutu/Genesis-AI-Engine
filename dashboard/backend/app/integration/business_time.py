"""Business Time — market local clock helpers (Lead Engine).

CEO (2026-07-30): Outreach strategy is 24/7.
Hunt / qualify / draft / send are never gated by weekday 09:00–18:00.
GENESIS_OUTREACH_BUSINESS_HOURS is ignored (legacy env kept for docs only).
"""

from __future__ import annotations

from datetime import datetime, timedelta, time, timezone
from typing import Any

# Legacy window constants (unused for gating; kept for status display history)
BUSINESS_OPEN = time(9, 0)
BUSINESS_CLOSE = time(18, 0)

# Fixed UTC offsets when zoneinfo/tzdata unavailable (Windows). Approximate
# standard winter offsets; summer DST +1h applied roughly Mar–Oct for EU/US.
_OFFSET_HOURS: dict[str, tuple[int, int]] = {
    # code: (winter_utc_offset, summer_utc_offset)
    "DE": (1, 2),
    "AT": (1, 2),
    "CH": (1, 2),
    "FR": (1, 2),
    "NL": (1, 2),
    "BE": (1, 2),
    "IT": (1, 2),
    "ES": (1, 2),
    "PL": (1, 2),
    "GB": (0, 1),
    "UK": (0, 1),
    "IE": (0, 1),
    "US": (-5, -4),  # New York
    "CA": (-5, -4),  # Toronto
    # APAC — fixed standard offsets (DST ignored; zoneinfo preferred when available)
    "AU": (10, 10),  # Sydney AEST
    "NZ": (12, 12),  # Auckland NZST
    "JP": (9, 9),  # Tokyo JST
    "KR": (9, 9),  # Seoul KST
    "SG": (8, 8),  # Singapore
}


def timezone_for_market(market_code: str | None) -> str:
    code = (market_code or "DE").strip().upper() or "DE"
    try:
        from app.integration.country_profiles import COUNTRY_PROFILES

        profile = COUNTRY_PROFILES.get(code) or {}
        tz = str(profile.get("timezone") or "").strip()
        if tz:
            return tz
    except Exception:
        pass
    fallbacks = {
        "DE": "Europe/Berlin",
        "AT": "Europe/Vienna",
        "CH": "Europe/Zurich",
        "GB": "Europe/London",
        "UK": "Europe/London",
        "US": "America/New_York",
        "CA": "America/Toronto",
        "AU": "Australia/Sydney",
        "NZ": "Pacific/Auckland",
        "JP": "Asia/Tokyo",
        "KR": "Asia/Seoul",
        "SG": "Asia/Singapore",
        "FR": "Europe/Paris",
        "NL": "Europe/Amsterdam",
    }
    return fallbacks.get(code, "Europe/Berlin")


def _eu_us_dst(utc: datetime) -> bool:
    """Rough DST: last Sunday Mar ≈ day 85–100 through late Oct."""
    # Simple: April–October inclusive as DST for northern hemisphere
    return 3 < utc.month < 11 or (utc.month == 3 and utc.day >= 25) or (
        utc.month == 10 and utc.day < 25
    )


def _offset_local(market_code: str | None, now_utc: datetime) -> datetime:
    code = (market_code or "DE").strip().upper() or "DE"
    winter, summer = _OFFSET_HOURS.get(code, (1, 2))
    hours = summer if _eu_us_dst(now_utc) else winter
    return (now_utc if now_utc.tzinfo else now_utc.replace(tzinfo=timezone.utc)) + timedelta(
        hours=hours
    )


def local_now(market_code: str | None, *, now_utc: datetime | None = None) -> datetime:
    """Current local time for market (aware datetime when zoneinfo works)."""
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    tz_name = timezone_for_market(market_code)
    try:
        from zoneinfo import ZoneInfo

        return now.astimezone(ZoneInfo(tz_name))
    except Exception:
        return _offset_local(market_code, now)


def business_hours_enforced() -> bool:
    """Always False — 24/7 outreach strategy (2026-07-30)."""
    return False


def is_business_hours(
    market_code: str | None,
    *,
    now_utc: datetime | None = None,
    local_dt: datetime | None = None,
) -> bool:
    """Always True — no local-hour send gate."""
    return True


def business_time_status(
    market_code: str | None,
    *,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Status row for Ready/Waiting / UI (always open under 24/7 strategy)."""
    local = local_now(market_code, now_utc=now_utc)
    return {
        "market": (market_code or "DE").strip().upper() or "DE",
        "timezone": timezone_for_market(market_code),
        "local_time": local.isoformat(),
        "local_hour": local.hour,
        "weekday": local.weekday(),
        "open": True,
        "window": "24/7",
        "business_hours_enforced": False,
        "queue": "ready",
    }


def market_from_lead(row: dict[str, Any] | None) -> str:
    if not isinstance(row, dict):
        return "DE"
    try:
        from app.integration.outreach_language_service import resolve_market_from_row

        m = resolve_market_from_row(row)
        if m:
            return str(m).upper()
    except Exception:
        pass
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    return str(meta.get("market") or row.get("market") or "DE").strip().upper() or "DE"
