"""Ready / Waiting queue helpers (Lead Engine v1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.integration.business_time import business_time_status, is_business_hours, market_from_lead
from app.integration.lead_engine_quality_gate import quality_gate_before_send


def _email_ok(row: dict[str, Any]) -> bool:
    import re

    text = str(row.get("contact") or "")
    return bool(re.search(r"[\w.+-]+@[\w.-]+\.\w+", text))


def classify_lead_queue(
    row: dict[str, Any],
    *,
    all_rows: list[dict[str, Any]] | None = None,
    now_utc: datetime | None = None,
) -> str:
    """Return ready | waiting | history | archived | skip."""
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    if meta.get("quality_archive"):
        return "archived"
    status = str(row.get("status") or "")
    outreach = str(row.get("outreach_status") or "")
    if status in ("won", "lost") or outreach == "sent":
        return "history"
    if meta.get("skip_outreach") or meta.get("skip_reason") == "healthy_site":
        return "skip"

    market = market_from_lead(row)
    in_hours = is_business_hours(market, now_utc=now_utc)
    has_draft = bool(_email_ok(row) and row.get("proposed_message"))
    if not in_hours:
        return "waiting"

    if outreach not in ("approved", "pending_approval"):
        return "waiting"

    gate = quality_gate_before_send(
        row, all_rows=all_rows, now_utc=now_utc, require_site_alive=False
    )
    if gate.get("ok") and has_draft:
        return "ready"
    return "waiting"


def build_lead_engine_dashboard(
    rows: list[dict[str, Any]],
    *,
    now_utc: datetime | None = None,
    enabled_markets: list[str] | None = None,
    top_n: int = 12,
) -> dict[str, Any]:
    """Counters + top premium Ready for studio_status / launcher."""
    now = now_utc or datetime.now(timezone.utc)
    ready: list[dict[str, Any]] = []
    waiting: list[dict[str, Any]] = []
    history_n = 0
    for row in rows:
        q = classify_lead_queue(row, all_rows=rows, now_utc=now)
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        item = {
            "id": row.get("id"),
            "company_name": row.get("company_name"),
            "market": market_from_lead(row),
            "premium_score": int(meta.get("premium_score") or 0),
            "recommended_package_id": row.get("recommended_package_id")
            or meta.get("recommended_package_id"),
            "outreach_status": row.get("outreach_status"),
            "found_at": row.get("found_at"),
            "queue": q,
        }
        if q == "ready":
            ready.append(item)
        elif q == "waiting":
            waiting.append(item)
        elif q == "history":
            history_n += 1

    # premium_score DESC, found_at DESC
    ready.sort(
        key=lambda x: (
            int(x.get("premium_score") or 0),
            str(x.get("found_at") or ""),
        ),
        reverse=True,
    )

    markets = list(enabled_markets or [])
    if not markets:
        try:
            from app.integration.country_profiles import COUNTRY_PROFILES

            markets = [code for code, p in COUNTRY_PROFILES.items() if p.get("enabled")]
        except Exception:
            markets = ["DE", "GB", "US"]

    countries = [business_time_status(code, now_utc=now) for code in markets]
    countries.sort(key=lambda c: (0 if c.get("open") else 1, str(c.get("market") or "")))

    return {
        "ready_now": len(ready),
        "waiting": len(waiting),
        "history": history_n,
        "top_premium_leads": ready[:top_n],
        "countries": countries,
        "version": "lead_engine_v1",
    }
