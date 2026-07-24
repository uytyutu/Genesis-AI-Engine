"""Quality Gate before outreach send (Lead Engine v1)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from app.integration.business_time import is_business_hours, market_from_lead

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Recontact cooldown (days) — Fresh Campaign rule
RECONTACT_COOLDOWN_DAYS = 90


def _extract_email(contact: str) -> str:
    text = str(contact or "")
    m = re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
    return (m.group(0) if m else text).strip()


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def recently_contacted(
    row: dict[str, Any],
    *,
    all_rows: list[dict[str, Any]] | None = None,
    cooldown_days: int = RECONTACT_COOLDOWN_DAYS,
    now_utc: datetime | None = None,
) -> bool:
    """True if this company/email/host was contacted within cooldown."""
    now = now_utc or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max(1, int(cooldown_days)))
    email = _extract_email(str(row.get("contact") or "")).lower()
    host = str(row.get("website_url") or "").strip().lower()
    oid = str(row.get("id") or "")

    def _touched(other: dict[str, Any]) -> bool:
        o_out = str(other.get("outreach_status") or "")
        o_status = str(other.get("status") or "")
        if o_out not in ("sent", "approved") and o_status not in ("contacted", "won", "replied"):
            return False
        ts = (
            _parse_dt(str(other.get("sent_at") or ""))
            or _parse_dt(str(other.get("updated_at") or ""))
            or _parse_dt(str(other.get("found_at") or ""))
        )
        if ts is None or ts < cutoff:
            return False
        o_email = _extract_email(str(other.get("contact") or "")).lower()
        o_host = str(other.get("website_url") or "").strip().lower()
        if email and o_email == email:
            return True
        if host and o_host and (host in o_host or o_host in host):
            return True
        return False

    # Self already sent recently
    if str(row.get("outreach_status") or "") == "sent":
        ts = _parse_dt(str(row.get("sent_at") or row.get("updated_at") or ""))
        if ts and ts >= cutoff:
            return True

    for other in all_rows or []:
        if str(other.get("id") or "") == oid:
            continue
        if _touched(other):
            return True
    return False


def quality_gate_before_send(
    row: dict[str, Any],
    *,
    all_rows: list[dict[str, Any]] | None = None,
    exclusion_blocked: bool = False,
    now_utc: datetime | None = None,
    require_site_alive: bool = True,
) -> dict[str, Any]:
    """Return {ok, reason, detail}. Fail → Skip → next lead."""
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    if meta.get("quality_archive"):
        return {"ok": False, "reason": "archived", "detail": "Lead is in quality archive"}
    if meta.get("skip_outreach") or meta.get("skip_reason") == "healthy_site":
        return {
            "ok": False,
            "reason": "healthy_site",
            "detail": str(meta.get("smart_offer_rationale") or "Skip healthy site"),
        }

    email = _extract_email(str(row.get("contact") or ""))
    if not email or not _EMAIL_RE.match(email):
        return {"ok": False, "reason": "invalid_email", "detail": "Email missing or invalid"}

    if meta.get("do_not_contact") or meta.get("email_status") in (
        "unsubscribed",
        "bounced",
        "blocked",
    ):
        return {
            "ok": False,
            "reason": "do_not_contact",
            "detail": "Contact opted out / blocked for marketing email",
        }

    try:
        import os
        from pathlib import Path

        from app.integration.email_contact_status import EmailContactStatusService

        mem_raw = os.getenv("GENESIS_MEMORY_DIR", "").strip()
        mem = Path(mem_raw).expanduser() if mem_raw else None
        if EmailContactStatusService(mem).is_marketing_blocked(email):
            return {
                "ok": False,
                "reason": "unsubscribed",
                "detail": "Email status is Unsubscribed / Bounced / Blocked",
            }
    except Exception:
        pass

    if exclusion_blocked:
        return {"ok": False, "reason": "exclusion", "detail": "Company on stop-list"}

    if recently_contacted(row, all_rows=all_rows, now_utc=now_utc):
        return {
            "ok": False,
            "reason": "recent_contact",
            "detail": f"Contacted within {RECONTACT_COOLDOWN_DAYS} days",
        }

    # Analysis / offer
    url = str(row.get("website_url") or "").strip()
    analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}
    offer_kind = str(meta.get("offer_kind") or "")
    pkg = str(row.get("recommended_package_id") or meta.get("recommended_package_id") or "")
    if not pkg and offer_kind != "skip":
        # Allow pending prepare — still require message
        if not row.get("proposed_message"):
            return {"ok": False, "reason": "no_offer", "detail": "No package / draft yet"}
    if not row.get("proposed_message"):
        return {"ok": False, "reason": "analysis_incomplete", "detail": "No outreach draft"}

    if require_site_alive and url and analysis:
        if analysis.get("fetch_ok") is False:
            # Repair offers may still send; broken fetch is OK for repair pitch
            if not str(pkg).startswith("repair"):
                return {
                    "ok": False,
                    "reason": "site_down",
                    "detail": "Website does not respond",
                }

    market = market_from_lead(row)
    if not is_business_hours(market, now_utc=now_utc):
        return {
            "ok": False,
            "reason": "outside_business_hours",
            "detail": f"Market {market} outside 09:00–18:00 local (Waiting)",
            "queue": "waiting",
        }

    return {"ok": True, "reason": "pass", "detail": "Quality Gate OK", "queue": "ready"}
