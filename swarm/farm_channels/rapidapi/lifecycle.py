"""Honest RapidAPI provider lifecycle — LIVE ≠ money."""

from __future__ import annotations

from typing import Any

from swarm.farm_channels.rapidapi.models import (
    STATUS_ACTIVE,
    STATUS_APPROVAL_REQUIRED,
    STATUS_ARCHIVED,
    STATUS_FAILED,
    STATUS_PAUSED,
    STATUS_PUBLISHED,
    STATUS_PUBLISHING,
    STATUS_QUALITY_GATE_FAILED,
    STATUS_READY,
)

# Provider-side commercial maturity (not Farm candidate status alone)
LC_DRAFT = "DRAFT"
LC_READY_TO_PUBLISH = "READY_TO_PUBLISH"
LC_PUBLISHED = "PUBLISHED"
LC_LIVE = "LIVE"
LC_HAS_EXTERNAL_TRAFFIC = "HAS_EXTERNAL_TRAFFIC"
LC_HAS_EXTERNAL_SUBSCRIBER = "HAS_EXTERNAL_SUBSCRIBER"
LC_HAS_PAID_SUBSCRIBER = "HAS_PAID_SUBSCRIBER"
LC_HAS_REAL_REVENUE = "HAS_REAL_REVENUE"

LIFECYCLE_ORDER = (
    LC_DRAFT,
    LC_READY_TO_PUBLISH,
    LC_PUBLISHED,
    LC_LIVE,
    LC_HAS_EXTERNAL_TRAFFIC,
    LC_HAS_EXTERNAL_SUBSCRIBER,
    LC_HAS_PAID_SUBSCRIBER,
    LC_HAS_REAL_REVENUE,
)


def _hub_published(row: dict[str, Any]) -> bool:
    api_id = str(row.get("rapidapi_api_id") or "").strip()
    if not api_id:
        return False
    pkg = row.get("publish_package") or {}
    host = str(pkg.get("rapidapi_host") or "").strip()
    hub_url = str(pkg.get("hub_url") or "").strip()
    return bool(api_id and (host or hub_url or pkg.get("hub_manual")))


def _metrics(row: dict[str, Any]) -> dict[str, Any]:
    m = row.get("metrics") or {}
    return {
        "requests": int(m.get("requests") or 0),
        "external_requests": int(m.get("external_requests") or m.get("requests") or 0),
        "subscribers": int(m.get("subscribers") or 0),
        "external_subscribers": int(
            m.get("external_subscribers") or m.get("subscribers") or 0
        ),
        "paid_subscribers": int(m.get("paid_subscribers") or 0),
        "real_revenue": float(m.get("real_revenue") or m.get("paid_out") or 0),
        "self_test_only": bool(m.get("self_test_only") or m.get("provider_self_test")),
    }


def derive_provider_lifecycle(
    row: dict[str, Any],
    *,
    paid_out_total: float = 0.0,
) -> str:
    """Highest proven commercial stage for one candidate. Never invents traffic/revenue."""
    st = str(row.get("status") or "")
    if st in (STATUS_FAILED, STATUS_QUALITY_GATE_FAILED, STATUS_ARCHIVED):
        return LC_DRAFT
    if st == STATUS_PAUSED:
        return LC_PUBLISHED if _hub_published(row) else LC_DRAFT

    met = _metrics(row)
    paid_out = float(paid_out_total or met["real_revenue"] or 0)
    if paid_out > 0:
        return LC_HAS_REAL_REVENUE
    if met["paid_subscribers"] > 0 and not met["self_test_only"]:
        return LC_HAS_PAID_SUBSCRIBER
    if met["external_subscribers"] > 0 and not met["self_test_only"]:
        return LC_HAS_EXTERNAL_SUBSCRIBER
    if met["external_requests"] > 0 and not met["self_test_only"]:
        return LC_HAS_EXTERNAL_TRAFFIC

    if _hub_published(row) and st in (STATUS_ACTIVE, STATUS_PUBLISHED):
        # LIVE = Hub listing + production routing evidence (api id / host / hub url)
        return LC_LIVE
    if _hub_published(row):
        return LC_PUBLISHED
    if st in (STATUS_APPROVAL_REQUIRED, STATUS_READY):
        return LC_READY_TO_PUBLISH
    if (row.get("quality_gate") or {}).get("ok"):
        return LC_READY_TO_PUBLISH
    return LC_DRAFT


def reconcile_candidate_status(row: dict[str, Any]) -> str | None:
    """
    Return corrected Farm status if ACTIVE/PUBLISHED was claimed without Hub id.
    Does not invent ACTIVE — only demotes dishonest LIVE claims.
    """
    st = str(row.get("status") or "")
    if st == STATUS_ACTIVE and not _hub_published(row):
        if (row.get("approval") or {}).get("approved"):
            return STATUS_APPROVAL_REQUIRED
        return STATUS_READY
    if st == STATUS_PUBLISHED and not _hub_published(row):
        return STATUS_APPROVAL_REQUIRED
    if st == STATUS_PUBLISHING and not _hub_published(row):
        return None
    return None


def theoretical_mrr_scenario(
    *,
    pro_price: float,
    paid_subscribers: int = 0,
    scenario_n: int = 12,
) -> dict[str, Any]:
    """List-price scenario is NEVER real MRR. At 0 paid → theoretical shown as 0 for hero."""
    pro = max(0.0, float(pro_price or 0))
    paid = max(0, int(paid_subscribers or 0))
    real = round(pro * paid, 2)
    return {
        "real_mrr": real,
        "theoretical_mrr": 0.0 if paid == 0 else real,
        "scenario_label": f"if_{scenario_n}_paid_pro_subscriptions",
        "scenario_mrr_at_n": round(pro * scenario_n, 2),
        "scenario_n": scenario_n,
        "pro_price": pro,
        "rule_ru": (
            "REAL MRR = paid subscribers × actual recurring. "
            "При 0 paid → REAL MRR = 0. scenario_mrr_at_n — модель, не pipeline."
        ),
    }


def portfolio_lifecycle_summary(
    rows: list[dict[str, Any]],
    *,
    paid_out_by_api: dict[str, float] | None = None,
) -> dict[str, Any]:
    paid_map = paid_out_by_api or {}
    by_lc: dict[str, int] = {k: 0 for k in LIFECYCLE_ORDER}
    live_ids: list[str] = []
    ready_ids: list[str] = []
    for row in rows:
        api_key = str(row.get("rapidapi_api_id") or row.get("id") or "")
        lc = derive_provider_lifecycle(row, paid_out_total=float(paid_map.get(api_key) or 0))
        by_lc[lc] = by_lc.get(lc, 0) + 1
        cid = str(row.get("id") or "")
        if lc in (
            LC_LIVE,
            LC_HAS_EXTERNAL_TRAFFIC,
            LC_HAS_EXTERNAL_SUBSCRIBER,
            LC_HAS_PAID_SUBSCRIBER,
            LC_HAS_REAL_REVENUE,
        ):
            live_ids.append(cid)
        if lc == LC_READY_TO_PUBLISH:
            ready_ids.append(cid)

    live = (
        by_lc[LC_LIVE]
        + by_lc[LC_HAS_EXTERNAL_TRAFFIC]
        + by_lc[LC_HAS_EXTERNAL_SUBSCRIBER]
        + by_lc[LC_HAS_PAID_SUBSCRIBER]
        + by_lc[LC_HAS_REAL_REVENUE]
    )
    published = live + by_lc[LC_PUBLISHED]
    return {
        "by_lifecycle": by_lc,
        "published_apis": published,
        "live_apis": live,
        "ready_to_publish": by_lc[LC_READY_TO_PUBLISH],
        "draft": by_lc[LC_DRAFT],
        "live_ids": live_ids,
        "ready_to_publish_ids": ready_ids,
        "rule_ru": (
            "LIVE только при реальном RapidAPI Hub listing (api id / host). "
            "READY_TO_PUBLISH ≠ LIVE. MONEY только после PAID_OUT."
        ),
    }
